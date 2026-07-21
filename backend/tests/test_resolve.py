"""Tests for configuration resolution and the render state."""

from __future__ import annotations

import pytest

RESOLVE_URL = "/api/configurations/resolve"


@pytest.mark.parametrize(
    ("module_type", "material"),
    [
        ("dimmer", "brass"),
        ("dimmer", "steel"),
        ("switch", "brass"),
        ("switch", "steel"),
    ],
)
def test_valid_configurations_resolve(client, module_type, material):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": module_type, "material": material},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["is_valid"] is True
    assert body["configuration"] == {
        "gang_count": 1,
        "module_type": module_type,
        "material": material,
    }
    assert body["material"]["code"] == material

    # Plate + screws + one selected module.
    asset_keys = [asset["asset_key"] for asset in body["assets"]]
    assert asset_keys == [
        "plate.1gang",
        "hardware.1gang.plate_screws",
        f"module.1gang.slot01.{module_type}",
    ]
    for asset in body["assets"]:
        assert asset["file"].startswith("/assets/glb/")
        assert asset["material_policy"] == "replace_all"
        assert asset["material_code"] == material

    # BOM has one line per asset, all in the selected material.
    assert len(body["bom"]) == 3
    for line in body["bom"]:
        assert line["quantity"] == 1
        assert line["material"] == material


def test_invalid_material_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "dimmer", "material": "gold"},
    )
    assert response.status_code == 422
    assert "material" in response.json()["message"].lower()


def test_invalid_module_type_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "outlet", "material": "brass"},
    )
    assert response.status_code == 422
    assert "module type" in response.json()["message"].lower()


def test_unsupported_gang_count_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 2, "module_type": "dimmer", "material": "brass"},
    )
    assert response.status_code == 422
    assert "gang_count" in response.json()["message"].lower()


def test_missing_asset_key_returns_clear_error(client, monkeypatch):
    """If the manifest lacks a required asset key, surface a clear error."""
    from app.services import asset_manifest_service

    manifest = asset_manifest_service.get_asset_manifest()
    # Remove the dimmer module asset to simulate a missing asset key.
    removed = manifest.assets.pop("module.1gang.slot01.dimmer")
    try:
        response = client.post(
            RESOLVE_URL,
            json={"gang_count": 1, "module_type": "dimmer", "material": "brass"},
        )
        assert response.status_code == 500
        assert "missing asset key" in response.json()["message"].lower()
    finally:
        manifest.assets["module.1gang.slot01.dimmer"] = removed
