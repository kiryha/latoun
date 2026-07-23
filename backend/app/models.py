"""SQLAlchemy ORM models for the Latoun configurator.

Entities modeled in this iteration:

* ``materials`` — Three.js render-material definitions (implementation-level).
* ``module_types`` — functional module placed in a slot (switch, dimmer, …).
* ``finish_schemes`` — customer-visible finish choices (brass, steel, …) plus
  the hidden internal ``init`` scheme that holds static assignments.
* ``material_assignments`` — the authoritative mapping
  ``finish_scheme + binding_name -> render_material``.
* ``assignment_states`` / ``assignment_state_modules`` — admin-only viewport
  assembly definitions ("Assembly States") for the Assignments tab.
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
    """Functional module type that can be placed in any slot."""

    __tablename__ = "module_types"

    module_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_customer_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FinishScheme(Base):
    """A customer-visible finish selection that resolves multiple materials.

    The hidden ``init`` scheme (``is_customer_visible = False``) carries static
    assignments shared by every assembly. Customer schemes overlay ``init``.
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


class AssignmentState(Base):
    """Admin-only viewport assembly definition for Assignments-tab testing.

    Owns gang count and per-slot modules (geometry). Finish schemes are chosen
    independently at preview time; ``default_finish_scheme_id`` is only the
    initial preview finish.
    """

    __tablename__ = "assignment_states"

    assignment_state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_state_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(128))
    gang_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_finish_scheme_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("finish_schemes.finish_scheme_id"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    default_finish_scheme: Mapped[FinishScheme | None] = relationship()
    modules: Mapped[list["AssignmentStateModule"]] = relationship(
        back_populates="assignment_state",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AssignmentStateModule.slot_number",
    )


class AssignmentStateModule(Base):
    """One module placed in one slot of an assignment state."""

    __tablename__ = "assignment_state_modules"

    assignment_state_module_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_state_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assignment_states.assignment_state_id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    module_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("module_types.module_type_id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    assignment_state: Mapped["AssignmentState"] = relationship(back_populates="modules")
    module_type: Mapped["ModuleType"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "assignment_state_id",
            "slot_number",
            name="uq_assignment_state_slot_number",
        ),
        Index("ix_assignment_state_modules_assignment_state_id", "assignment_state_id"),
        Index("ix_assignment_state_modules_module_type_id", "module_type_id"),
    )
