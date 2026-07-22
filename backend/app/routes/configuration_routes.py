"""Configuration endpoints: resolve, save, list, read."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import (
    ConfigurationDetail,
    ConfigurationRequest,
    ConfigurationSummary,
    RenderStateOut,
)
from ..services import configuration_service
from ..services.render_state_service import resolve_render_state

router = APIRouter(prefix="/api/configurations", tags=["configurations"])


@router.post("/resolve", response_model=RenderStateOut)
def resolve_configuration(
    request: ConfigurationRequest, session: Session = Depends(get_session)
) -> RenderStateOut:
    return resolve_render_state(
        session,
        gang_count=request.gang_count,
        module_type_code=request.module_type,
        finish_scheme_code=request.finish_scheme,
    )


@router.post("", response_model=ConfigurationSummary)
def save_configuration(
    request: ConfigurationRequest, session: Session = Depends(get_session)
) -> ConfigurationSummary:
    configuration = configuration_service.save_configuration(session, request)
    return ConfigurationSummary.model_validate(configuration)


@router.get("", response_model=list[ConfigurationSummary])
def list_configurations(
    session: Session = Depends(get_session),
) -> list[ConfigurationSummary]:
    configurations = configuration_service.list_configurations(session)
    return [ConfigurationSummary.model_validate(c) for c in configurations]


@router.get("/{configuration_id}", response_model=ConfigurationDetail)
def read_configuration(
    configuration_id: int, session: Session = Depends(get_session)
) -> ConfigurationDetail:
    configuration = configuration_service.get_configuration(session, configuration_id)
    # Resolve the render state again from current product data rather than
    # persisting asset paths / material parameters.
    render_state = resolve_render_state(
        session,
        gang_count=configuration.gang_count,
        module_type_code=configuration.module_type_code,
        finish_scheme_code=configuration.finish_scheme_code,
    )
    return ConfigurationDetail(
        configuration=ConfigurationSummary.model_validate(configuration),
        render_state=render_state,
    )


@router.delete("/{configuration_id}", response_model=ConfigurationSummary)
def delete_configuration(
    configuration_id: int, session: Session = Depends(get_session)
) -> ConfigurationSummary:
    configuration = configuration_service.delete_configuration(
        session, configuration_id
    )
    return ConfigurationSummary.model_validate(configuration)
