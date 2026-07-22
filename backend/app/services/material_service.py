"""CRUD for materials used by the material manager.

Materials are the source of truth for Three.js ``MeshPhysicalMaterial`` render
parameters. Saved configurations reference a material by its stable ``code``,
so deleting a material that is still referenced is refused to avoid dangling
configurations.
"""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import Configuration, Material
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
        # Cascade the rename to saved configurations so references stay valid.
        session.execute(
            update(Configuration)
            .where(Configuration.material_code == material.code)
            .values(material_code=new_code)
        )
        material.code = new_code

    for key, value in payload.items():
        setattr(material, key, value)
    session.commit()
    session.refresh(material)
    return material


def delete_material(session: Session, code: str) -> Material:
    material = get_material(session, code)

    reference_count = (
        session.scalar(
            select(func.count(Configuration.configuration_id)).where(
                Configuration.material_code == code
            )
        )
        or 0
    )
    if reference_count > 0:
        raise ConflictError(
            f"Cannot delete material '{code}': it is referenced by "
            f"{reference_count} saved configuration(s)."
        )

    session.delete(material)
    session.commit()
    return material
