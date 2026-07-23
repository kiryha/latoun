"""Assignment state admin endpoints plus render-state resolution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import AssignmentStateCreate, AssignmentStateOut, AssignmentStateUpdate
from ..schemas import RenderStateOut
from ..services import assignment_state_service

router = APIRouter(prefix="/api/assignment-states", tags=["assignment-states"])


@router.get("", response_model=list[AssignmentStateOut])
def list_assignment_states(
    is_active: bool | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[AssignmentStateOut]:
    return assignment_state_service.list_assignment_states(
        session, is_active=is_active
    )


@router.post("", response_model=AssignmentStateOut, status_code=201)
def create_assignment_state(
    payload: AssignmentStateCreate, session: Session = Depends(get_session)
) -> AssignmentStateOut:
    return assignment_state_service.create_assignment_state(session, payload)


@router.get("/{assignment_state_id}", response_model=AssignmentStateOut)
def get_assignment_state(
    assignment_state_id: int, session: Session = Depends(get_session)
) -> AssignmentStateOut:
    return assignment_state_service.get_assignment_state(session, assignment_state_id)


@router.put("/{assignment_state_id}", response_model=AssignmentStateOut)
def update_assignment_state(
    assignment_state_id: int,
    payload: AssignmentStateUpdate,
    session: Session = Depends(get_session),
) -> AssignmentStateOut:
    return assignment_state_service.update_assignment_state(
        session, assignment_state_id, payload
    )


@router.delete("/{assignment_state_id}", response_model=AssignmentStateOut)
def delete_assignment_state(
    assignment_state_id: int, session: Session = Depends(get_session)
) -> AssignmentStateOut:
    return assignment_state_service.delete_assignment_state(
        session, assignment_state_id
    )


@router.get("/{assignment_state_id}/render-state", response_model=RenderStateOut)
def resolve_assignment_state_render(
    assignment_state_id: int,
    finish_scheme: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> RenderStateOut:
    """Load geometry from the assignment state; materials from finish_scheme."""
    return assignment_state_service.resolve_assignment_state_render(
        session, assignment_state_id, finish_scheme_code=finish_scheme
    )
