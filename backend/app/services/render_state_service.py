"""Resolves a semantic configuration into a full render state.

Flow:
  1. Validate the material code and module type against the database.
  2. Resolve the ordered list of asset keys for the assembly.
  3. Look up each asset's GLB path + material policy in the manifest.
  4. Attach the resolved material parameters.
  5. Generate the prototype BOM.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ValidationError
from ..models import Material, ModuleType
from ..schemas import (
    MaterialOut,
    RenderStateOut,
    ResolvedAsset,
    ResolvedConfiguration,
)
from .asset_manifest_service import get_asset_manifest
from .bom_service import build_prototype_bom

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


def _resolve_material(session: Session, material_code: str) -> Material:
    material = session.scalar(
        select(Material).where(
            Material.code == material_code, Material.is_active.is_(True)
        )
    )
    if material is None:
        raise ValidationError(f"Invalid or inactive material code: {material_code}")
    return material


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
    material_code: str,
) -> RenderStateOut:
    """Resolve a semantic configuration into a render state.

    Raises ``ValidationError`` / ``MissingAssetError`` on invalid input so the
    API layer can surface a clear message.
    """
    if gang_count not in SUPPORTED_GANG_COUNTS:
        raise ValidationError(
            f"Unsupported gang_count: {gang_count}. "
            f"Supported: {list(SUPPORTED_GANG_COUNTS)}"
        )

    material = _resolve_material(session, material_code)
    _validate_module_type(session, module_type_code)

    manifest = get_asset_manifest()
    asset_keys = _resolve_asset_keys(module_type_code)

    assets: list[ResolvedAsset] = []
    for asset_key in asset_keys:
        entry = manifest.get(asset_key)  # raises MissingAssetError if absent
        assets.append(
            ResolvedAsset(
                asset_key=asset_key,
                file=entry["file"],
                material_policy=entry.get("material_policy", "replace_all"),
                material_code=material.code,
            )
        )

    bom = build_prototype_bom(assets, material.code)

    return RenderStateOut(
        is_valid=True,
        configuration=ResolvedConfiguration(
            gang_count=gang_count,
            module_type=module_type_code,
            material=material.code,
        ),
        material=MaterialOut.model_validate(material),
        assets=assets,
        bom=bom,
    )
