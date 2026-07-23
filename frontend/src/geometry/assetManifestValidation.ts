// Client-side validation for the wall-plate asset manifest working copy.

import type {
  AssetManifestEntry,
  EditableManifestEntry,
  ManifestIssue,
  ManifestValidationResult,
  ModuleTypeOption,
} from "./types";
import { WALL_PLATES_PREFIX } from "./types";

const ASSET_TYPES = new Set(["plate", "hardware", "slot_module"]);

function resolverIdentity(
  entry: AssetManifestEntry,
): string | null {
  if (entry.asset_type === "plate") {
    return `plate:${entry.gang_count}`;
  }
  if (entry.asset_type === "hardware") {
    return `hardware:${entry.hardware_type}:${entry.gang_count}`;
  }
  return `slot_module:${entry.gang_count}:${entry.slot_position}:${entry.module_type}`;
}

function validateEntry(
  row: EditableManifestEntry,
  moduleTypesByCode: Map<string, ModuleTypeOption>,
): { errors: ManifestIssue[]; warnings: ManifestIssue[] } {
  const errors: ManifestIssue[] = [];
  const warnings: ManifestIssue[] = [];
  const key = row.manifestKey;
  const entry = row.value;
  const base = { assetKey: key, clientId: row.clientId };

  if (!key.trim()) {
    errors.push({ level: "error", message: "Manifest key is empty.", ...base });
  }

  if (!ASSET_TYPES.has(entry.asset_type)) {
    errors.push({
      level: "error",
      message: `Unrecognized asset_type: ${entry.asset_type}.`,
      ...base,
    });
  }

  if (![1, 2, 3, 4].includes(entry.gang_count)) {
    errors.push({
      level: "error",
      message: "Gang count must be between 1 and 4.",
      ...base,
    });
  }

  if (typeof entry.is_active !== "boolean") {
    errors.push({
      level: "error",
      message: "is_active must be a boolean.",
      ...base,
    });
  }

  const file = entry.file?.trim() ?? "";
  if (!file) {
    errors.push({ level: "error", message: "File path is required.", ...base });
  } else {
    if (!file.startsWith(WALL_PLATES_PREFIX)) {
      errors.push({
        level: "error",
        message: `File path must begin with ${WALL_PLATES_PREFIX}.`,
        ...base,
      });
    }
    if (!file.toLowerCase().endsWith(".glb")) {
      errors.push({
        level: "error",
        message: "File path must end with .glb.",
        ...base,
      });
    }
    if (file.includes("..") || file.includes("\\") || file.includes("file://")) {
      errors.push({
        level: "error",
        message: "File path contains unsupported or dangerous path characters.",
        ...base,
      });
    }
  }

  if (entry.asset_type === "slot_module") {
    if (!entry.module_type) {
      errors.push({
        level: "error",
        message: "module_type is required for slot modules.",
        ...base,
      });
    } else {
      const mt = moduleTypesByCode.get(entry.module_type);
      if (!mt) {
        errors.push({
          level: "error",
          message: `Module type "${entry.module_type}" does not exist in the database.`,
          ...base,
        });
      } else if (!mt.is_active) {
        warnings.push({
          level: "warning",
          message: `Module type "${entry.module_type}" is inactive.`,
          ...base,
        });
      }
    }
    if (
      !Number.isInteger(entry.slot_position) ||
      entry.slot_position < 1 ||
      entry.slot_position > entry.gang_count
    ) {
      errors.push({
        level: "error",
        message: `Slot ${entry.slot_position} is invalid for a ${entry.gang_count}-gang asset.`,
        ...base,
      });
    }
  }

  return { errors, warnings };
}

export function validateWorkingManifest(
  rows: EditableManifestEntry[],
  moduleTypes: ModuleTypeOption[],
): ManifestValidationResult {
  const liveRows = rows.filter((row) => row.editState !== "deleted");
  const moduleTypesByCode = new Map(moduleTypes.map((mt) => [mt.code, mt]));
  const errors: ManifestIssue[] = [];
  const warnings: ManifestIssue[] = [];

  const keys = new Map<string, string>();
  for (const row of liveRows) {
    const key = row.manifestKey.trim();
    if (!key) continue;
    if (keys.has(key)) {
      errors.push({
        level: "error",
        message: "Duplicate manifest key.",
        assetKey: key,
        clientId: row.clientId,
      });
    } else {
      keys.set(key, row.clientId);
    }
  }

  const activeIdentities = new Map<string, EditableManifestEntry>();
  const inactiveIdentities = new Map<string, EditableManifestEntry>();

  for (const row of liveRows) {
    const result = validateEntry(row, moduleTypesByCode);
    errors.push(...result.errors);
    warnings.push(...result.warnings);

    const identity = resolverIdentity(row.value);
    if (!identity) continue;
    if (row.value.is_active) {
      const existing = activeIdentities.get(identity);
      if (existing) {
        errors.push({
          level: "error",
          message: `Two active entries resolve to the same assembly requirement (${row.manifestKey} and ${existing.manifestKey}).`,
          assetKey: row.manifestKey,
          clientId: row.clientId,
        });
      } else {
        activeIdentities.set(identity, row);
        if (inactiveIdentities.has(identity)) {
          warnings.push({
            level: "warning",
            message: "An inactive entry duplicates this resolver identity.",
            assetKey: row.manifestKey,
            clientId: row.clientId,
          });
        }
      }
    } else {
      if (activeIdentities.has(identity) || inactiveIdentities.has(identity)) {
        warnings.push({
          level: "warning",
          message: "An inactive entry duplicates another resolver identity.",
          assetKey: row.manifestKey,
          clientId: row.clientId,
        });
      }
      inactiveIdentities.set(identity, row);
    }
  }

  return { ok: errors.length === 0, errors, warnings };
}

export function entryStatusLabel(
  row: EditableManifestEntry,
  validation: ManifestValidationResult,
  missingFiles: Set<string>,
): string {
  if (row.editState === "deleted") return "Deleted";
  const hasError = validation.errors.some(
    (issue) => issue.clientId === row.clientId || issue.assetKey === row.manifestKey,
  );
  if (hasError) return "Error";
  const hasWarning = validation.warnings.some(
    (issue) => issue.clientId === row.clientId || issue.assetKey === row.manifestKey,
  );
  if (missingFiles.has(row.value.file)) return "Missing file";
  if (hasWarning) return "Warning";
  return "Valid";
}
