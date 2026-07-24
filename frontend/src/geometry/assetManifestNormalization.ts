// Defaults, key suggestions, and entry shaping helpers for the Geometry tab.

import type {
  AssetCategory,
  AssetManifestEntry,
  GangCount,
  HardwareManifestEntry,
  PlateManifestEntry,
  SlotModuleManifestEntry,
} from "./types";

export function suggestManifestKey(
  entry: AssetManifestEntry,
): string {
  if (entry.category === "plate") {
    return `plate.${entry.gang_count}gang`;
  }
  if (entry.category === "hardware") {
    return `hardware.${entry.gang_count}gang.${entry.hardware_type}`;
  }
  return `module.${entry.gang_count}gang.slot${entry.slot_position}.${entry.module_type}`;
}

/** Suggested bare file name (folder lives in manifest properties.glb_folder). */
export function suggestFilePath(entry: AssetManifestEntry): string {
  if (entry.category === "plate") {
    return `${entry.gang_count}gang_plate.glb`;
  }
  if (entry.category === "hardware") {
    return `${entry.gang_count}gang_plate_screws.glb`;
  }
  return `${entry.gang_count}gang_slot${entry.slot_position}_${entry.module_type}.glb`;
}

export function createDefaultEntry(
  category: AssetCategory,
  defaultModuleType = "switch",
): AssetManifestEntry {
  if (category === "plate") {
    const entry: PlateManifestEntry = {
      category: "plate",
      gang_count: 1,
      file: "",
      is_active: true,
    };
    return entry;
  }
  if (category === "hardware") {
    const entry: HardwareManifestEntry = {
      category: "hardware",
      hardware_type: "plate_screws",
      gang_count: 1,
      file: "",
      is_active: true,
    };
    return entry;
  }
  const entry: SlotModuleManifestEntry = {
    category: "slot_module",
    gang_count: 1,
    module_type: defaultModuleType,
    slot_position: 1,
    file: "",
    is_active: true,
  };
  return entry;
}

export function reshapeEntryForCategory(
  current: AssetManifestEntry,
  nextCategory: AssetCategory,
  defaultModuleType = "switch",
): AssetManifestEntry {
  const base = {
    gang_count: current.gang_count,
    file: current.file,
    is_active: current.is_active,
  };

  if (nextCategory === "plate") {
    return { category: "plate", ...base };
  }
  if (nextCategory === "hardware") {
    return {
      category: "hardware",
      hardware_type: "plate_screws",
      ...base,
    };
  }
  const slot =
    current.category === "slot_module" ? current.slot_position : 1;
  const moduleType =
    current.category === "slot_module"
      ? current.module_type
      : defaultModuleType;
  return {
    category: "slot_module",
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
