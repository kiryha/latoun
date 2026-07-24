"""Wall-plate asset manifest endpoints for the Geometry tab."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import ModuleType
from ..schemas import (
    AssetFileStatusOut,
    AssetManifestDocument,
    AssetManifestGetOut,
    AssetManifestProperties,
    AssetManifestSaveOut,
    AssetManifestSaveRequest,
    AssetManifestValidateOut,
    AssetManifestValidateRequest,
    GeometryConversionRequest,
    GeometryConversionOut,
    GeometryPartsInventoryOut,
    ManifestIssueOut,
    ModuleTypeOut,
)
from ..services import asset_manifest_service as manifest_service
from ..services import geometry_conversion_service

router = APIRouter(prefix="/api", tags=["wall-plates"])


@router.get("/module-types", response_model=list[ModuleTypeOut])
def list_module_types(session: Session = Depends(get_session)) -> list[ModuleTypeOut]:
    """All module types (including inactive) for Geometry editing."""
    rows = session.scalars(
        select(ModuleType).order_by(ModuleType.sort_order, ModuleType.code)
    ).all()
    return [ModuleTypeOut.model_validate(row) for row in rows]


@router.get(
    "/wall-plates/asset-manifest",
    response_model=AssetManifestGetOut,
)
def get_wall_plate_asset_manifest() -> AssetManifestGetOut:
    assets, glb_folder, revision = manifest_service.get_manifest_document()
    return AssetManifestGetOut(
        manifest=AssetManifestDocument(
            properties=AssetManifestProperties(glb_folder=glb_folder),
            parts=assets,
        ),
        revision=revision,
    )


@router.put(
    "/wall-plates/asset-manifest",
    response_model=AssetManifestSaveOut,
)
def save_wall_plate_asset_manifest(
    payload: AssetManifestSaveRequest,
    session: Session = Depends(get_session),
) -> AssetManifestSaveOut:
    assets, glb_folder, revision, warnings = manifest_service.save_manifest(
        session,
        assets=payload.manifest.parts,
        glb_folder=payload.manifest.properties.glb_folder,
        expected_revision=payload.expected_revision,
    )
    return AssetManifestSaveOut(
        manifest=AssetManifestDocument(
            properties=AssetManifestProperties(glb_folder=glb_folder),
            parts=assets,
        ),
        revision=revision,
        warnings=warnings,
        saved=True,
    )


@router.post(
    "/wall-plates/asset-manifest/validate",
    response_model=AssetManifestValidateOut,
)
def validate_wall_plate_asset_manifest(
    payload: AssetManifestValidateRequest,
    session: Session = Depends(get_session),
) -> AssetManifestValidateOut:
    module_types = {
        row.code: row
        for row in session.scalars(select(ModuleType)).all()
    }
    result = manifest_service.validate_manifest(
        payload.manifest.parts, module_types=module_types
    )
    return AssetManifestValidateOut(
        ok=result.ok,
        errors=[
            ManifestIssueOut(
                level=issue.level, message=issue.message, asset_key=issue.asset_key
            )
            for issue in result.errors
        ],
        warnings=[
            ManifestIssueOut(
                level=issue.level, message=issue.message, asset_key=issue.asset_key
            )
            for issue in result.warnings
        ],
    )


@router.get(
    "/wall-plates/asset-file-status",
    response_model=AssetFileStatusOut,
)
def wall_plate_asset_file_status(
    path: list[str] = Query(default=[]),
) -> AssetFileStatusOut:
    """Return whether each public GLB path exists under frontend/public."""
    return AssetFileStatusOut(files=manifest_service.check_glb_availability(path))


@router.post(
    "/wall-plates/convert-parts",
    response_model=GeometryConversionOut,
)
def convert_wall_plate_parts(
    payload: GeometryConversionRequest,
) -> GeometryConversionOut:
    """Convert all top-level source OBJ files to same-named GLBs."""
    return GeometryConversionOut.model_validate(
        geometry_conversion_service.convert_all_parts(
            skip_existing=payload.skip_existing
        )
    )


@router.get(
    "/wall-plates/parts",
    response_model=GeometryPartsInventoryOut,
)
def list_wall_plate_parts() -> GeometryPartsInventoryOut:
    """List source OBJ files and whether their same-named GLBs exist."""
    return GeometryPartsInventoryOut.model_validate(
        geometry_conversion_service.list_parts()
    )
