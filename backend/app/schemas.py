"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Hex color like #RRGGBB (validated on create/update).
HEX_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"
# Stable machine identifier: lowercase letters, digits, underscore, hyphen.
MATERIAL_CODE_PATTERN = r"^[a-z0-9_-]+$"


# --------------------------------------------------------------------------- #
# Catalog
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


# --------------------------------------------------------------------------- #
# Material management (admin CRUD)
# --------------------------------------------------------------------------- #
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
    """Partial update; only provided fields are changed.

    ``code`` may be renamed; references in saved configurations are cascaded.
    """

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


class ModuleTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    display_name: str


class CatalogOut(BaseModel):
    materials: list[MaterialOut]
    module_types: list[ModuleTypeOut]
    gang_counts: list[int]


# --------------------------------------------------------------------------- #
# Configuration request
# --------------------------------------------------------------------------- #
class ConfigurationRequest(BaseModel):
    gang_count: int = Field(default=1, ge=1)
    module_type: str
    material: str


# --------------------------------------------------------------------------- #
# Resolved render state
# --------------------------------------------------------------------------- #
class ResolvedConfiguration(BaseModel):
    gang_count: int
    module_type: str
    material: str


class ResolvedAsset(BaseModel):
    asset_key: str
    file: str
    material_policy: str
    material_code: str


class BomLine(BaseModel):
    component_code: str
    display_name: str
    quantity: int
    material: str


class RenderStateOut(BaseModel):
    is_valid: bool
    configuration: ResolvedConfiguration
    material: MaterialOut
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
    material_code: str
    created_at: datetime
    updated_at: datetime


class ConfigurationDetail(BaseModel):
    configuration: ConfigurationSummary
    render_state: RenderStateOut
