"""Catalog endpoints: available materials, module types, gang counts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Material, ModuleType
from ..schemas import CatalogOut, MaterialOut, ModuleTypeOut
from ..services.render_state_service import SUPPORTED_GANG_COUNTS

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/catalog", response_model=CatalogOut)
def get_catalog(session: Session = Depends(get_session)) -> CatalogOut:
    materials = session.scalars(
        select(Material).where(Material.is_active.is_(True)).order_by(Material.code)
    ).all()
    module_types = session.scalars(
        select(ModuleType)
        .where(ModuleType.is_active.is_(True))
        .order_by(ModuleType.code)
    ).all()

    return CatalogOut(
        materials=[MaterialOut.model_validate(m) for m in materials],
        module_types=[ModuleTypeOut.model_validate(mt) for mt in module_types],
        gang_counts=list(SUPPORTED_GANG_COUNTS),
    )
