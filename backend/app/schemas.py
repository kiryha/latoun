"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Hex color like #RRGGBB (validated on create/update).
HEX_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"
# Stable machine identifier: lowercase letters, digits, underscore, hyphen.
MATERIAL_CODE_PATTERN = r"^[a-z0-9_-]+$"
# Finish scheme code: same rules as material code.
FINISH_SCHEME_CODE_PATTERN = r"^[a-z0-9_-]+$"
# Semantic binding name: must start with a letter, then letters/digits/underscore.
BINDING_NAME_PATTERN = r"^[a-z][a-z0-9_]*$"


# --------------------------------------------------------------------------- #
# Render materials
# --------------------------------------------------------------------------- #
class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    display_name: str
    base_color: str
    metalness: float
    roughness: float
    anisotropy: float
    anisotropy_rotation: float
    normal_texture_path: str | None = None
    roughness_texture_path: str | None = None


class MaterialAdminOut(MaterialOut):
    """Full material record for the material manager, including status."""

    is_active: bool


class MaterialCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=MATERIAL_CODE_PATTERN)
    display_name: str = Field(min_length=1, max_length=128)
    base_color: str = Field(default="#CCCCCC", pattern=HEX_COLOR_PATTERN)
    metalness: float = Field(default=1.0, ge=0.0, le=1.0)
    roughness: float = Field(default=0.5, ge=0.0, le=1.0)
    anisotropy: float = Field(default=0.0, ge=0.0, le=1.0)
    anisotropy_rotation: float = Field(default=0.0, ge=0.0, le=6.2831853)
    normal_texture_path: str | None = Field(default=None, max_length=256)
    roughness_texture_path: str | None = Field(default=None, max_length=256)
    is_active: bool = True


class MaterialUpdate(BaseModel):
    """Partial update; only provided fields are changed. ``code`` may be renamed."""

    code: str | None = Field(
        default=None, min_length=1, max_length=64, pattern=MATERIAL_CODE_PATTERN
    )
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    base_color: str | None = Field(default=None, pattern=HEX_COLOR_PATTERN)
    metalness: float | None = Field(default=None, ge=0.0, le=1.0)
    roughness: float | None = Field(default=None, ge=0.0, le=1.0)
    anisotropy: float | None = Field(default=None, ge=0.0, le=1.0)
    anisotropy_rotation: float | None = Field(default=None, ge=0.0, le=6.2831853)
    normal_texture_path: str | None = Field(default=None, max_length=256)
    roughness_texture_path: str | None = Field(default=None, max_length=256)
    is_active: bool | None = None


class MaterialUsageOut(BaseModel):
    """One assignment that references a material (used in delete-block messages)."""

    finish_scheme_code: str
    finish_scheme_display_name: str
    binding_name: str


# --------------------------------------------------------------------------- #
# Finish schemes
# --------------------------------------------------------------------------- #
class FinishSchemeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finish_scheme_id: int
    code: str
    display_name: str
    description: str | None = None
    is_active: bool
    is_customer_visible: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FinishSchemeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=FINISH_SCHEME_CODE_PATTERN)
    display_name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    is_active: bool = True
    is_customer_visible: bool = True
    sort_order: int = 0


class FinishSchemeUpdate(BaseModel):
    """Partial update. ``code`` is read-only after creation and is not accepted."""

    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    is_active: bool | None = None
    is_customer_visible: bool | None = None
    sort_order: int | None = None


# --------------------------------------------------------------------------- #
# Material assignments
# --------------------------------------------------------------------------- #
class MaterialAssignmentOut(BaseModel):
    material_assignment_id: int
    finish_scheme_id: int
    finish_scheme_code: str
    binding_name: str
    material_code: str
    material_display_name: str


class MaterialAssignmentCreate(BaseModel):
    binding_name: str = Field(min_length=1, max_length=64)
    material_code: str = Field(min_length=1, max_length=64)


class MaterialAssignmentUpdate(BaseModel):
    binding_name: str | None = Field(default=None, min_length=1, max_length=64)
    material_code: str | None = Field(default=None, min_length=1, max_length=64)


class BulkAssignmentItem(BaseModel):
    binding_name: str = Field(min_length=1, max_length=64)
    material_code: str = Field(min_length=1, max_length=64)


class BulkAssignmentsRequest(BaseModel):
    assignments: list[BulkAssignmentItem]


# --------------------------------------------------------------------------- #
# Resolved assignments (for a customer finish scheme)
# --------------------------------------------------------------------------- #
class FinishSchemeRef(BaseModel):
    code: str
    display_name: str


class ResolvedAssignmentsOut(BaseModel):
    finish_scheme: FinishSchemeRef
    active_sources: list[str]
    material_assignments: dict[str, str]
    materials: dict[str, MaterialOut]


# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #
class ModuleTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    module_type_id: int
    code: str
    display_name: str
    is_active: bool = True
    is_customer_visible: bool = True
    sort_order: int = 0


# --------------------------------------------------------------------------- #
# Wall-plate asset manifest (Geometry tab)
# --------------------------------------------------------------------------- #
class AssetManifestProperties(BaseModel):
    """Shared manifest-level data. ``glb_folder`` is the public URL prefix
    (relative) that every entry's bare ``file`` name is resolved against."""

    glb_folder: str = "/assets/wall_plates/"


class AssetManifestDocument(BaseModel):
    properties: AssetManifestProperties = Field(
        default_factory=AssetManifestProperties
    )
    parts: dict[str, dict]


class AssetManifestGetOut(BaseModel):
    manifest: AssetManifestDocument
    revision: str


class AssetManifestSaveRequest(BaseModel):
    manifest: AssetManifestDocument
    expected_revision: str | None = None


class AssetManifestSaveOut(BaseModel):
    manifest: AssetManifestDocument
    revision: str
    warnings: list[str] = Field(default_factory=list)
    saved: bool = True


class AssetManifestValidateRequest(BaseModel):
    manifest: AssetManifestDocument


class ManifestIssueOut(BaseModel):
    level: str
    message: str
    asset_key: str | None = None


class AssetManifestValidateOut(BaseModel):
    ok: bool
    errors: list[ManifestIssueOut] = Field(default_factory=list)
    warnings: list[ManifestIssueOut] = Field(default_factory=list)


class AssetFileStatusOut(BaseModel):
    files: dict[str, bool]


class CatalogFinishScheme(BaseModel):
    """Customer-visible finish choice shown in the Assembly tab."""

    code: str
    display_name: str
    description: str | None = None


class CatalogOut(BaseModel):
    finish_schemes: list[CatalogFinishScheme]
    module_types: list[ModuleTypeOut]
    gang_counts: list[int]


# --------------------------------------------------------------------------- #
# Assignment states (admin viewport assemblies)
# --------------------------------------------------------------------------- #
class AssignmentStateModuleIn(BaseModel):
    slot_number: int = Field(ge=1)
    module_type_id: int


class AssignmentStateModuleOut(BaseModel):
    assignment_state_module_id: int
    slot_number: int
    module_type_id: int
    module_type_code: str
    module_type_display_name: str


class AssignmentStateCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    gang_count: int = Field(ge=1)
    default_finish_scheme_id: int | None = None
    notes: str | None = Field(default=None, max_length=2048)
    is_active: bool = True
    sort_order: int = 0
    modules: list[AssignmentStateModuleIn]


class AssignmentStateUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    gang_count: int | None = Field(default=None, ge=1)
    default_finish_scheme_id: int | None = None
    notes: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = None
    sort_order: int | None = None
    modules: list[AssignmentStateModuleIn] | None = None


class AssignmentStateOut(BaseModel):
    assignment_state_id: int
    assignment_state_code: str
    display_name: str
    gang_count: int
    default_finish_scheme_id: int | None
    default_finish_scheme_code: str | None
    notes: str | None
    is_active: bool
    sort_order: int
    modules: list[AssignmentStateModuleOut]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Render resolve
# --------------------------------------------------------------------------- #
class RenderSlotModule(BaseModel):
    slot_number: int = Field(ge=1)
    module_type: str


class RenderResolveRequest(BaseModel):
    """Ad-hoc assembly resolve for the Assembly tab (geometry + finish)."""

    gang_count: int = Field(default=1, ge=1)
    modules: list[RenderSlotModule]
    finish_scheme: str


class ResolvedSlotModule(BaseModel):
    slot_number: int
    module_type: str


class ResolvedAssembly(BaseModel):
    gang_count: int
    modules: list[ResolvedSlotModule]
    finish_scheme: str
    assignment_state_code: str | None = None
    assignment_state_display_name: str | None = None


class ResolvedAsset(BaseModel):
    """A geometry file to load. Materials are resolved per semantic binding,
    not per asset, so no material fields live here anymore."""

    asset_key: str
    file: str
    role: str = "module"
    slot_number: int | None = None
    module_type: str | None = None


class MissingAssetWarning(BaseModel):
    """Registered-or-expected geometry that could not be resolved."""

    asset_key: str
    role: str
    gang_count: int
    slot_number: int | None = None
    module_type: str | None = None
    message: str


class BomLine(BaseModel):
    component_code: str
    display_name: str
    quantity: int
    finish_scheme: str


class RenderStateOut(BaseModel):
    is_valid: bool
    assets_complete: bool = True
    assembly: ResolvedAssembly
    active_sources: list[str]
    # binding_name -> render material code
    material_assignments: dict[str, str]
    # render material code -> full material definition
    materials: dict[str, MaterialOut]
    assets: list[ResolvedAsset]
    missing_assets: list[MissingAssetWarning] = Field(default_factory=list)
    bom: list[BomLine]
