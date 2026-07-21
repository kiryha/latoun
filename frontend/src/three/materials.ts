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
