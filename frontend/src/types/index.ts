// Shared types mirroring the backend Pydantic schemas. These describe the
// resolved render state; the frontend never invents asset paths or material
// parameters on its own.

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

export interface ModuleType {
  code: string;
  display_name: string;
}

export interface Catalog {
  materials: Material[];
  module_types: ModuleType[];
  gang_counts: number[];
}

export interface ResolvedConfiguration {
  gang_count: number;
  module_type: string;
  material: string;
}

export interface ResolvedAsset {
  asset_key: string;
  file: string;
  material_policy: string;
  material_code: string;
}

export interface BomLine {
  component_code: string;
  display_name: string;
  quantity: number;
  material: string;
}

export interface RenderState {
  is_valid: boolean;
  configuration: ResolvedConfiguration;
  material: Material;
  assets: ResolvedAsset[];
  bom: BomLine[];
}

export interface ConfigurationRequest {
  gang_count: number;
  module_type: string;
  material: string;
}

export interface ConfigurationSummary {
  configuration_id: number;
  configuration_code: string;
  gang_count: number;
  module_type_code: string;
  material_code: string;
  created_at: string;
  updated_at: string;
}

export interface ConfigurationDetail {
  configuration: ConfigurationSummary;
  render_state: RenderState;
}
