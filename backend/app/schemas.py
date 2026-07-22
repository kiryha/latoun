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

    code: str
    display_name: str


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
# Configuration request
# --------------------------------------------------------------------------- #
class ConfigurationRequest(BaseModel):
    gang_count: int = Field(default=1, ge=1)
    module_type: str
    finish_scheme: str


# --------------------------------------------------------------------------- #
# Resolved render state
# --------------------------------------------------------------------------- #
class ResolvedConfiguration(BaseModel):
    gang_count: int
    module_type: str
    finish_scheme: str


class ResolvedAsset(BaseModel):
    """A geometry file to load. Materials are resolved per semantic binding,
    not per asset, so no material fields live here anymore."""

    asset_key: str
    file: str


class BomLine(BaseModel):
    component_code: str
    display_name: str
    quantity: int
    finish_scheme: str


class RenderStateOut(BaseModel):
    is_valid: bool
    configuration: ResolvedConfiguration
    active_sources: list[str]
    # binding_name -> render material code
    material_assignments: dict[str, str]
    # render material code -> full material definition
    materials: dict[str, MaterialOut]
    assets: list[ResolvedAsset]
    bom: list[BomLine]


# --------------------------------------------------------------------------- #
# Saved configurations
# --------------------------------------------------------------------------- #
class ConfigurationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    configuration_id: int
    configuration_code: str
    gang_count: int
    module_type_code: str
    finish_scheme_code: str
    created_at: datetime
    updated_at: datetime


class ConfigurationDetail(BaseModel):
    configuration: ConfigurationSummary
    render_state: RenderStateOut
