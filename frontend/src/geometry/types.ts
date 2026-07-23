// Wall-plate asset manifest types for the Geometry tab.

export type AssetType = "plate" | "hardware" | "slot_module";

export type GangCount = 1 | 2 | 3 | 4;

export type HardwareType = "plate_screws";

export type EntryEditState = "unchanged" | "added" | "modified" | "deleted";

export interface PlateManifestEntry {
  asset_type: "plate";
  gang_count: GangCount;
  file: string;
  is_active: boolean;
}

export interface HardwareManifestEntry {
  asset_type: "hardware";
  hardware_type: HardwareType;
  gang_count: GangCount;
  file: string;
  is_active: boolean;
}

export interface SlotModuleManifestEntry {
  asset_type: "slot_module";
  gang_count: GangCount;
  module_type: string;
  slot_position: number;
  file: string;
  is_active: boolean;
}

export type AssetManifestEntry =
  | PlateManifestEntry
  | HardwareManifestEntry
  | SlotModuleManifestEntry;

export interface AssetManifest {
  parts: Record<string, AssetManifestEntry>;
}

export interface EditableManifestEntry {
  /** Stable client row id (survives key renames). */
  clientId: string;
  manifestKey: string;
  originalManifestKey?: string;
  value: AssetManifestEntry;
  editState: EntryEditState;
}

export interface ManifestIssue {
  level: "error" | "warning";
  message: string;
  assetKey?: string | null;
  clientId?: string | null;
}

export interface ManifestValidationResult {
  ok: boolean;
  errors: ManifestIssue[];
  warnings: ManifestIssue[];
}

export interface AssetManifestGetResponse {
  manifest: AssetManifest;
  revision: string;
}

export interface AssetManifestSaveResponse {
  manifest: AssetManifest;
  revision: string;
  warnings: string[];
  saved: boolean;
}

export interface ModuleTypeOption {
  module_type_id: number;
  code: string;
  display_name: string;
  is_active: boolean;
  is_customer_visible: boolean;
  sort_order: number;
}

export const WALL_PLATES_PREFIX = "/assets/wall_plates/";
export const GANG_COUNTS: GangCount[] = [1, 2, 3, 4];
export const ASSET_TYPE_LABELS: Record<AssetType, string> = {
  plate: "Plate",
  hardware: "Hardware",
  slot_module: "Slot Module",
};
