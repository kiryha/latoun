"""Initialize and seed the SQLite database.

Run as a module from the ``backend`` directory:

    python -m app.seed

The database is fully reproducible from this script; the active SQLite file is
not committed to Git.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, init_database
from .models import Material, ModuleType

MATERIALS_SEED = [
    {
        "code": "brass",
        "display_name": "Brass",
        "base_color": "#B88A44",
        "metalness": 1.0,
        "roughness": 0.28,
        "anisotropy": 0.5,
        "anisotropy_rotation": 0.0,
        "normal_texture_path": None,
        "roughness_texture_path": None,
        "is_active": True,
    },
    {
        "code": "steel",
        "display_name": "Steel",
        "base_color": "#B7BABD",
        "metalness": 1.0,
        "roughness": 0.32,
        "anisotropy": 0.45,
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


def seed() -> None:
    init_database()
    with SessionLocal() as session:
        _upsert_materials(session)
        _upsert_module_types(session)
        session.commit()
    print(f"Database initialized and seeded at: {engine.url.database}")
    print(f"  Materials: {[m['code'] for m in MATERIALS_SEED]}")
    print(f"  Module types: {[m['code'] for m in MODULE_TYPES_SEED]}")


if __name__ == "__main__":
    seed()
