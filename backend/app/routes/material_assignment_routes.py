"""Material assignment endpoints addressed by assignment id.

    PUT    /api/material-assignments/{material_assignment_id}
    DELETE /api/material-assignments/{material_assignment_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import MaterialAssignmentOut, MaterialAssignmentUpdate
from ..services import material_assignment_service

router = APIRouter(prefix="/api/material-assignments", tags=["material-assignments"])


@router.put("/{material_assignment_id}", response_model=MaterialAssignmentOut)
def update_assignment(
    material_assignment_id: int,
    payload: MaterialAssignmentUpdate,
    session: Session = Depends(get_session),
) -> MaterialAssignmentOut:
    return material_assignment_service.update_assignment(
        session, material_assignment_id, payload
    )


@router.delete("/{material_assignment_id}", response_model=MaterialAssignmentOut)
def delete_assignment(
    material_assignment_id: int, session: Session = Depends(get_session)
) -> MaterialAssignmentOut:
    return material_assignment_service.delete_assignment(
        session, material_assignment_id
    )
