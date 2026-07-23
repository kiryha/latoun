// Shared types mirroring the backend Pydantic schemas. These describe the
// resolved render state; the frontend never invents asset paths or material
// parameters on its own.

// --------------------------------------------------------------------------- //
// Render materials
// --------------------------------------------------------------------------- //
export interface Material {
  code: string;
  display_name: string;
  base_color: string;
  metalness: number;
  roughness: number;
  anisotropy: number;
  anisotropy_rotation: number;
  normal_texture_path: string | null;
  roughness_texture_path: string | null;
}

export interface MaterialAdmin extends Material {
  is_active: boolean;
}

export interface MaterialCreate {
  code: string;
  display_name: string;
  base_color?: string;
  metalness?: number;
  roughness?: number;
  anisotropy?: number;
  anisotropy_rotation?: number;
  normal_texture_path?: string | null;
  roughness_texture_path?: string | null;
  is_active?: boolean;
}

export type MaterialUpdate = Partial<MaterialCreate>;

// --------------------------------------------------------------------------- //
// Finish schemes
// --------------------------------------------------------------------------- //
export interface FinishScheme {
  finish_scheme_id: number;
  code: string;
  display_name: string;
  description: string | null;
  is_active: boolean;
  is_customer_visible: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FinishSchemeCreate {
  code: string;
  display_name: string;
  description?: string | null;
  is_active?: boolean;
  is_customer_visible?: boolean;
  sort_order?: number;
}

export interface FinishSchemeUpdate {
  display_name?: string;
  description?: string | null;
  is_active?: boolean;
  is_customer_visible?: boolean;
  sort_order?: number;
}

// --------------------------------------------------------------------------- //
// Material assignments
// --------------------------------------------------------------------------- //
export interface MaterialAssignment {
  material_assignment_id: number;
  finish_scheme_id: number;
  finish_scheme_code: string;
  binding_name: string;
  material_code: string;
  material_display_name: string;
}

export interface MaterialAssignmentCreate {
  binding_name: string;
  material_code: string;
}

export interface MaterialAssignmentUpdate {
  binding_name?: string;
  material_code?: string;
}

export interface BulkAssignmentsRequest {
  assignments: MaterialAssignmentCreate[];
}

export interface ResolvedAssignments {
  finish_scheme: { code: string; display_name: string };
  active_sources: string[];
  material_assignments: Record<string, string>;
  materials: Record<string, Material>;
}

// --------------------------------------------------------------------------- //
// Catalog
// --------------------------------------------------------------------------- //
export interface ModuleType {
  module_type_id: number;
  code: string;
  display_name: string;
  is_active?: boolean;
  is_customer_visible?: boolean;
  sort_order?: number;
}

export interface CatalogFinishScheme {
  code: string;
  display_name: string;
  description: string | null;
}

export interface Catalog {
  finish_schemes: CatalogFinishScheme[];
  module_types: ModuleType[];
  gang_counts: number[];
}

// --------------------------------------------------------------------------- //
// Assignment states
// --------------------------------------------------------------------------- //
export interface AssignmentStateModule {
  assignment_state_module_id: number;
  slot_number: number;
  module_type_id: number;
  module_type_code: string;
  module_type_display_name: string;
}

export interface AssignmentStateModuleInput {
  slot_number: number;
  module_type_id: number;
}

export interface AssignmentState {
  assignment_state_id: number;
  assignment_state_code: string;
  display_name: string;
  gang_count: number;
  default_finish_scheme_id: number | null;
  default_finish_scheme_code: string | null;
  notes: string | null;
  is_active: boolean;
  sort_order: number;
  modules: AssignmentStateModule[];
  created_at: string;
  updated_at: string;
}

export interface AssignmentStateCreate {
  display_name: string;
  gang_count: number;
  default_finish_scheme_id?: number | null;
  notes?: string | null;
  is_active?: boolean;
  sort_order?: number;
  modules: AssignmentStateModuleInput[];
}

export interface AssignmentStateUpdate {
  display_name?: string;
  gang_count?: number;
  default_finish_scheme_id?: number | null;
  notes?: string | null;
  is_active?: boolean;
  sort_order?: number;
  modules?: AssignmentStateModuleInput[];
}

// --------------------------------------------------------------------------- //
// Resolved render state
// --------------------------------------------------------------------------- //
export interface ResolvedSlotModule {
  slot_number: number;
  module_type: string;
}

export interface ResolvedAssembly {
  gang_count: number;
  modules: ResolvedSlotModule[];
  finish_scheme: string;
  assignment_state_code: string | null;
  assignment_state_display_name: string | null;
}

export interface ResolvedAsset {
  asset_key: string;
  file: string;
  role?: "plate" | "plate_screws" | "module" | string;
  slot_number?: number | null;
  module_type?: string | null;
}

export interface MissingAssetWarning {
  asset_key: string;
  role: string;
  gang_count: number;
  slot_number?: number | null;
  module_type?: string | null;
  message: string;
}

export interface MissingMaterialReport {
  binding: string;
  contexts: string[];
}

export interface BomLine {
  component_code: string;
  display_name: string;
  quantity: number;
  finish_scheme: string;
}

export interface RenderState {
  is_valid: boolean;
  assets_complete?: boolean;
  assembly: ResolvedAssembly;
  active_sources: string[];
  material_assignments: Record<string, string>;
  materials: Record<string, Material>;
  assets: ResolvedAsset[];
  missing_assets?: MissingAssetWarning[];
  bom: BomLine[];
}

export interface RenderResolveRequest {
  gang_count: number;
  modules: ResolvedSlotModule[];
  finish_scheme: string;
}
