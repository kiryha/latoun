"""Tests for assembly-state (assignment_states) CRUD and catalog integration."""

from __future__ import annotations

import pytest


def _module_id(client, code: str) -> int:
    catalog = client.get("/api/catalog").json()
    return next(
        module["module_type_id"]
        for module in catalog["module_types"]
        if module["code"] == code
    )


def _finish_id(client, code: str) -> int:
    schemes = client.get("/api/finish-schemes").json()
    return next(
        scheme["finish_scheme_id"] for scheme in schemes if scheme["code"] == code
    )


def test_catalog_lists_seeded_data(client):
    response = client.get("/api/catalog")
    assert response.status_code == 200
    body = response.json()

    finish_codes = {scheme["code"] for scheme in body["finish_schemes"]}
    module_codes = {module["code"] for module in body["module_types"]}
    assert {"brass", "steel"} <= finish_codes
    assert "init" not in finish_codes
    assert {"switch", "dimmer", "outlet", "usb_c_outlet"} <= module_codes
    assert "rotary_dimmer" not in module_codes
    assert body["gang_counts"] == [1, 2, 3, 4]
    assert all("module_type_id" in module for module in body["module_types"])


def test_list_starts_empty(client):
    response = client.get("/api/assignment-states")
    assert response.status_code == 200
    assert response.json() == []


def test_create_update_delete_assignment_state(client):
    switch_id = _module_id(client, "switch")
    brass_id = _finish_id(client, "brass")

    created = client.post(
        "/api/assignment-states",
        json={
            "display_name": "switch",
            "gang_count": 1,
            "default_finish_scheme_id": brass_id,
            "notes": "test",
            "is_active": True,
            "sort_order": 99,
            "modules": [{"slot_number": 1, "module_type_id": switch_id}],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["assignment_state_code"].startswith("LAT-ASG-")
    assert body["display_name"] == "switch"
    assert body["modules"][0]["module_type_code"] == "switch"
    state_id = body["assignment_state_id"]

    dimmer_id = _module_id(client, "dimmer")
    updated = client.put(
        f"/api/assignment-states/{state_id}",
        json={
            "display_name": "dimmer-brass",
            "modules": [{"slot_number": 1, "module_type_id": dimmer_id}],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["display_name"] == "dimmer-brass"
    assert updated.json()["modules"][0]["module_type_code"] == "dimmer"

    deleted = client.delete(f"/api/assignment-states/{state_id}")
    assert deleted.status_code == 200
    listed = client.get("/api/assignment-states").json()
    assert state_id not in {state["assignment_state_id"] for state in listed}


def test_reject_missing_slots(client):
    switch_id = _module_id(client, "switch")
    response = client.post(
        "/api/assignment-states",
        json={
            "display_name": "bad",
            "gang_count": 2,
            "modules": [{"slot_number": 1, "module_type_id": switch_id}],
        },
    )
    assert response.status_code == 422


def test_reject_duplicate_slots(client):
    switch_id = _module_id(client, "switch")
    response = client.post(
        "/api/assignment-states",
        json={
            "display_name": "bad",
            "gang_count": 2,
            "modules": [
                {"slot_number": 1, "module_type_id": switch_id},
                {"slot_number": 1, "module_type_id": switch_id},
            ],
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("gang_count", "module_codes"),
    [
        (1, ["dimmer"]),
        (2, ["switch", "outlet"]),
        (4, ["usb_c_outlet", "switch", "outlet", "dimmer"]),
    ],
)
def test_save_multi_slot_assignment_state(client, gang_count, module_codes):
    brass_id = _finish_id(client, "brass")
    modules = [
        {
            "slot_number": index + 1,
            "module_type_id": _module_id(client, code),
        }
        for index, code in enumerate(module_codes)
    ]
    created = client.post(
        "/api/assignment-states",
        json={
            "display_name": "-".join(module_codes) + "-brass",
            "gang_count": gang_count,
            "default_finish_scheme_id": brass_id,
            "modules": modules,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["gang_count"] == gang_count
    assert body["default_finish_scheme_code"] == "brass"
    assert [row["slot_number"] for row in body["modules"]] == list(
        range(1, gang_count + 1)
    )
    assert [row["module_type_code"] for row in body["modules"]] == module_codes


def test_block_finish_scheme_delete_when_assembly_state_references(client):
    switch_id = _module_id(client, "switch")
    brass_id = _finish_id(client, "brass")
    created = client.post(
        "/api/assignment-states",
        json={
            "display_name": "switch",
            "gang_count": 1,
            "default_finish_scheme_id": brass_id,
            "modules": [{"slot_number": 1, "module_type_id": switch_id}],
        },
    )
    assert created.status_code == 201, created.text

    response = client.delete(f"/api/finish-schemes/{brass_id}")
    assert response.status_code == 409
    assert "assembly state" in response.json()["message"].lower()
