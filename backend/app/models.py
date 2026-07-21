"""SQLAlchemy ORM models for the v0.1 configurator.

Only the entities needed by this iteration are modeled: materials, module
types, and saved configurations. Product logic is intentionally kept in the
database / services layer rather than in the frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Material(Base):
    """Physical material with Three.js MeshPhysicalMaterial render parameters."""

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


class Configuration(Base):
    """A saved semantic configuration.

    We store only stable string codes here. Asset paths and material
    parameters are resolved again from current product data on read, never
    persisted, per the brief.
    """

    __tablename__ = "configurations"

    configuration_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True
    )
    gang_count: Mapped[int] = mapped_column(Integer, default=1)
    module_type_code: Mapped[str] = mapped_column(String(64))
    material_code: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
