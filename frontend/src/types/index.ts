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

// Full material record used by the material manager (includes status).
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

// All fields optional for a partial update; `code` may be renamed.
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

// `code` is read-only after creation, so it is not part of the update payload.
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
  code: string;
  display_name: string;
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
// Resolved render state
// --------------------------------------------------------------------------- //
export interface ResolvedConfiguration {
  gang_count: number;
  module_type: string;
  finish_scheme: string;
}

export interface ResolvedAsset {
  asset_key: string;
  file: string;
}

export interface BomLine {
  component_code: string;
  display_name: string;
  quantity: number;
  finish_scheme: string;
}

export interface RenderState {
  is_valid: boolean;
  configuration: ResolvedConfiguration;
  active_sources: string[];
  // binding name -> render material code
  material_assignments: Record<string, string>;
  // render material code -> full material definition
  materials: Record<string, Material>;
  assets: ResolvedAsset[];
  bom: BomLine[];
}

export interface ConfigurationRequest {
  gang_count: number;
  module_type: string;
  finish_scheme: string;
}

export interface ConfigurationSummary {
  configuration_id: number;
  configuration_code: string;
  gang_count: number;
  module_type_code: string;
  finish_scheme_code: string;
  created_at: string;
  updated_at: string;
}

export interface ConfigurationDetail {
  configuration: ConfigurationSummary;
  render_state: RenderState;
}
