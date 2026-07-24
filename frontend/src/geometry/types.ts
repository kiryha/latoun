// Wall-plate asset manifest types for the Geometry tab.

export type AssetCategory = "plate" | "hardware" | "slot_module";

export type GangCount = 1 | 2 | 3 | 4;

export type HardwareType = "plate_screws";

export type EntryEditState = "unchanged" | "added" | "modified" | "deleted";

export interface PlateManifestEntry {
  category: "plate";
  gang_count: GangCount;
  file: string;
  is_active: boolean;
}

export interface HardwareManifestEntry {
  category: "hardware";
  hardware_type: HardwareType;
  gang_count: GangCount;
  file: string;
  is_active: boolean;
}

export interface SlotModuleManifestEntry {
  category: "slot_module";
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

export interface AssetManifestProperties {
  /** Public URL prefix (relative) that each entry's bare `file` resolves against. */
  glb_folder: string;
}

export interface AssetManifest {
  properties: AssetManifestProperties;
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

export interface GeometryConversionFile {
  source: string;
  output: string;
  success: boolean;
  skipped: boolean;
  error: string | null;
}

export interface GeometryConversionResponse {
  total: number;
  converted: number;
  skipped: number;
  failed: number;
  files: GeometryConversionFile[];
}

export interface GeometryPartFile {
  source: string;
  output: string;
  glb_exists: boolean;
  source_size: number;
  output_size: number | null;
}

export interface GeometryPartsInventory {
  source_directory: string;
  output_directory: string;
  blender_executable: string;
  blender_available: boolean;
  parts: GeometryPartFile[];
}

/** Default public URL folder for GLBs (overridable via manifest properties.glb_folder). */
export const DEFAULT_GLB_FOLDER = "/assets/wall_plates/";
/** Back-compat alias. */
export const WALL_PLATES_PREFIX = DEFAULT_GLB_FOLDER;
export const GANG_COUNTS: GangCount[] = [1, 2, 3, 4];
export const CATEGORY_LABELS: Record<AssetCategory, string> = {
  plate: "Plate",
  hardware: "Hardware",
  slot_module: "Slot Module",
};
