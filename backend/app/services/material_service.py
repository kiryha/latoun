"""CRUD for render materials used by the material manager.

Materials are the source of truth for Three.js ``MeshPhysicalMaterial`` render
parameters. Material assignments reference a material by foreign key, so
deleting a material that is still referenced by an assignment is refused to
avoid dangling assignments.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import Material, MaterialAssignment
from ..schemas import MaterialCreate, MaterialUpdate


def list_materials(session: Session) -> list[Material]:
    """Return all materials (active and inactive) ordered by code."""
    return list(session.scalars(select(Material).order_by(Material.code)))


def get_material(session: Session, code: str) -> Material:
    material = session.scalar(select(Material).where(Material.code == code))
    if material is None:
        raise NotFoundError(f"Material not found: {code}")
    return material


def create_material(session: Session, data: MaterialCreate) -> Material:
    existing = session.scalar(select(Material).where(Material.code == data.code))
    if existing is not None:
        raise ConflictError(f"Material code already exists: {data.code}")

    material = Material(**data.model_dump())
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def update_material(session: Session, code: str, data: MaterialUpdate) -> Material:
    material = get_material(session, code)
    # Only apply fields the client actually sent (partial update).
    payload = data.model_dump(exclude_unset=True)

    new_code = payload.pop("code", None)
    if new_code is not None and new_code != material.code:
        clash = session.scalar(select(Material).where(Material.code == new_code))
        if clash is not None:
            raise ConflictError(f"Material code already exists: {new_code}")
        # Assignments reference the material by foreign key (material_id), so a
        # code rename needs no cascade.
        material.code = new_code

    for key, value in payload.items():
        setattr(material, key, value)
    session.commit()
    session.refresh(material)
    return material


def delete_material(session: Session, code: str) -> Material:
    material = get_material(session, code)

    usages = session.scalars(
        select(MaterialAssignment)
        .where(MaterialAssignment.material_id == material.material_id)
        .order_by(MaterialAssignment.binding_name)
    ).all()
    if usages:
        detail = "; ".join(
            f"{usage.finish_scheme.code} -> {usage.binding_name}" for usage in usages
        )
        raise ConflictError(
            f"Cannot delete material '{code}': it is used by "
            f"{len(usages)} assignment(s): {detail}. Reassign or remove those "
            "assignments first."
        )

    session.delete(material)
    session.commit()
    return material
