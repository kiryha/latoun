"""Ad-hoc render-state resolution for the Assembly tab."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import RenderResolveRequest, RenderStateOut
from ..services.render_state_service import resolve_render_state

router = APIRouter(prefix="/api/render", tags=["render"])


@router.post("/resolve", response_model=RenderStateOut)
def resolve_render(
    request: RenderResolveRequest, session: Session = Depends(get_session)
) -> RenderStateOut:
    return resolve_render_state(
        session,
        gang_count=request.gang_count,
        modules=[(row.slot_number, row.module_type) for row in request.modules],
        finish_scheme_code=request.finish_scheme,
    )
