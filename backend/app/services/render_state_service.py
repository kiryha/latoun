"""Resolves an assembly (slots + finish) into a full render state.

Flow:
  1. Validate gang count and every slot module against the database.
  2. Resolve the ordered list of asset keys for the assembly.
  3. Look up each asset's GLB path in the manifest (geometry registry only).
     Missing keys become asset warnings — they do not fail configuration.
  4. Resolve semantic material assignments by combining ``init`` with the
     selected finish scheme (single shared resolver).
  5. Generate the prototype BOM from available assets only.

Geometry is derived from gang count + per-slot modules. Finish schemes are
independent and only affect material assignments.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ValidationError
from ..models import ModuleType
from ..schemas import (
    MaterialOut,
    MissingAssetWarning,
    RenderStateOut,
    ResolvedAssembly,
    ResolvedAsset,
    ResolvedSlotModule,
)
from .asset_manifest_service import get_asset_manifest
from .bom_service import build_prototype_bom
from .material_assignment_service import resolve_assignment_mapping

SUPPORTED_GANG_COUNTS: tuple[int, ...] = (1, 2, 3, 4)


def _validate_module_type(session: Session, module_type_code: str) -> ModuleType:
    module_type = session.scalar(
        select(ModuleType).where(
            ModuleType.code == module_type_code, ModuleType.is_active.is_(True)
        )
    )
    if module_type is None:
        raise ValidationError(f"Invalid or inactive module type: {module_type_code}")
    return module_type


def _module_asset_key(gang_count: int, slot_number: int, module_type_code: str) -> str:
    return f"module.{gang_count}gang.slot{slot_number:02d}.{module_type_code}"


def _normalize_slot_modules(
    session: Session,
    *,
    gang_count: int,
    modules: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    if gang_count not in SUPPORTED_GANG_COUNTS:
        raise ValidationError(
            f"Unsupported gang_count: {gang_count}. "
            f"Supported: {list(SUPPORTED_GANG_COUNTS)}"
        )
    if not modules:
        raise ValidationError("At least one slot module is required.")

    slot_numbers = [slot for slot, _code in modules]
    if len(slot_numbers) != len(set(slot_numbers)):
        raise ValidationError("Duplicate slot numbers are not allowed.")

    expected_slots = set(range(1, gang_count + 1))
    actual_slots = set(slot_numbers)
    if actual_slots != expected_slots:
        raise ValidationError(
            f"Modules must cover slots {sorted(expected_slots)} exactly; "
            f"got {sorted(actual_slots)}."
        )

    normalized: list[tuple[int, str]] = []
    for slot_number, module_type_code in sorted(modules, key=lambda item: item[0]):
        _validate_module_type(session, module_type_code)
        normalized.append((slot_number, module_type_code))
    return normalized


def _describe_missing_module(
    *,
    gang_count: int,
    slot_number: int,
    module_type_code: str,
) -> str:
    readable = module_type_code.replace("_", " ")
    return (
        f"No GLB is registered for {gang_count}-gang slot {slot_number} "
        f"{readable}."
    )


def _resolve_geometry(
    gang_count: int, normalized: list[tuple[int, str]]
) -> tuple[list[ResolvedAsset], list[MissingAssetWarning]]:
    """Resolve plate, screws, and slot modules via structured active lookup."""
    manifest = get_asset_manifest()
    assets: list[ResolvedAsset] = []
    missing: list[MissingAssetWarning] = []

    plate_fallback_key = f"plate.{gang_count}gang"
    plate_match = manifest.find_active(category="plate", gang_count=gang_count)
    if plate_match is None:
        missing.append(
            MissingAssetWarning(
                asset_key=plate_fallback_key,
                role="plate",
                gang_count=gang_count,
                message=f"No GLB is registered for {gang_count}-gang plate.",
            )
        )
    else:
        plate_key, plate_entry = plate_match
        assets.append(
            ResolvedAsset(
                asset_key=plate_key,
                file=manifest.url_for_entry(plate_entry),
                role="plate",
            )
        )

    screws_fallback_key = f"hardware.{gang_count}gang.plate_screws"
    screws_match = manifest.find_active(
        category="hardware",
        gang_count=gang_count,
        hardware_type="plate_screws",
    )
    if screws_match is None:
        missing.append(
            MissingAssetWarning(
                asset_key=screws_fallback_key,
                role="plate_screws",
                gang_count=gang_count,
                message=f"No GLB is registered for {gang_count}-gang plate screws.",
            )
        )
    else:
        screws_key, screws_entry = screws_match
        assets.append(
            ResolvedAsset(
                asset_key=screws_key,
                file=manifest.url_for_entry(screws_entry),
                role="plate_screws",
            )
        )

    for slot_number, module_type_code in normalized:
        fallback_key = _module_asset_key(gang_count, slot_number, module_type_code)
        match = manifest.find_active(
            category="slot_module",
            gang_count=gang_count,
            slot_position=slot_number,
            module_type=module_type_code,
        )
        if match is None:
            missing.append(
                MissingAssetWarning(
                    asset_key=fallback_key,
                    role="module",
                    gang_count=gang_count,
                    slot_number=slot_number,
                    module_type=module_type_code,
                    message=_describe_missing_module(
                        gang_count=gang_count,
                        slot_number=slot_number,
                        module_type_code=module_type_code,
                    ),
                )
            )
            continue
        asset_key, entry = match
        assets.append(
            ResolvedAsset(
                asset_key=asset_key,
                file=manifest.url_for_entry(entry),
                role="module",
                slot_number=slot_number,
                module_type=module_type_code,
            )
        )

    return assets, missing


def resolve_render_state(
    session: Session,
    *,
    gang_count: int,
    modules: list[tuple[int, str]],
    finish_scheme_code: str,
    assignment_state_code: str | None = None,
    assignment_state_display_name: str | None = None,
) -> RenderStateOut:
    """Resolve geometry + finish into a render state.

    ``modules`` is a list of ``(slot_number, module_type_code)`` covering every
    slot from 1..gang_count exactly once.

    Configuration validity is independent of geometry availability: missing
    GLBs produce ``missing_assets`` warnings and ``assets_complete=False``.
    """
    normalized = _normalize_slot_modules(
        session, gang_count=gang_count, modules=modules
    )

    selected_scheme, active_sources, mapping, materials = resolve_assignment_mapping(
        session, finish_scheme_code
    )

    assets, missing_assets = _resolve_geometry(gang_count, normalized)
    bom = build_prototype_bom(assets, selected_scheme.code)

    return RenderStateOut(
        is_valid=True,
        assets_complete=len(missing_assets) == 0,
        assembly=ResolvedAssembly(
            gang_count=gang_count,
            modules=[
                ResolvedSlotModule(slot_number=slot, module_type=code)
                for slot, code in normalized
            ],
            finish_scheme=selected_scheme.code,
            assignment_state_code=assignment_state_code,
            assignment_state_display_name=assignment_state_display_name,
        ),
        active_sources=active_sources,
        material_assignments=mapping,
        materials={
            code: MaterialOut.model_validate(material)
            for code, material in materials.items()
        },
        assets=assets,
        missing_assets=missing_assets,
        bom=bom,
    )
