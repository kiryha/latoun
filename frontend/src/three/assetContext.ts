// Human-readable context labels for validation / material error reports.

import type { MissingAssetWarning, ResolvedAsset } from "../types";

export function describeAssetContext(asset: ResolvedAsset): string {
  if (asset.role === "plate") return "plate";
  if (asset.role === "plate_screws") return "plate screws";
  if (asset.role === "module" || asset.slot_number != null) {
    const slot = asset.slot_number ?? "?";
    const moduleType = (asset.module_type ?? "module").split("_").join(" ");
    return `slot ${slot} ${moduleType}`;
  }

  if (asset.asset_key.startsWith("plate.")) return "plate";
  if (asset.asset_key.includes("plate_screws")) return "plate screws";

  const match = asset.asset_key.match(
    /^module\.\d+gang\.slot(\d+)\.(.+)$/,
  );
  if (match) {
    return `slot ${Number(match[1])} ${match[2].split("_").join(" ")}`;
  }
  return asset.asset_key;
}

export function describeMissingAssetContext(
  warning: MissingAssetWarning,
): string {
  if (warning.role === "plate") return "plate";
  if (warning.role === "plate_screws") return "plate screws";
  if (warning.slot_number != null) {
    const moduleType = (warning.module_type ?? "module").split("_").join(" ");
    return `slot ${warning.slot_number} ${moduleType}`;
  }
  return warning.asset_key;
}

export function placeholderOffsetX(
  slotNumber: number,
  gangCount: number,
): number {
  // Spread placeholders left-to-right when real slot GLBs are missing.
  const spacing = 0.055;
  const start = -((gangCount - 1) * spacing) / 2;
  return start + (slotNumber - 1) * spacing;
}
