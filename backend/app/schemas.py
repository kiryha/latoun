"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
