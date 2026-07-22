"""Tests for configuration resolution and the render state."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import FinishScheme, Material, MaterialAssignment

RESOLVE_URL = "/api/configurations/resolve"


@pytest.mark.parametrize(
    ("module_type", "finish_scheme"),
    [
        ("dimmer", "brass"),
        ("dimmer", "steel"),
        ("switch", "brass"),
        ("switch", "steel"),
    ],
)
def test_valid_configurations_resolve(client, module_type, finish_scheme):
    response = client.post(
        RESOLVE_URL,
        json={
            "gang_count": 1,
            "module_type": module_type,
            "finish_scheme": finish_scheme,
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert body["is_valid"] is True
    assert body["configuration"] == {
        "gang_count": 1,
        "module_type": module_type,
        "finish_scheme": finish_scheme,
    }
    assert "init" in body["active_sources"]
    assert finish_scheme in body["active_sources"]

    expected_metal = (
        "brass_brushed" if finish_scheme == "brass" else "stainless_steel_brushed"
    )
    assert body["material_assignments"]["primary_metal"] == expected_metal
    assert body["material_assignments"]["hardware_metal"] == expected_metal
    assert body["material_assignments"]["actuator_metal"] == expected_metal
    assert body["material_assignments"]["electrical_core"] == "black_plastic_matte"
    assert expected_metal in body["materials"]
    assert "black_plastic_matte" in body["materials"]

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
    for line in body["bom"]:
        assert line["quantity"] == 1
        assert line["finish_scheme"] == finish_scheme


def test_invalid_finish_scheme_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "gold"},
    )
    assert response.status_code in (404, 422)
    message = response.json()["message"].lower()
    assert "finish" in message or "scheme" in message or "not found" in message


def test_inactive_finish_scheme_cannot_be_selected(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "black"},
    )
    assert response.status_code == 422
    assert "inactive" in response.json()["message"].lower()


def test_invalid_module_type_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "outlet", "finish_scheme": "brass"},
    )
    assert response.status_code == 422
    assert "module type" in response.json()["message"].lower()


def test_unsupported_gang_count_returns_validation_error(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 2, "module_type": "dimmer", "finish_scheme": "brass"},
    )
    assert response.status_code == 422
    assert "gang_count" in response.json()["message"].lower()


def test_selected_scheme_overrides_init_for_matching_binding(client, db_sessionmaker):
    # Give init a primary_metal assignment that would conflict with brass.
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
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "brass"},
    )
    assert response.status_code == 200
    assert response.json()["material_assignments"]["primary_metal"] == "brass_brushed"


def test_resolve_init_assignments_alone(client):
    response = client.post(
        RESOLVE_URL,
        json={"gang_count": 1, "module_type": "dimmer", "finish_scheme": "init"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["active_sources"] == ["init"]
    assert body["material_assignments"]["electrical_core"] == "black_plastic_matte"
    assert "primary_metal" not in body["material_assignments"]
