// Builds a THREE.MeshPhysicalMaterial from resolved material parameters.
// Parameters come from the backend (SQLite), never hardcoded here.

import * as THREE from "three";
import type { Material } from "../types";

export function createPhysicalMaterial(material: Material): THREE.MeshPhysicalMaterial {
  const physical = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(material.base_color),
    metalness: material.metalness,
    roughness: material.roughness,
  });

  // Anisotropy is available on MeshPhysicalMaterial in recent three versions.
  physical.anisotropy = material.anisotropy;
  physical.anisotropyRotation = material.anisotropy_rotation;
  physical.name = `material.${material.code}`;

  return physical;
}

// Bright magenta error material for a semantic binding that has no assignment.
// Deliberately obvious so missing assignments are never silent.
export function createMissingBindingMaterial(
  bindingName: string,
): THREE.MeshStandardMaterial {
  const missingBindingMaterial = new THREE.MeshStandardMaterial({
    color: 0xff00ff,
    metalness: 0.0,
    roughness: 0.5,
  });
  missingBindingMaterial.name = `missing_binding:${bindingName}`;
  return missingBindingMaterial;
}

// Builds a code -> THREE.Material map from the resolved render materials.
// One material instance per code, shared across meshes that resolve to it.
export function buildRenderMaterialMap(
  materialsByCode: Record<string, Material>,
): Map<string, THREE.Material> {
  const map = new Map<string, THREE.Material>();
  for (const material of Object.values(materialsByCode)) {
    map.set(material.code, createPhysicalMaterial(material));
  }
  return map;
}
