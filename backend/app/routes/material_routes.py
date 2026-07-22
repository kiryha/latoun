"""Material management endpoints: list, create, update/rename, delete."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import MaterialAdminOut, MaterialCreate, MaterialUpdate
from ..services import material_service

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("", response_model=list[MaterialAdminOut])
def list_materials(session: Session = Depends(get_session)) -> list[MaterialAdminOut]:
    materials = material_service.list_materials(session)
    return [MaterialAdminOut.model_validate(m) for m in materials]


@router.post("", response_model=MaterialAdminOut, status_code=201)
def create_material(
    payload: MaterialCreate, session: Session = Depends(get_session)
) -> MaterialAdminOut:
    material = material_service.create_material(session, payload)
    return MaterialAdminOut.model_validate(material)


@router.patch("/{code}", response_model=MaterialAdminOut)
def update_material(
    code: str, payload: MaterialUpdate, session: Session = Depends(get_session)
) -> MaterialAdminOut:
    material = material_service.update_material(session, code, payload)
    return MaterialAdminOut.model_validate(material)


@router.delete("/{code}", response_model=MaterialAdminOut)
def delete_material(
    code: str, session: Session = Depends(get_session)
) -> MaterialAdminOut:
    material = material_service.delete_material(session, code)
    return MaterialAdminOut.model_validate(material)
