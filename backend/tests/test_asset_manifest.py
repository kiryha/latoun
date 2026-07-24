"""Tests for wall-plate asset manifest migration, validation, and saving."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import settings
from app.services import asset_manifest_service as svc


# The padded slot names are intentional here: legacy manifests remain readable
# even though newly generated keys and file names now use unpadded slot numbers.
LEGACY_MANIFEST = {
    "schema_version": 2,
    "assets": {
        "plate.1gang": {
            "asset_type": "plate",
            "file": "/assets/glb/1gang_plate.glb",
            "coordinate_space": "assembly_origin",
        },
        "hardware.1gang.plate_screws": {
            "asset_type": "hardware",
            "file": "/assets/glb/1gang_plate_screws.glb",
            "coordinate_space": "assembly_origin",
        },
        "module.1gang.slot01.dimmer": {
            "asset_type": "slot_module",
            "module_type": "dimmer",
            "slot_position": 1,
            "file": "/assets/glb/1gang_slot01_dimmer.glb",
            "coordinate_space": "assembly_origin",
        },
        "module.1gang.slot01.switch": {
            "asset_type": "slot_module",
            "module_type": "switch",
            "slot_position": 1,
            "file": "/assets/glb/1gang_slot01_switch.glb",
            "coordinate_space": "assembly_origin",
        },
    },
}


def test_migrate_legacy_manifest():
    migrated = svc.migrate_manifest(LEGACY_MANIFEST)
    assert "schema_version" not in migrated
    plate = migrated["plate.1gang"]
    # Legacy ``asset_type`` is migrated to ``category`` on load.
    assert plate["category"] == "plate"
    assert "asset_type" not in plate
    assert plate["gang_count"] == 1
    # ``file`` is reduced to a bare name; the folder lives in properties.
    assert plate["file"] == "1gang_plate.glb"
    assert plate["is_active"] is True
    assert "coordinate_space" not in plate

    screws = migrated["hardware.1gang.plate_screws"]
    assert screws["hardware_type"] == "plate_screws"
    assert screws["gang_count"] == 1
    assert screws["file"] == "1gang_plate_screws.glb"

    dimmer = migrated["module.1gang.slot01.dimmer"]
    assert dimmer["module_type"] == "dimmer"
    assert dimmer["slot_position"] == 1
    assert dimmer["gang_count"] == 1


def test_serialize_uses_parts_key():
    migrated = svc.migrate_manifest(LEGACY_MANIFEST)
    text = svc.serialize_manifest(migrated)
    data = json.loads(text)
    assert "parts" in data
    assert "assets" not in data
    assert data["properties"]["glb_folder"] == "/assets/wall_plates/"
    assert data["parts"]["plate.1gang"]["file"] == "1gang_plate.glb"


def test_validate_valid_entries(client):
    parts = svc.migrate_manifest(LEGACY_MANIFEST)
    response = client.post(
        "/api/wall-plates/asset-manifest/validate",
        json={"manifest": {"parts": parts}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["errors"] == []


def test_validate_invalid_slot(client):
    parts = {
        "module.2gang.slot3.switch": {
            "category": "slot_module",
            "gang_count": 2,
            "module_type": "switch",
            "slot_position": 3,
            "file": "2gang_slot3_switch.glb",
            "is_active": True,
        }
    }
    response = client.post(
        "/api/wall-plates/asset-manifest/validate",
        json={"manifest": {"parts": parts}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert any("Slot 3" in err["message"] for err in body["errors"])


def test_validate_duplicate_active_resolver(client):
    parts = {
        "module.2gang.slot1.switch": {
            "category": "slot_module",
            "gang_count": 2,
            "module_type": "switch",
            "slot_position": 1,
            "file": "2gang_slot1_switch.glb",
            "is_active": True,
        },
        "module.2gang.slot1.switch.alt": {
            "category": "slot_module",
            "gang_count": 2,
            "module_type": "switch",
            "slot_position": 1,
            "file": "2gang_slot1_switch_alt.glb",
            "is_active": True,
        },
    }
    response = client.post(
        "/api/wall-plates/asset-manifest/validate",
        json={"manifest": {"parts": parts}},
    )
    body = response.json()
    assert body["ok"] is False
    assert any("Two active entries" in err["message"] for err in body["errors"])


def test_inactive_duplicate_is_warning_only(client):
    parts = {
        "module.2gang.slot1.switch": {
            "category": "slot_module",
            "gang_count": 2,
            "module_type": "switch",
            "slot_position": 1,
            "file": "2gang_slot1_switch.glb",
            "is_active": True,
        },
        "module.2gang.slot1.switch.alt": {
            "category": "slot_module",
            "gang_count": 2,
            "module_type": "switch",
            "slot_position": 1,
            "file": "2gang_slot1_switch_alt.glb",
            "is_active": False,
        },
    }
    response = client.post(
        "/api/wall-plates/asset-manifest/validate",
        json={"manifest": {"parts": parts}},
    )
    body = response.json()
    assert body["ok"] is True
    assert any("inactive" in w["message"].lower() for w in body["warnings"])


def test_get_manifest_reads_new_location(client):
    response = client.get("/api/wall-plates/asset-manifest")
    assert response.status_code == 200
    body = response.json()
    assert "revision" in body
    parts = body["manifest"]["parts"]
    assert "plate.1gang" in parts
    assert parts["plate.1gang"]["file"] == "1gang_plate.glb"
    assert body["manifest"]["properties"]["glb_folder"] == "/assets/wall_plates/"
    assert "coordinate_space" not in parts["plate.1gang"]
    assert "schema_version" not in body["manifest"]
    assert "assets" not in body["manifest"]


@pytest.fixture()
def isolated_manifest(tmp_path, monkeypatch):
    manifest_path = tmp_path / "asset_manifest.json"
    seeded = svc.migrate_manifest(LEGACY_MANIFEST)
    manifest_path.write_text(
        svc.serialize_manifest(seeded), encoding="utf-8"
    )
    monkeypatch.setattr(settings, "asset_manifest_path", manifest_path)
    svc.clear_manifest_cache()
    yield manifest_path
    svc.clear_manifest_cache()


def test_put_saves_atomically_and_formats(client, isolated_manifest: Path):
    get_response = client.get("/api/wall-plates/asset-manifest")
    revision = get_response.json()["revision"]
    parts = get_response.json()["manifest"]["parts"]
    parts["plate.2gang"] = {
        "category": "plate",
        "gang_count": 2,
        "file": "2gang_plate.glb",
        "is_active": True,
    }

    put_response = client.put(
        "/api/wall-plates/asset-manifest",
        json={
            "manifest": {"parts": parts},
            "expected_revision": revision,
        },
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["saved"] is True
    assert "plate.2gang" in body["manifest"]["parts"]

    on_disk = json.loads(isolated_manifest.read_text(encoding="utf-8"))
    assert "schema_version" not in on_disk
    assert "assets" not in on_disk
    assert on_disk["properties"]["glb_folder"] == "/assets/wall_plates/"
    assert on_disk["parts"]["plate.2gang"]["file"] == "2gang_plate.glb"
    # Deterministic formatting: trailing newline, 2-space indent.
    text = isolated_manifest.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert '"category": "plate"' in text


def test_put_revision_conflict(client, isolated_manifest: Path):
    get_response = client.get("/api/wall-plates/asset-manifest")
    parts = get_response.json()["manifest"]["parts"]
    response = client.put(
        "/api/wall-plates/asset-manifest",
        json={
            "manifest": {"parts": parts},
            "expected_revision": "sha256-stale",
        },
    )
    assert response.status_code == 409
    assert "changed on disk" in response.json()["message"]


def test_put_rejects_resolver_conflicts(client, isolated_manifest: Path):
    get_response = client.get("/api/wall-plates/asset-manifest")
    revision = get_response.json()["revision"]
    parts = {
        "plate.1gang": {
            "category": "plate",
            "gang_count": 1,
            "file": "1gang_plate.glb",
            "is_active": True,
        },
        "plate.1gang.alt": {
            "category": "plate",
            "gang_count": 1,
            "file": "1gang_plate_alt.glb",
            "is_active": True,
        },
    }
    response = client.put(
        "/api/wall-plates/asset-manifest",
        json={
            "manifest": {"parts": parts},
            "expected_revision": revision,
        },
    )
    assert response.status_code == 422


def test_inactive_entries_ignored_by_assembly(client, isolated_manifest: Path):
    get_response = client.get("/api/wall-plates/asset-manifest")
    revision = get_response.json()["revision"]
    parts = get_response.json()["manifest"]["parts"]
    parts["module.1gang.slot01.switch"]["is_active"] = False

    put_response = client.put(
        "/api/wall-plates/asset-manifest",
        json={
            "manifest": {"parts": parts},
            "expected_revision": revision,
        },
    )
    assert put_response.status_code == 200

    resolve = client.post(
        "/api/render/resolve",
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "switch"}],
            "finish_scheme": "brass",
        },
    )
    body = resolve.json()
    missing_keys = {item["asset_key"] for item in body["missing_assets"]}
    assert "module.1gang.slot01.switch" in missing_keys


def test_list_module_types_includes_sort_order(client):
    response = client.get("/api/module-types")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 4
    assert all("sort_order" in row for row in body)
    codes = [row["code"] for row in body]
    assert "switch" in codes
