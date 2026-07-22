"""Tests for the material management CRUD endpoints."""

from __future__ import annotations


def test_list_materials_includes_seeded(client):
    response = client.get("/api/materials")
    assert response.status_code == 200
    codes = {m["code"] for m in response.json()}
    assert {"brass", "steel"}.issubset(codes)


def test_create_material(client):
    payload = {
        "code": "copper",
        "display_name": "Copper",
        "base_color": "#B87333",
        "metalness": 1.0,
        "roughness": 0.35,
        "anisotropy": 0.1,
    }
    response = client.post("/api/materials", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == "copper"
    assert body["display_name"] == "Copper"
    assert body["is_active"] is True


def test_create_duplicate_code_conflicts(client):
    response = client.post(
        "/api/materials", json={"code": "brass", "display_name": "Brass 2"}
    )
    assert response.status_code == 409


def test_create_invalid_color_rejected(client):
    response = client.post(
        "/api/materials",
        json={"code": "bad", "display_name": "Bad", "base_color": "red"},
    )
    assert response.status_code == 422


def test_update_material_partial(client):
    response = client.patch(
        "/api/materials/steel",
        json={"display_name": "Brushed Steel", "roughness": 0.4},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["display_name"] == "Brushed Steel"
    assert body["roughness"] == 0.4
    # Untouched field preserved.
    assert body["metalness"] == 1.0


def test_update_missing_material_404(client):
    response = client.patch("/api/materials/nope", json={"roughness": 0.1})
    assert response.status_code == 404


def test_delete_unreferenced_material(client):
    client.post("/api/materials", json={"code": "temp", "display_name": "Temp"})
    response = client.delete("/api/materials/temp")
    assert response.status_code == 200
    assert client.get("/api/materials").json()
    assert "temp" not in {m["code"] for m in client.get("/api/materials").json()}


def test_rename_material_code(client):
    client.post("/api/materials", json={"code": "copper", "display_name": "Copper"})
    response = client.patch("/api/materials/copper", json={"code": "bronze"})
    assert response.status_code == 200, response.text
    assert response.json()["code"] == "bronze"

    codes = {m["code"] for m in client.get("/api/materials").json()}
    assert "bronze" in codes
    assert "copper" not in codes


def test_rename_to_existing_code_conflicts(client):
    response = client.patch("/api/materials/steel", json={"code": "brass"})
    assert response.status_code == 409


def test_rename_cascades_to_configurations(client):
    saved = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "switch", "material": "brass"},
    )
    assert saved.status_code == 200, saved.text
    config_id = saved.json()["configuration_id"]

    renamed = client.patch("/api/materials/brass", json={"code": "brass_polished"})
    assert renamed.status_code == 200, renamed.text

    # The saved configuration now references the new code and still resolves.
    detail = client.get(f"/api/configurations/{config_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["configuration"]["material_code"] == "brass_polished"
    assert body["render_state"]["material"]["code"] == "brass_polished"


def test_delete_referenced_material_conflicts(client):
    # Save a configuration that references "brass", then deletion must fail.
    saved = client.post(
        "/api/configurations",
        json={"gang_count": 1, "module_type": "switch", "material": "brass"},
    )
    assert saved.status_code == 200, saved.text
    response = client.delete("/api/materials/brass")
    assert response.status_code == 409
