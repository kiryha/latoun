"""Initialize and seed the SQLite database.

Run as a module from the ``backend`` directory:

    python -m app.seed

The database is fully reproducible from this script; the active SQLite file is
not committed to Git. Seeding is idempotent (upsert by stable code / key).
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, init_database
from .models import (
    AssignmentState,
    AssignmentStateModule,
    FinishScheme,
    Material,
    MaterialAssignment,
    ModuleType,
)

# Render materials: implementation-level shader definitions referenced by
# assignments. Values mirror docs/material_assignment.md.
MATERIALS_SEED = [
    {
        "code": "brass_brushed",
        "display_name": "Brushed Brass",
        "base_color": "#B88A44",
        "metalness": 1.0,
        "roughness": 0.45,
        "anisotropy": 0.0,
        "anisotropy_rotation": 0.5,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
    {
        "code": "stainless_steel_brushed",
        "display_name": "Brushed Stainless Steel",
        "base_color": "#C8CBCE",
        "metalness": 1.0,
        "roughness": 0.35,
        "anisotropy": 0.0,
        "anisotropy_rotation": 0.45,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
    {
        "code": "black_steel_brushed",
        "display_name": "Brushed Black Steel",
        "base_color": "#2A2A2E",
        "metalness": 1.0,
        "roughness": 0.5,
        "anisotropy": 0.0,
        "anisotropy_rotation": 0.45,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
    {
        "code": "black_plastic_matte",
        "display_name": "Matte Black Plastic",
        "base_color": "#080808",
        "metalness": 0.0,
        "roughness": 0.72,
        "anisotropy": 0.0,
        "anisotropy_rotation": 0.0,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
    {
        "code": "white_print",
        "display_name": "White Print",
        "base_color": "#F2F2F2",
        "metalness": 0.0,
        "roughness": 0.55,
        "anisotropy": 0.0,
        "anisotropy_rotation": 0.0,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
]

MODULE_TYPES_SEED = [
    {"code": "switch", "display_name": "Switch", "is_active": True},
    {"code": "dimmer", "display_name": "Rotary Dimmer", "is_active": True},
]

FINISH_SCHEMES_SEED = [
    {
        "code": "init",
        "display_name": "Initialization",
        "description": "Static material assignments shared by all assemblies.",
        "is_active": True,
        "is_customer_visible": False,
        "sort_order": 0,
    },
    {
        "code": "brass",
        "display_name": "Brass",
        "description": "Brass product finish scheme.",
        "is_active": True,
        "is_customer_visible": True,
        "sort_order": 10,
    },
    {
        "code": "steel",
        "display_name": "Steel",
        "description": "Stainless-steel product finish scheme.",
        "is_active": True,
        "is_customer_visible": True,
        "sort_order": 20,
    },
    {
        "code": "black",
        "display_name": "Black",
        "description": "Blackened-metal product finish scheme.",
        "is_active": False,
        "is_customer_visible": True,
        "sort_order": 30,
    },
]

# (finish_scheme_code, binding_name, material_code)
ASSIGNMENTS_SEED = [
    ("init", "electrical_core", "black_plastic_matte"),
    ("init", "insulator", "black_plastic_matte"),
    ("init", "label", "white_print"),
    ("brass", "primary_metal", "brass_brushed"),
    ("brass", "hardware_metal", "brass_brushed"),
    ("brass", "actuator_metal", "brass_brushed"),
    ("steel", "primary_metal", "stainless_steel_brushed"),
    ("steel", "hardware_metal", "stainless_steel_brushed"),
    ("steel", "actuator_metal", "stainless_steel_brushed"),
    ("black", "primary_metal", "black_steel_brushed"),
    ("black", "hardware_metal", "black_steel_brushed"),
    ("black", "actuator_metal", "black_steel_brushed"),
]

def _upsert_materials(session: Session) -> None:
    for data in MATERIALS_SEED:
        existing = session.scalar(
            select(Material).where(Material.code == data["code"])
        )
        if existing is None:
            session.add(Material(**data))
        else:
            for key, value in data.items():
                setattr(existing, key, value)


def _upsert_module_types(session: Session) -> None:
    for data in MODULE_TYPES_SEED:
        existing = session.scalar(
            select(ModuleType).where(ModuleType.code == data["code"])
        )
        if existing is None:
            session.add(ModuleType(**data))
        else:
            for key, value in data.items():
                setattr(existing, key, value)


def _upsert_finish_schemes(session: Session) -> None:
    for data in FINISH_SCHEMES_SEED:
        existing = session.scalar(
            select(FinishScheme).where(FinishScheme.code == data["code"])
        )
        if existing is None:
            session.add(FinishScheme(**data))
        else:
            for key, value in data.items():
                setattr(existing, key, value)


def _upsert_assignments(session: Session) -> None:
    # Requires materials and finish schemes to be flushed so ids are available.
    session.flush()
    scheme_by_code = {
        scheme.code: scheme for scheme in session.scalars(select(FinishScheme))
    }
    material_by_code = {
        material.code: material for material in session.scalars(select(Material))
    }

    for scheme_code, binding_name, material_code in ASSIGNMENTS_SEED:
        scheme = scheme_by_code[scheme_code]
        material = material_by_code[material_code]
        existing = session.scalar(
            select(MaterialAssignment).where(
                MaterialAssignment.finish_scheme_id == scheme.finish_scheme_id,
                MaterialAssignment.binding_name == binding_name,
            )
        )
        if existing is None:
            session.add(
                MaterialAssignment(
                    finish_scheme_id=scheme.finish_scheme_id,
                    binding_name=binding_name,
                    material_id=material.material_id,
                )
            )
        else:
            existing.material_id = material.material_id


def _clear_assignment_states(session: Session) -> None:
    """Remove all Assembly States. They are created from the Assembly tab."""
    session.execute(delete(AssignmentStateModule))
    session.execute(delete(AssignmentState))


def seed() -> None:
    init_database()
    with SessionLocal() as session:
        _upsert_materials(session)
        _upsert_module_types(session)
        _upsert_finish_schemes(session)
        _upsert_assignments(session)
        _clear_assignment_states(session)
        session.commit()
    print(f"Database initialized and seeded at: {engine.url.database}")
    print(f"  Render materials: {[m['code'] for m in MATERIALS_SEED]}")
    print(f"  Module types: {[m['code'] for m in MODULE_TYPES_SEED]}")
    print(f"  Finish schemes: {[f['code'] for f in FINISH_SCHEMES_SEED]}")
    print(f"  Assignments: {len(ASSIGNMENTS_SEED)}")
    print("  Assembly states: cleared (save from Assembly tab)")


if __name__ == "__main__":
    seed()
