"""Tests for render-state resolution."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import FinishScheme, Material, MaterialAssignment

RESOLVE_URL = "/api/render/resolve"


@pytest.mark.parametrize(
    ("module_type", "finish_scheme"),
    [
        ("dimmer", "brass"),
        ("dimmer", "steel"),
        ("switch", "brass"),
        ("switch", "steel"),
        ("outlet", "brass"),
        ("usb_c_outlet", "steel"),
    ],
)
def test_valid_assemblies_resolve(client, module_type, finish_scheme):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": module_type}],
            "finish_scheme": finish_scheme,
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert body["is_valid"] is True
    assert body["assembly"]["gang_count"] == 1
    assert body["assembly"]["finish_scheme"] == finish_scheme
    assert body["assembly"]["modules"] == [
        {"slot_number": 1, "module_type": module_type}
    ]
    assert "init" in body["active_sources"]
    assert finish_scheme in body["active_sources"]

    expected_metal = (
        "brass_brushed" if finish_scheme == "brass" else "stainless_steel_brushed"
    )
    assert body["material_assignments"]["primary_metal"] == expected_metal
    assert body["material_assignments"]["electrical_core"] == "black_plastic_matte"

    asset_keys = [asset["asset_key"] for asset in body["assets"]]
    module_key = f"module.1gang.slot01.{module_type}"
    assert "plate.1gang" in asset_keys
    assert "hardware.1gang.plate_screws" in asset_keys

    if module_type in {"switch", "dimmer"}:
        assert body["assets_complete"] is True
        assert body["missing_assets"] == []
        assert module_key in asset_keys
        assert len(body["bom"]) == 3
    else:
        assert body["assets_complete"] is False
        assert any(item["asset_key"] == module_key for item in body["missing_assets"])
        assert module_key not in asset_keys


def test_invalid_finish_scheme_returns_error(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "dimmer"}],
            "finish_scheme": "gold",
        },
    )
    assert response.status_code in (404, 422)


def test_inactive_finish_scheme_cannot_be_selected(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "dimmer"}],
            "finish_scheme": "black",
        },
    )
    assert response.status_code == 422
    assert "inactive" in response.json()["message"].lower()


def test_invalid_module_type_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "blank"}],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 422
    assert "module type" in response.json()["message"].lower()


@pytest.mark.parametrize("gang_count", [1, 2, 3, 4])
def test_plate_and_screws_resolve_for_every_gang_count(client, gang_count):
    modules = [
        {"slot_number": slot, "module_type": "switch"}
        for slot in range(1, gang_count + 1)
    ]
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": gang_count,
            "modules": modules,
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    asset_keys = {asset["asset_key"] for asset in body["assets"]}
    missing_keys = {item["asset_key"] for item in body["missing_assets"]}

    plate_key = f"plate.{gang_count}gang"
    screws_key = f"hardware.{gang_count}gang.plate_screws"
    if gang_count == 1:
        assert plate_key in asset_keys
        assert screws_key in asset_keys
    else:
        assert plate_key in missing_keys
        assert screws_key in missing_keys
        assert plate_key not in asset_keys
        assert screws_key not in asset_keys


def test_multi_gang_mixed_modules_resolve_with_warnings(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 2,
            "modules": [
                {"slot_number": 1, "module_type": "outlet"},
                {"slot_number": 2, "module_type": "dimmer"},
            ],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["assets_complete"] is False
    assert body["assembly"]["modules"] == [
        {"slot_number": 1, "module_type": "outlet"},
        {"slot_number": 2, "module_type": "dimmer"},
    ]
    missing_keys = {item["asset_key"] for item in body["missing_assets"]}
    assert "plate.2gang" in missing_keys
    assert "module.2gang.slot01.outlet" in missing_keys
    assert "module.2gang.slot02.dimmer" in missing_keys
    # Missing assets must not silently substitute another device.
    assert all(
        "switch" not in item["asset_key"] for item in body["missing_assets"]
    )


def test_slot_module_asset_keys_use_left_to_right_numbering(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 4,
            "modules": [
                {"slot_number": 1, "module_type": "usb_c_outlet"},
                {"slot_number": 2, "module_type": "switch"},
                {"slot_number": 3, "module_type": "outlet"},
                {"slot_number": 4, "module_type": "dimmer"},
            ],
            "finish_scheme": "steel",
        },
    )
    assert response.status_code == 200
    body = response.json()
    missing_by_slot = {
        item["slot_number"]: item["module_type"]
        for item in body["missing_assets"]
        if item["role"] == "module"
    }
    assert missing_by_slot == {
        1: "usb_c_outlet",
        2: "switch",
        3: "outlet",
        4: "dimmer",
    }


def test_gang_count_out_of_range_rejected(client):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 5,
            "modules": [
                {"slot_number": i, "module_type": "switch"} for i in range(1, 6)
            ],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 422


def test_selected_scheme_overrides_init_for_matching_binding(client, db_sessionmaker):
    with db_sessionmaker() as session:
        init_scheme = session.scalar(
            select(FinishScheme).where(FinishScheme.code == "init")
        )
        plastic = session.scalar(
            select(Material).where(Material.code == "black_plastic_matte")
        )
        assert init_scheme is not None and plastic is not None
        session.add(
            MaterialAssignment(
                finish_scheme_id=init_scheme.finish_scheme_id,
                binding_name="primary_metal",
                material_id=plastic.material_id,
            )
        )
        session.commit()

    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "dimmer"}],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 200
    assert response.json()["material_assignments"]["primary_metal"] == "brass_brushed"


def test_finish_change_updates_all_metal_bindings(client):
    brass = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "switch"}],
            "finish_scheme": "brass",
        },
    ).json()
    steel = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "modules": [{"slot_number": 1, "module_type": "switch"}],
            "finish_scheme": "steel",
        },
    ).json()

    for binding in ("primary_metal", "hardware_metal", "actuator_metal"):
        assert brass["material_assignments"][binding] == "brass_brushed"
        assert steel["material_assignments"][binding] == "stainless_steel_brushed"
    # Static bindings continue to resolve from init.
    assert brass["material_assignments"]["electrical_core"] == "black_plastic_matte"
    assert steel["material_assignments"]["electrical_core"] == "black_plastic_matte"
    # Geometry asset keys are identical across finishes.
    assert [a["asset_key"] for a in brass["assets"]] == [
        a["asset_key"] for a in steel["assets"]
    ]


def test_resolve_assignment_state_render(client):
    catalog = client.get("/api/catalog").json()
    dimmer_id = next(
        module["module_type_id"]
        for module in catalog["module_types"]
        if module["code"] == "dimmer"
    )
    brass_id = next(
        scheme["finish_scheme_id"]
        for scheme in client.get("/api/finish-schemes").json()
        if scheme["code"] == "brass"
    )
    created = client.post(
        "/api/assignment-states",
        json={
            "display_name": "dimmer-brass",
            "gang_count": 1,
            "default_finish_scheme_id": brass_id,
            "modules": [{"slot_number": 1, "module_type_id": dimmer_id}],
        },
    )
    assert created.status_code == 201, created.text
    state = created.json()

    response = client.get(
        f"/api/assignment-states/{state['assignment_state_id']}/render-state",
        params={"finish_scheme": "steel"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assembly"]["assignment_state_code"] == state["assignment_state_code"]
    assert body["assembly"]["finish_scheme"] == "steel"
    assert body["assembly"]["modules"] == [
        {"slot_number": 1, "module_type": "dimmer"}
    ]
    assert (
        body["material_assignments"]["primary_metal"] == "stainless_steel_brushed"
    )
