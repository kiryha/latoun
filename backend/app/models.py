"""SQLAlchemy ORM models for the v0.1 configurator.

Entities modeled in this iteration:

* ``materials`` — Three.js render-material definitions (implementation-level).
* ``module_types`` — functional module placed in a slot (switch / dimmer).
* ``finish_schemes`` — customer-visible finish choices (brass, steel, …) plus
  the hidden internal ``init`` scheme that holds static assignments.
* ``material_assignments`` — the authoritative mapping
  ``finish_scheme + binding_name -> render_material``.
* ``configurations`` — saved semantic product states.

Product logic is intentionally kept in the database / services layer rather
than in the frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Material(Base):
    """A render material: parameters used to build a Three.js material.

    Render materials are implementation-level shader definitions (e.g.
    ``brass_brushed``). They are referenced by material assignments, never
    stored directly on geometry.
    """

    __tablename__ = "materials"

    material_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    base_color: Mapped[str] = mapped_column(String(16))
    metalness: Mapped[float] = mapped_column(Float)
    roughness: Mapped[float] = mapped_column(Float)
    anisotropy: Mapped[float] = mapped_column(Float, default=0.0)
    anisotropy_rotation: Mapped[float] = mapped_column(Float, default=0.0)
    normal_texture_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    roughness_texture_path: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ModuleType(Base):
    """Functional module type that can be placed in a slot (switch / dimmer)."""

    __tablename__ = "module_types"

    module_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class FinishScheme(Base):
    """A customer-visible finish selection that resolves multiple materials.

    The hidden ``init`` scheme (``is_customer_visible = False``) carries static
    assignments shared by every configuration. Customer schemes overlay ``init``.
    """

    __tablename__ = "finish_schemes"

    finish_scheme_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_customer_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    assignments: Mapped[list["MaterialAssignment"]] = relationship(
        back_populates="finish_scheme",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MaterialAssignment(Base):
    """Maps one ``finish_scheme + binding_name`` to one render material.

    The flat table is intentional: ``finish_scheme + binding_name -> material``.
    """

    __tablename__ = "material_assignments"

    material_assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finish_scheme_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("finish_schemes.finish_scheme_id", ondelete="CASCADE"),
        nullable=False,
    )
    binding_name: Mapped[str] = mapped_column(String(64), nullable=False)
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("materials.material_id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    finish_scheme: Mapped["FinishScheme"] = relationship(back_populates="assignments")
    material: Mapped["Material"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "finish_scheme_id",
            "binding_name",
            name="uq_finish_scheme_binding_name",
        ),
        Index("ix_material_assignments_finish_scheme_id", "finish_scheme_id"),
        Index("ix_material_assignments_binding_name", "binding_name"),
        Index("ix_material_assignments_material_id", "material_id"),
    )


class Configuration(Base):
    """A saved semantic configuration.

    We store only stable string codes here. Asset paths and material
    parameters are resolved again from current product data on read, never
    persisted, per the brief. The finish is stored as ``finish_scheme_code``.
    """

    __tablename__ = "configurations"

    configuration_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True
    )
    gang_count: Mapped[int] = mapped_column(Integer, default=1)
    module_type_code: Mapped[str] = mapped_column(String(64))
    finish_scheme_code: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
