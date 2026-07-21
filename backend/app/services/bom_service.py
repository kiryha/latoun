"""Generates the provisional ("prototype") BOM.

The BOM currently represents the visible/renderable assembly parts, not the
final manufacturing BOM with separate certified electrical cores and actuator
components. The UI labels it clearly as a Prototype BOM.
"""

from __future__ import annotations

from ..schemas import BomLine, ResolvedAsset

# Human-readable names for the renderable components in the v0.1 assembly.
COMPONENT_DISPLAY_NAMES: dict[str, str] = {
    "plate.1gang": "1-Gang Plate",
    "hardware.1gang.plate_screws": "1-Gang Plate Screw Set",
    "module.1gang.slot01.dimmer": "Rotary Dimmer Module",
    "module.1gang.slot01.switch": "Switch Module",
}


def _display_name_for(asset_key: str) -> str:
    return COMPONENT_DISPLAY_NAMES.get(asset_key, asset_key)


def build_prototype_bom(
    assets: list[ResolvedAsset], material_code: str
) -> list[BomLine]:
    """Build one BOM line per resolved renderable asset."""
    return [
        BomLine(
            component_code=asset.asset_key,
            display_name=_display_name_for(asset.asset_key),
            quantity=1,
            material=material_code,
        )
        for asset in assets
    ]
