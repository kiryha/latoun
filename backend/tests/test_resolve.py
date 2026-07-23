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
    assert asset_keys == [
        "plate.1gang",
        "hardware.1gang.plate_screws",
        f"module.1gang.slot01.{module_type}",
    ]
    for asset in body["assets"]:
        assert asset["file"].startswith("/assets/glb/")
        assert "material_policy" not in asset

    assert len(body["bom"]) == 3


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
            "modules": [{"slot_number": 1, "module_type": "outlet"}],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 422
    assert "module type" in response.json()["message"].lower()


def test_unsupported_gang_count_without_assets_fails_or_validates(client):
    # Gang count 2 is allowed by the model but assets are missing today.
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 2,
            "modules": [
                {"slot_number": 1, "module_type": "switch"},
                {"slot_number": 2, "module_type": "dimmer"},
            ],
            "finish_scheme": "brass",
        },
    )
    assert response.status_code == 500
    assert "asset" in response.json()["message"].lower()


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
            "display_name": "dimmer",
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
