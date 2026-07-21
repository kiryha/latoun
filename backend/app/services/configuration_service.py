"""Persistence and retrieval of saved configurations."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import NotFoundError
from ..models import Configuration
from ..schemas import ConfigurationRequest
from .render_state_service import resolve_render_state


def _next_configuration_code(session: Session) -> str:
    """Generate a sequential code like ``LAT-CFG-000001``."""
    count = session.scalar(select(func.count(Configuration.configuration_id))) or 0
    return f"LAT-CFG-{count + 1:06d}"


def save_configuration(
    session: Session, request: ConfigurationRequest
) -> Configuration:
    """Validate then persist a semantic configuration.

    Resolution runs first so that we never store an invalid configuration.
    """
    # Resolve to validate material / module type / assets before saving.
    resolve_render_state(
        session,
        gang_count=request.gang_count,
        module_type_code=request.module_type,
        material_code=request.material,
    )

    configuration = Configuration(
        configuration_code=_next_configuration_code(session),
        gang_count=request.gang_count,
        module_type_code=request.module_type,
        material_code=request.material,
    )
    session.add(configuration)
    session.commit()
    session.refresh(configuration)
    return configuration


def list_configurations(session: Session) -> list[Configuration]:
    """Return saved configurations in reverse chronological order."""
    return list(
        session.scalars(
            select(Configuration).order_by(Configuration.created_at.desc())
        )
    )


def get_configuration(session: Session, configuration_id: int) -> Configuration:
    configuration = session.get(Configuration, configuration_id)
    if configuration is None:
        raise NotFoundError(f"Configuration not found: {configuration_id}")
    return configuration
