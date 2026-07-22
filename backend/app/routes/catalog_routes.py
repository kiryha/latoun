"""Catalog endpoints: available materials, module types, gang counts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import ModuleType
from ..schemas import CatalogFinishScheme, CatalogOut, ModuleTypeOut
from ..services.finish_scheme_service import list_finish_schemes
from ..services.render_state_service import SUPPORTED_GANG_COUNTS

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/catalog", response_model=CatalogOut)
def get_catalog(session: Session = Depends(get_session)) -> CatalogOut:
    # Finish buttons in the Assembly tab come from customer-visible active finish
    # schemes, never from the materials table. This excludes the hidden ``init``.
    finish_schemes = list_finish_schemes(
        session, is_active=True, is_customer_visible=True
    )
    module_types = session.scalars(
        select(ModuleType)
        .where(ModuleType.is_active.is_(True))
        .order_by(ModuleType.code)
    ).all()

    return CatalogOut(
        finish_schemes=[
            CatalogFinishScheme(
                code=scheme.code,
                display_name=scheme.display_name,
                description=scheme.description,
            )
            for scheme in finish_schemes
        ],
        module_types=[ModuleTypeOut.model_validate(mt) for mt in module_types],
        gang_counts=list(SUPPORTED_GANG_COUNTS),
    )
