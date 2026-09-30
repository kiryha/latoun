// Semantic material application service.
//
// For every mesh in a loaded GLB, the imported material name is treated as a
// semantic binding (strict Option A: no fallback to a render-material code).
// The binding is looked up in the resolved assignments and the referenced
// render material is applied. Missing bindings get a bright magenta error
// material and are reported so the UI can surface a visible warning.
//
// Supports meshes with a single material and meshes with a material array.
//
// The original imported binding is stored on mesh.userData so re-application
// (React Strict Mode, finish-scheme changes) does not read the already-applied
// render material name (e.g. "material.brass_brushed").

import * as THREE from "three";
import { createMissingBindingMaterial } from "./materials";

const SEMANTIC_BINDING_KEY = "latounSemanticBinding";

/**
 * Convert an imported glTF material name into Latoun's semantic binding key.
 *
 * Houdini's glTF 2.0 exporter may preserve the full material-node path (for
 * example, `/mat/primary_metal`) as the glTF material name. Other exporters
 * already emit the leaf name. Binding keys cannot contain path separators, so
 * using the final non-empty segment keeps both forms interoperable.
 */
export function normalizeSemanticBindingName(materialName: string): string {
  const segments = materialName
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .filter((segment) => segment.length > 0);
  return (segments[segments.length - 1] ?? "").toLowerCase();
}

export interface MaterialApplicationResult {
  // Binding names that could not be resolved (empty name is reported as "").
  missingBindings: string[];
}

function bindingStorageKey(slotIndex: number | null): string {
  return slotIndex === null
    ? SEMANTIC_BINDING_KEY
    : `${SEMANTIC_BINDING_KEY}:${slotIndex}`;
}

function readStoredBinding(
  mesh: THREE.Mesh,
  slotIndex: number | null,
): string | null {
  const stored = mesh.userData[bindingStorageKey(slotIndex)];
  return typeof stored === "string" ? stored : null;
}

function rememberBinding(
  mesh: THREE.Mesh,
  slotIndex: number | null,
  bindingName: string,
): void {
  mesh.userData[bindingStorageKey(slotIndex)] = bindingName;
}

function bindingNameFromMaterial(
  mesh: THREE.Mesh,
  originalMaterial: THREE.Material,
  slotIndex: number | null,
): string {
  const stored = readStoredBinding(mesh, slotIndex);
  if (stored !== null) {
    return stored;
  }
  const bindingName = normalizeSemanticBindingName(
    originalMaterial.name ?? "",
  );
  rememberBinding(mesh, slotIndex, bindingName);
  return bindingName;
}

export function applySemanticMaterials(
  assetRoot: THREE.Object3D,
  materialAssignments: Record<string, string>,
  renderMaterialsByCode: Map<string, THREE.Material>,
): MaterialApplicationResult {
  const missingBindings = new Set<string>();

  const resolveOne = (
    mesh: THREE.Mesh,
    originalMaterial: THREE.Material,
    slotIndex: number | null,
  ): THREE.Material => {
    const bindingName = bindingNameFromMaterial(
      mesh,
      originalMaterial,
      slotIndex,
    );
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
      mesh.material = mesh.material.map((material, slotIndex) =>
        resolveOne(mesh, material, slotIndex),
      );
    } else if (mesh.material) {
      mesh.material = resolveOne(mesh, mesh.material, null);
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
    if (Array.isArray(mesh.material)) {
      mesh.material.forEach((material, slotIndex) => {
        names.add(bindingNameFromMaterial(mesh, material, slotIndex));
      });
    } else {
      names.add(bindingNameFromMaterial(mesh, mesh.material, null));
    }
  });
  return Array.from(names).sort();
}
