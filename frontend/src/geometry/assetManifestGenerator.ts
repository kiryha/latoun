// Bulk generation of wall-plate manifest entries (plates, screws, slot modules).

import { suggestFilePath, suggestManifestKey } from "./assetManifestNormalization";
import type {
  AssetManifestEntry,
  GangCount,
  ModuleTypeOption,
} from "./types";
import { GANG_COUNTS } from "./types";

export interface BulkGenerateOptions {
  generatePlates: boolean;
  generatePlateScrews: boolean;
  generateSlotModules: boolean;
  gangCounts: GangCount[];
  moduleTypeCodes: string[];
  activateGenerated: boolean;
}

export interface GeneratedEntry {
  manifestKey: string;
  value: AssetManifestEntry;
}

export interface BulkGeneratePreview {
  toCreate: GeneratedEntry[];
  preservedCount: number;
  conflictCount: number;
}

export function defaultBulkGenerateOptions(
  moduleTypes: ModuleTypeOption[],
): BulkGenerateOptions {
  return {
    generatePlates: true,
    generatePlateScrews: true,
    generateSlotModules: true,
    gangCounts: [...GANG_COUNTS],
    moduleTypeCodes: moduleTypes
      .filter((mt) => mt.is_active)
      .sort((a, b) => a.sort_order - b.sort_order || a.code.localeCompare(b.code))
      .map((mt) => mt.code),
    activateGenerated: true,
  };
}

export function previewBulkGeneration(
  existingKeys: Set<string>,
  options: BulkGenerateOptions,
): BulkGeneratePreview {
  const candidates: GeneratedEntry[] = [];

  for (const gang of options.gangCounts) {
    if (options.generatePlates) {
      const value: AssetManifestEntry = {
        category: "plate",
        gang_count: gang,
        file: "",
        is_active: options.activateGenerated,
      };
      value.file = suggestFilePath(value);
      candidates.push({
        manifestKey: suggestManifestKey(value),
        value,
      });
    }
    if (options.generatePlateScrews) {
      const value: AssetManifestEntry = {
        category: "hardware",
        hardware_type: "plate_screws",
        gang_count: gang,
        file: "",
        is_active: options.activateGenerated,
      };
      value.file = suggestFilePath(value);
      candidates.push({
        manifestKey: suggestManifestKey(value),
        value,
      });
    }
    if (options.generateSlotModules) {
      for (let slot = 1; slot <= gang; slot += 1) {
        for (const moduleType of options.moduleTypeCodes) {
          const value: AssetManifestEntry = {
            category: "slot_module",
            gang_count: gang,
            module_type: moduleType,
            slot_position: slot,
            file: "",
            is_active: options.activateGenerated,
          };
          value.file = suggestFilePath(value);
          candidates.push({
            manifestKey: suggestManifestKey(value),
            value,
          });
        }
      }
    }
  }

  const toCreate = candidates.filter(
    (item) => !existingKeys.has(item.manifestKey),
  );
  return {
    toCreate,
    preservedCount: existingKeys.size,
    conflictCount: candidates.length - toCreate.length,
  };
}
