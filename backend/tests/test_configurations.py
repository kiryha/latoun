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

    finish_codes = {scheme["code"] for scheme in body["finish_schemes"]}
    module_codes = {module["code"] for module in body["module_types"]}
    # Catalog exposes customer-visible active finishes only; init is excluded.
    assert {"brass", "steel"} <= finish_codes
    assert "init" not in finish_codes
    assert "black" not in finish_codes  # inactive
    assert {"switch", "dimmer"} <= module_codes
    assert body["gang_counts"] == [1]


def test_saved_configuration_can_be_loaded_again(client):
    save_response = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "brass"},
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["configuration_code"] == "LAT-CFG-000001"
    configuration_id = saved["configuration_id"]

    list_response = client.get("/api/configurations")
    assert list_response.status_code == 200
    codes = [config["configuration_code"] for config in list_response.json()]
    assert "LAT-CFG-000001" in codes

    read_response = client.get(f"/api/configurations/{configuration_id}")
    assert read_response.status_code == 200
    detail = read_response.json()
    assert detail["configuration"]["module_type_code"] == "dimmer"
    assert detail["configuration"]["finish_scheme_code"] == "brass"
    assert detail["render_state"]["is_valid"] is True
    assert len(detail["render_state"]["assets"]) == 3
    assert (
        detail["render_state"]["material_assignments"]["primary_metal"]
        == "brass_brushed"
    )


def test_configuration_codes_increment(client):
    first = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "switch", "finish_scheme": "steel"},
    ).json()
    second = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "brass"},
    ).json()
    assert first["configuration_code"] == "LAT-CFG-000001"
    assert second["configuration_code"] == "LAT-CFG-000002"

    listed = client.get("/api/configurations").json()
    assert listed[0]["configuration_code"] == "LAT-CFG-000002"


def test_saving_invalid_configuration_is_rejected(client):
    response = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "gold"},
    )
    assert response.status_code in (404, 422)


def test_read_missing_configuration_returns_404(client):
    response = client.get("/api/configurations/9999")
    assert response.status_code == 404


def test_delete_configuration(client):
    saved = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "brass"},
    ).json()
    configuration_id = saved["configuration_id"]

    deleted = client.delete(f"/api/configurations/{configuration_id}")
    assert deleted.status_code == 200
    assert deleted.json()["configuration_code"] == saved["configuration_code"]

    listed = client.get("/api/configurations").json()
    assert configuration_id not in {
        config["configuration_id"] for config in listed
    }


def test_delete_missing_configuration_returns_404(client):
    response = client.delete("/api/configurations/9999")
    assert response.status_code == 404
