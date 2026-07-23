// Defaults, key suggestions, and entry shaping helpers for the Geometry tab.

import type {
  AssetManifestEntry,
  AssetType,
  GangCount,
  HardwareManifestEntry,
  PlateManifestEntry,
  SlotModuleManifestEntry,
} from "./types";
import { WALL_PLATES_PREFIX } from "./types";

export function suggestManifestKey(
  entry: AssetManifestEntry,
): string {
  if (entry.asset_type === "plate") {
    return `plate.${entry.gang_count}gang`;
  }
  if (entry.asset_type === "hardware") {
    return `hardware.${entry.gang_count}gang.${entry.hardware_type}`;
  }
  const slot = String(entry.slot_position).padStart(2, "0");
  return `module.${entry.gang_count}gang.slot${slot}.${entry.module_type}`;
}

export function suggestFilePath(entry: AssetManifestEntry): string {
  if (entry.asset_type === "plate") {
    return `${WALL_PLATES_PREFIX}${entry.gang_count}gang_plate.glb`;
  }
  if (entry.asset_type === "hardware") {
    return `${WALL_PLATES_PREFIX}${entry.gang_count}gang_plate_screws.glb`;
  }
  const slot = String(entry.slot_position).padStart(2, "0");
  return `${WALL_PLATES_PREFIX}${entry.gang_count}gang_slot${slot}_${entry.module_type}.glb`;
}

export function createDefaultEntry(
  assetType: AssetType,
  defaultModuleType = "switch",
): AssetManifestEntry {
  if (assetType === "plate") {
    const entry: PlateManifestEntry = {
      asset_type: "plate",
      gang_count: 1,
      file: WALL_PLATES_PREFIX,
      is_active: true,
    };
    return entry;
  }
  if (assetType === "hardware") {
    const entry: HardwareManifestEntry = {
      asset_type: "hardware",
      hardware_type: "plate_screws",
      gang_count: 1,
      file: WALL_PLATES_PREFIX,
      is_active: true,
    };
    return entry;
  }
  const entry: SlotModuleManifestEntry = {
    asset_type: "slot_module",
    gang_count: 1,
    module_type: defaultModuleType,
    slot_position: 1,
    file: WALL_PLATES_PREFIX,
    is_active: true,
  };
  return entry;
}

export function reshapeEntryForAssetType(
  current: AssetManifestEntry,
  nextType: AssetType,
  defaultModuleType = "switch",
): AssetManifestEntry {
  const base = {
    gang_count: current.gang_count,
    file: current.file.startsWith(WALL_PLATES_PREFIX)
      ? current.file
      : WALL_PLATES_PREFIX,
    is_active: current.is_active,
  };

  if (nextType === "plate") {
    return { asset_type: "plate", ...base };
  }
  if (nextType === "hardware") {
    return {
      asset_type: "hardware",
      hardware_type: "plate_screws",
      ...base,
    };
  }
  const slot =
    current.asset_type === "slot_module" ? current.slot_position : 1;
  const moduleType =
    current.asset_type === "slot_module"
      ? current.module_type
      : defaultModuleType;
  return {
    asset_type: "slot_module",
    ...base,
    module_type: moduleType,
    slot_position: Math.min(slot, base.gang_count),
  };
}

export function uniqueCopyKey(
  baseKey: string,
  existingKeys: Set<string>,
): string {
  let candidate = `${baseKey}.copy`;
  let index = 2;
  while (existingKeys.has(candidate)) {
    candidate = `${baseKey}.copy${index}`;
    index += 1;
  }
  return candidate;
}

export function isGangCount(value: number): value is GangCount {
  return value === 1 || value === 2 || value === 3 || value === 4;
}
