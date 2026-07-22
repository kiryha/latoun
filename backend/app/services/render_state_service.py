"""Resolves a semantic configuration into a full render state.

Flow:
  1. Validate the gang count and module type against the database.
  2. Resolve the ordered list of asset keys for the assembly.
  3. Look up each asset's GLB path in the manifest (geometry registry only).
  4. Resolve semantic material assignments by combining ``init`` with the
     selected finish scheme (single shared resolver).
  5. Generate the prototype BOM.

The frontend reads semantic binding names from the loaded GLB materials and
applies the resolved render materials. This service does not inspect GLB
contents, so missing-binding detection at the geometry level happens on the
frontend at render time.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ValidationError
from ..models import ModuleType
from ..schemas import (
    MaterialOut,
    RenderStateOut,
    ResolvedAsset,
    ResolvedConfiguration,
)
from .asset_manifest_service import get_asset_manifest
from .bom_service import build_prototype_bom
from .material_assignment_service import resolve_assignment_mapping

SUPPORTED_GANG_COUNTS: tuple[int, ...] = (1,)

# Maps a module type code to its slot-module asset key for the 1-gang assembly.
_MODULE_ASSET_KEYS: dict[str, str] = {
    "dimmer": "module.1gang.slot01.dimmer",
    "switch": "module.1gang.slot01.switch",
}

# Static base assets that are always part of the 1-gang assembly.
_BASE_ASSET_KEYS: tuple[str, ...] = (
    "plate.1gang",
    "hardware.1gang.plate_screws",
)


def _validate_module_type(session: Session, module_type_code: str) -> ModuleType:
    module_type = session.scalar(
        select(ModuleType).where(
            ModuleType.code == module_type_code, ModuleType.is_active.is_(True)
        )
    )
    if module_type is None:
        raise ValidationError(f"Invalid or inactive module type: {module_type_code}")
    return module_type


def _resolve_asset_keys(module_type_code: str) -> list[str]:
    module_asset_key = _MODULE_ASSET_KEYS.get(module_type_code)
    if module_asset_key is None:
        raise ValidationError(
            f"No slot module asset defined for module type: {module_type_code}"
        )
    return [*_BASE_ASSET_KEYS, module_asset_key]


def resolve_render_state(
    session: Session,
    *,
    gang_count: int,
    module_type_code: str,
    finish_scheme_code: str,
) -> RenderStateOut:
    """Resolve a semantic configuration into a render state.

    Raises ``ValidationError`` / ``MissingAssetError`` / ``NotFoundError`` on
    invalid input so the API layer can surface a clear message.
    """
    if gang_count not in SUPPORTED_GANG_COUNTS:
        raise ValidationError(
            f"Unsupported gang_count: {gang_count}. "
            f"Supported: {list(SUPPORTED_GANG_COUNTS)}"
        )

    _validate_module_type(session, module_type_code)

    # Combine init + selected finish scheme into a flat binding -> material map.
    selected_scheme, active_sources, mapping, materials = resolve_assignment_mapping(
        session, finish_scheme_code
    )

    manifest = get_asset_manifest()
    asset_keys = _resolve_asset_keys(module_type_code)
    assets = [
        ResolvedAsset(asset_key=asset_key, file=manifest.get(asset_key)["file"])
        for asset_key in asset_keys
    ]

    bom = build_prototype_bom(assets, selected_scheme.code)

    return RenderStateOut(
        is_valid=True,
        configuration=ResolvedConfiguration(
            gang_count=gang_count,
            module_type=module_type_code,
            finish_scheme=selected_scheme.code,
        ),
        active_sources=active_sources,
        material_assignments=mapping,
        materials={
            code: MaterialOut.model_validate(material)
            for code, material in materials.items()
        },
        assets=assets,
        bom=bom,
    )
