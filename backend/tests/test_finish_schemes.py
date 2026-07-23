"""Tests for finish schemes and semantic material assignments."""

from __future__ import annotations


def _scheme_id(client, code: str) -> int:
    schemes = client.get("/api/finish-schemes").json()
    match = next(scheme for scheme in schemes if scheme["code"] == code)
    return match["finish_scheme_id"]


def test_list_finish_schemes_includes_seeded(client):
    response = client.get("/api/finish-schemes")
    assert response.status_code == 200
    codes = {scheme["code"] for scheme in response.json()}
    assert {"init", "brass", "steel", "black"} <= codes


def test_customer_visible_list_excludes_init(client):
    response = client.get(
        "/api/finish-schemes",
        params={"is_active": True, "is_customer_visible": True},
    )
    assert response.status_code == 200
    codes = {scheme["code"] for scheme in response.json()}
    assert "init" not in codes
    assert {"brass", "steel"} <= codes
    assert "black" not in codes


def test_create_finish_scheme(client):
    response = client.post(
        "/api/finish-schemes",
        json={
            "code": "copper",
            "display_name": "Copper",
            "description": "Copper finish",
            "is_active": True,
            "is_customer_visible": True,
            "sort_order": 40,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == "copper"
    assert body["display_name"] == "Copper"


def test_create_duplicate_finish_scheme_code_conflicts(client):
    response = client.post(
        "/api/finish-schemes",
        json={"code": "brass", "display_name": "Brass 2"},
    )
    assert response.status_code == 409


def test_update_finish_scheme(client):
    scheme_id = _scheme_id(client, "steel")
    response = client.put(
        f"/api/finish-schemes/{scheme_id}",
        json={"display_name": "Stainless", "description": "Updated"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["display_name"] == "Stainless"
    assert body["code"] == "steel"


def test_delete_unused_finish_scheme(client):
    created = client.post(
        "/api/finish-schemes",
        json={"code": "temp_finish", "display_name": "Temp"},
    ).json()
    response = client.delete(f"/api/finish-schemes/{created['finish_scheme_id']}")
    assert response.status_code == 200
    codes = {scheme["code"] for scheme in client.get("/api/finish-schemes").json()}
    assert "temp_finish" not in codes


def test_block_deletion_of_init(client):
    scheme_id = _scheme_id(client, "init")
    response = client.delete(f"/api/finish-schemes/{scheme_id}")
    assert response.status_code == 409
    assert "init" in response.json()["message"].lower()


def test_block_deletion_when_assembly_states_reference_scheme(client):
    catalog = client.get("/api/catalog").json()
    switch_id = next(
        module["module_type_id"]
        for module in catalog["module_types"]
        if module["code"] == "switch"
    )
    scheme_id = _scheme_id(client, "brass")
    created = client.post(
        "/api/assignment-states",
        json={
            "display_name": "switch",
            "gang_count": 1,
            "default_finish_scheme_id": scheme_id,
            "modules": [{"slot_number": 1, "module_type_id": switch_id}],
        },
    )
    assert created.status_code == 201, created.text

    response = client.delete(f"/api/finish-schemes/{scheme_id}")
    assert response.status_code == 409
    assert "assembly state" in response.json()["message"].lower()


def test_create_assignment(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": "usb_insert", "material_code": "black_plastic_matte"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["binding_name"] == "usb_insert"
    assert body["material_code"] == "black_plastic_matte"


def test_create_assignment_normalizes_binding_name(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": " USB Insert ", "material_code": "black_plastic_matte"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["binding_name"] == "usb_insert"


def test_reject_invalid_binding_name(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": "123_bad", "material_code": "brass_brushed"},
    )
    assert response.status_code == 422


def test_block_duplicate_finish_scheme_binding(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": "primary_metal", "material_code": "brass_brushed"},
    )
    assert response.status_code == 409


def test_block_assignment_to_missing_material(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": "accent_metal", "material_code": "does_not_exist"},
    )
    assert response.status_code == 422


def test_update_and_delete_assignment(client):
    scheme_id = _scheme_id(client, "brass")
    created = client.post(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={"binding_name": "label_plate", "material_code": "white_print"},
    ).json()
    assignment_id = created["material_assignment_id"]

    updated = client.put(
        f"/api/material-assignments/{assignment_id}",
        json={"material_code": "black_plastic_matte"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["material_code"] == "black_plastic_matte"

    deleted = client.delete(f"/api/material-assignments/{assignment_id}")
    assert deleted.status_code == 200


def test_bulk_save_assignments_replaces_set(client):
    scheme_id = _scheme_id(client, "brass")
    response = client.put(
        f"/api/finish-schemes/{scheme_id}/assignments",
        json={
            "assignments": [
                {"binding_name": "primary_metal", "material_code": "brass_brushed"},
                {"binding_name": "hardware_metal", "material_code": "brass_brushed"},
            ]
        },
    )
    assert response.status_code == 200, response.text
    bindings = {row["binding_name"] for row in response.json()}
    assert bindings == {"primary_metal", "hardware_metal"}


def test_resolved_assignments_combines_init_and_scheme(client):
    response = client.get("/api/finish-schemes/brass/resolved-assignments")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["active_sources"] == ["init", "brass"]
    assert body["material_assignments"]["primary_metal"] == "brass_brushed"
    assert body["material_assignments"]["electrical_core"] == "black_plastic_matte"
