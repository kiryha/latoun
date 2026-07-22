"""Tests for the material management CRUD endpoints."""

from __future__ import annotations


def test_list_materials_includes_seeded(client):
    response = client.get("/api/materials")
    assert response.status_code == 200
    codes = {material["code"] for material in response.json()}
    assert {"brass_brushed", "stainless_steel_brushed", "black_plastic_matte"} <= codes


def test_create_material(client):
    payload = {
        "code": "copper_brushed",
        "display_name": "Brushed Copper",
        "base_color": "#B87333",
        "metalness": 1.0,
        "roughness": 0.35,
        "anisotropy": 0.1,
    }
    response = client.post("/api/materials", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == "copper_brushed"
    assert body["display_name"] == "Brushed Copper"
    assert body["is_active"] is True


def test_create_duplicate_code_conflicts(client):
    response = client.post(
        "/api/materials",
        json={"code": "brass_brushed", "display_name": "Brass 2"},
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
        "/api/materials/stainless_steel_brushed",
        json={"display_name": "Brushed Steel", "roughness": 0.4},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["display_name"] == "Brushed Steel"
    assert body["roughness"] == 0.4
    assert body["metalness"] == 1.0


def test_update_missing_material_404(client):
    response = client.patch("/api/materials/nope", json={"roughness": 0.1})
    assert response.status_code == 404


def test_delete_unreferenced_material(client):
    client.post(
        "/api/materials",
        json={"code": "temp", "display_name": "Temp"},
    )
    response = client.delete("/api/materials/temp")
    assert response.status_code == 200
    codes = {material["code"] for material in client.get("/api/materials").json()}
    assert "temp" not in codes


def test_rename_material_code(client):
    client.post(
        "/api/materials",
        json={"code": "copper_brushed", "display_name": "Copper"},
    )
    response = client.patch(
        "/api/materials/copper_brushed",
        json={"code": "bronze_brushed"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["code"] == "bronze_brushed"

    codes = {material["code"] for material in client.get("/api/materials").json()}
    assert "bronze_brushed" in codes
    assert "copper_brushed" not in codes


def test_rename_to_existing_code_conflicts(client):
    response = client.patch(
        "/api/materials/stainless_steel_brushed",
        json={"code": "brass_brushed"},
    )
    assert response.status_code == 409


def test_delete_referenced_material_conflicts(client):
    response = client.delete("/api/materials/brass_brushed")
    assert response.status_code == 409
    message = response.json()["message"].lower()
    assert "assignment" in message
    assert "primary_metal" in message or "brass" in message
