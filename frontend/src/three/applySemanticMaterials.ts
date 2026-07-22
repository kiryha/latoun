// Semantic material application service.
//
// For every mesh in a loaded GLB, the imported material name is treated as a
// semantic binding (strict Option A: no fallback to a render-material code).
// The binding is looked up in the resolved assignments and the referenced
// render material is applied. Missing bindings get a bright magenta error
// material and are reported so the UI can surface a visible warning.
//
// Supports meshes with a single material and meshes with a material array.

import * as THREE from "three";
import { createMissingBindingMaterial } from "./materials";

export interface MaterialApplicationResult {
  // Binding names that could not be resolved (empty name is reported as "").
  missingBindings: string[];
}

export function applySemanticMaterials(
  assetRoot: THREE.Object3D,
  materialAssignments: Record<string, string>,
  renderMaterialsByCode: Map<string, THREE.Material>,
): MaterialApplicationResult {
  const missingBindings = new Set<string>();

  const resolveOne = (originalMaterial: THREE.Material): THREE.Material => {
    const bindingName = (originalMaterial.name ?? "").trim().toLowerCase();
    const renderMaterialCode = materialAssignments[bindingName];

    if (!renderMaterialCode) {
      missingBindings.add(bindingName);
      return createMissingBindingMaterial(bindingName);
    }

    const resolvedMaterial = renderMaterialsByCode.get(renderMaterialCode);
    if (!resolvedMaterial) {
      missingBindings.add(bindingName);
      return createMissingBindingMaterial(bindingName);
    }

    return resolvedMaterial;
  };

  assetRoot.traverse((sceneObject: THREE.Object3D) => {
    const mesh = sceneObject as THREE.Mesh;
    if (!mesh.isMesh) return;

    if (Array.isArray(mesh.material)) {
      mesh.material = mesh.material.map(resolveOne);
    } else if (mesh.material) {
      mesh.material = resolveOne(mesh.material);
    }

    mesh.castShadow = true;
    mesh.receiveShadow = true;
  });

  return { missingBindings: Array.from(missingBindings).sort() };
}

// Collects the unique imported (semantic binding) material names in a GLB.
// Used for the optional "Bindings Found in Loaded Assembly" discovery panel.
export function collectBindingNames(assetRoot: THREE.Object3D): string[] {
  const names = new Set<string>();
  assetRoot.traverse((sceneObject: THREE.Object3D) => {
    const mesh = sceneObject as THREE.Mesh;
    if (!mesh.isMesh || !mesh.material) return;
    const materials = Array.isArray(mesh.material)
      ? mesh.material
      : [mesh.material];
    for (const material of materials) {
      names.add((material.name ?? "").trim().toLowerCase());
    }
  });
  return Array.from(names).sort();
}
