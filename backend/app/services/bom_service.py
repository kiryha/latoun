"""Generates the provisional ("prototype") BOM.

The BOM currently represents the visible/renderable assembly parts, not the
final manufacturing BOM with separate certified electrical cores and actuator
components. The UI labels it clearly as a Prototype BOM.
"""

from __future__ import annotations

import re

from ..schemas import BomLine, ResolvedAsset

# Human-readable names for known renderable components.
COMPONENT_DISPLAY_NAMES: dict[str, str] = {
    "plate.1gang": "1-Gang Plate",
    "hardware.1gang.plate_screws": "1-Gang Plate Screw Set",
    "module.1gang.slot01.dimmer": "Rotary Dimmer Module",
    "module.1gang.slot01.switch": "Switch Module",
}

_MODULE_KEY_RE = re.compile(
    r"^module\.(?P<gang>\d+)gang\.slot(?P<slot>\d+)\.(?P<module>.+)$"
)


def _display_name_for(asset_key: str) -> str:
    if asset_key in COMPONENT_DISPLAY_NAMES:
        return COMPONENT_DISPLAY_NAMES[asset_key]

    match = _MODULE_KEY_RE.match(asset_key)
    if match:
        module = match.group("module").replace("_", " ").title()
        slot = int(match.group("slot"))
        return f"{module} (Slot {slot})"

    if asset_key.startswith("plate."):
        return asset_key.replace(".", " ").replace("gang", "-Gang").title()
    if "plate_screws" in asset_key:
        return asset_key.replace(".", " ").replace("_", " ").title()

    return asset_key


def build_prototype_bom(
    assets: list[ResolvedAsset], finish_scheme_code: str
) -> list[BomLine]:
    """Build one BOM line per resolved renderable asset."""
    return [
        BomLine(
            component_code=asset.asset_key,
            display_name=_display_name_for(asset.asset_key),
            quantity=1,
            finish_scheme=finish_scheme_code,
        )
        for asset in assets
    ]
