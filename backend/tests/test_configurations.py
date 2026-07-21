"""Tests for saving, listing, and reloading configurations, plus catalog."""

from __future__ import annotations


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_catalog_lists_seeded_data(client):
    response = client.get("/api/catalog")
    assert response.status_code == 200
    body = response.json()

    material_codes = {m["code"] for m in body["materials"]}
    module_codes = {m["code"] for m in body["module_types"]}
    assert {"brass", "steel"} <= material_codes
    assert {"switch", "dimmer"} <= module_codes
    assert body["gang_counts"] == [1]


def test_saved_configuration_can_be_loaded_again(client):
    save_response = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "material": "brass"},
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["configuration_code"] == "LAT-CFG-000001"
    configuration_id = saved["configuration_id"]

    # It appears in the list.
    list_response = client.get("/api/configurations")
    assert list_response.status_code == 200
    codes = [c["configuration_code"] for c in list_response.json()]
    assert "LAT-CFG-000001" in codes

    # It can be read back with a freshly resolved render state.
    read_response = client.get(f"/api/configurations/{configuration_id}")
    assert read_response.status_code == 200
    detail = read_response.json()
    assert detail["configuration"]["module_type_code"] == "dimmer"
    assert detail["configuration"]["material_code"] == "brass"
    assert detail["render_state"]["is_valid"] is True
    assert len(detail["render_state"]["assets"]) == 3


def test_configuration_codes_increment(client):
    first = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "switch", "material": "steel"},
    ).json()
    second = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "material": "brass"},
    ).json()
    assert first["configuration_code"] == "LAT-CFG-000001"
    assert second["configuration_code"] == "LAT-CFG-000002"

    # Reverse chronological order.
    listed = client.get("/api/configurations").json()
    assert listed[0]["configuration_code"] == "LAT-CFG-000002"


def test_saving_invalid_configuration_is_rejected(client):
    response = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "material": "gold"},
    )
    assert response.status_code == 422


def test_read_missing_configuration_returns_404(client):
    response = client.get("/api/configurations/9999")
    assert response.status_code == 404
