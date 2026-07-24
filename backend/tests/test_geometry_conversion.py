"""Tests for the Blender-backed Geometry part converter."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.config import settings
from app.services import geometry_conversion_service as svc


def test_convert_parts_endpoint_returns_file_results(client, monkeypatch):
    monkeypatch.setattr(
        svc,
        "convert_all_parts",
        lambda *, skip_existing: {
            "total": 2,
            "converted": 1,
            "skipped": 0,
            "failed": 1,
            "files": [
                {
                    "source": "plate.obj",
                    "output": "plate.glb",
                    "success": True,
                    "skipped": False,
                    "error": None,
                },
                {
                    "source": "switch.obj",
                    "output": "switch.glb",
                    "success": False,
                    "skipped": False,
                    "error": "Import failed",
                },
            ],
        },
    )

    response = client.post(
        "/api/wall-plates/convert-parts",
        json={"skip_existing": False},
    )

    assert response.status_code == 200
    assert response.json()["converted"] == 1
    assert response.json()["files"][1]["error"] == "Import failed"


def test_convert_all_parts_runs_blender_headlessly(tmp_path, monkeypatch):
    blender = tmp_path / "blender.exe"
    blender.touch()
    source = tmp_path / "obj"
    source.mkdir()
    (source / "plate.obj").write_text("o plate\n", encoding="utf-8")
    output = tmp_path / "glb"
    payload = {
        "total": 1,
        "converted": 1,
        "skipped": 0,
        "failed": 0,
        "files": [
            {
                "source": "plate.obj",
                "output": "plate.glb",
                "success": True,
                "skipped": False,
                "error": None,
            }
        ],
    }
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"Blender log\n{svc.RESULT_PREFIX}{json.dumps(payload)}\n",
            stderr="",
        )

    monkeypatch.setattr(settings, "blender_executable", blender)
    monkeypatch.setattr(settings, "parts_obj_directory", source)
    monkeypatch.setattr(settings, "parts_glb_directory", output)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = svc.convert_all_parts(skip_existing=False)

    assert result == payload
    command = captured["command"]
    assert "--background" in command
    assert "--factory-startup" in command
    assert str(source) in command
    assert str(output) in command
    assert command[-1] == "0"
    assert captured["kwargs"]["timeout"] == settings.blender_timeout_seconds


def test_convert_all_parts_skips_blender_when_source_is_empty(
    tmp_path, monkeypatch
):
    blender = tmp_path / "blender.exe"
    blender.touch()
    source = tmp_path / "obj"
    source.mkdir()

    monkeypatch.setattr(settings, "blender_executable", blender)
    monkeypatch.setattr(settings, "parts_obj_directory", source)
    monkeypatch.setattr(settings, "parts_glb_directory", tmp_path / "glb")

    result = svc.convert_all_parts()

    assert result == {
        "total": 0,
        "converted": 0,
        "skipped": 0,
        "failed": 0,
        "files": [],
    }


def test_skip_existing_avoids_launching_blender(tmp_path, monkeypatch):
    blender = tmp_path / "blender.exe"
    blender.touch()
    source = tmp_path / "obj"
    source.mkdir()
    (source / "plate.obj").write_text("o plate\n", encoding="utf-8")
    output = tmp_path / "glb"
    output.mkdir()
    (output / "plate.glb").write_bytes(b"existing")

    monkeypatch.setattr(settings, "blender_executable", blender)
    monkeypatch.setattr(settings, "parts_obj_directory", source)
    monkeypatch.setattr(settings, "parts_glb_directory", output)

    result = svc.convert_all_parts(skip_existing=True)

    assert result["converted"] == 0
    assert result["skipped"] == 1
    assert result["files"][0]["skipped"] is True


def test_parts_inventory_reports_matching_glbs(tmp_path, monkeypatch):
    source = tmp_path / "obj"
    source.mkdir()
    (source / "plate.obj").write_bytes(b"obj")
    (source / "switch.obj").write_bytes(b"switch")
    output = tmp_path / "glb"
    output.mkdir()
    (output / "plate.glb").write_bytes(b"glb")

    monkeypatch.setattr(settings, "parts_obj_directory", source)
    monkeypatch.setattr(settings, "parts_glb_directory", output)

    inventory = svc.list_parts()

    assert [part["source"] for part in inventory["parts"]] == [
        "plate.obj",
        "switch.obj",
    ]
    assert inventory["parts"][0]["glb_exists"] is True
    assert inventory["parts"][1]["glb_exists"] is False
