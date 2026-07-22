"""Finish scheme endpoints plus nested assignment endpoints.

    GET    /api/finish-schemes
    POST   /api/finish-schemes
    GET    /api/finish-schemes/{finish_scheme_id}
    PUT    /api/finish-schemes/{finish_scheme_id}
    DELETE /api/finish-schemes/{finish_scheme_id}

    GET    /api/finish-schemes/{finish_scheme_id}/assignments
    POST   /api/finish-schemes/{finish_scheme_id}/assignments
    PUT    /api/finish-schemes/{finish_scheme_id}/assignments   (bulk save)

    GET    /api/finish-schemes/{finish_scheme_code}/resolved-assignments
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import (
    BulkAssignmentsRequest,
    FinishSchemeCreate,
    FinishSchemeOut,
    FinishSchemeUpdate,
    MaterialAssignmentCreate,
    MaterialAssignmentOut,
    ResolvedAssignmentsOut,
)
from ..services import finish_scheme_service, material_assignment_service

router = APIRouter(prefix="/api/finish-schemes", tags=["finish-schemes"])


@router.get("", response_model=list[FinishSchemeOut])
def list_finish_schemes(
    is_active: bool | None = None,
    is_customer_visible: bool | None = None,
    session: Session = Depends(get_session),
) -> list[FinishSchemeOut]:
    schemes = finish_scheme_service.list_finish_schemes(
        session, is_active=is_active, is_customer_visible=is_customer_visible
    )
    return [FinishSchemeOut.model_validate(scheme) for scheme in schemes]


@router.post("", response_model=FinishSchemeOut, status_code=201)
def create_finish_scheme(
    payload: FinishSchemeCreate, session: Session = Depends(get_session)
) -> FinishSchemeOut:
    scheme = finish_scheme_service.create_finish_scheme(session, payload)
    return FinishSchemeOut.model_validate(scheme)


@router.get("/{finish_scheme_id}", response_model=FinishSchemeOut)
def get_finish_scheme(
    finish_scheme_id: int, session: Session = Depends(get_session)
) -> FinishSchemeOut:
    scheme = finish_scheme_service.get_finish_scheme(session, finish_scheme_id)
    return FinishSchemeOut.model_validate(scheme)


@router.put("/{finish_scheme_id}", response_model=FinishSchemeOut)
def update_finish_scheme(
    finish_scheme_id: int,
    payload: FinishSchemeUpdate,
    session: Session = Depends(get_session),
) -> FinishSchemeOut:
    scheme = finish_scheme_service.update_finish_scheme(
        session, finish_scheme_id, payload
    )
    return FinishSchemeOut.model_validate(scheme)


@router.delete("/{finish_scheme_id}", response_model=FinishSchemeOut)
def delete_finish_scheme(
    finish_scheme_id: int, session: Session = Depends(get_session)
) -> FinishSchemeOut:
    scheme = finish_scheme_service.delete_finish_scheme(session, finish_scheme_id)
    return FinishSchemeOut.model_validate(scheme)


# --------------------------------------------------------------------------- #
# Nested assignments
# --------------------------------------------------------------------------- #
@router.get(
    "/{finish_scheme_id}/assignments",
    response_model=list[MaterialAssignmentOut],
)
def list_assignments(
    finish_scheme_id: int, session: Session = Depends(get_session)
) -> list[MaterialAssignmentOut]:
    return material_assignment_service.list_assignments(session, finish_scheme_id)


@router.post(
    "/{finish_scheme_id}/assignments",
    response_model=MaterialAssignmentOut,
    status_code=201,
)
def create_assignment(
    finish_scheme_id: int,
    payload: MaterialAssignmentCreate,
    session: Session = Depends(get_session),
) -> MaterialAssignmentOut:
    return material_assignment_service.create_assignment(
        session, finish_scheme_id, payload
    )


@router.put(
    "/{finish_scheme_id}/assignments",
    response_model=list[MaterialAssignmentOut],
)
def bulk_save_assignments(
    finish_scheme_id: int,
    payload: BulkAssignmentsRequest,
    session: Session = Depends(get_session),
) -> list[MaterialAssignmentOut]:
    return material_assignment_service.bulk_save_assignments(
        session, finish_scheme_id, payload.assignments
    )


# --------------------------------------------------------------------------- #
# Resolved assignments (by code)
# --------------------------------------------------------------------------- #
@router.get(
    "/{finish_scheme_code}/resolved-assignments",
    response_model=ResolvedAssignmentsOut,
)
def resolved_assignments(
    finish_scheme_code: str, session: Session = Depends(get_session)
) -> ResolvedAssignmentsOut:
    return material_assignment_service.resolve_assignments(session, finish_scheme_code)
