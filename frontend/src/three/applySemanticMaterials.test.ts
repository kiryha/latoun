import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { applySemanticMaterials } from "./applySemanticMaterials";

function meshWithBinding(binding: string): THREE.Mesh {
  const material = new THREE.MeshStandardMaterial({ color: "#ffffff" });
  material.name = binding;
  return new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), material);
}

describe("applySemanticMaterials", () => {
  it("applies finish assignments across every mesh", () => {
    const root = new THREE.Group();
    root.add(meshWithBinding("primary_metal"));
    root.add(meshWithBinding("hardware_metal"));
    root.add(meshWithBinding("actuator_metal"));
    root.add(meshWithBinding("electrical_core"));

    const brass = new THREE.MeshStandardMaterial({ color: "#b88a44" });
    const plastic = new THREE.MeshStandardMaterial({ color: "#111111" });
    const materials = new Map<string, THREE.Material>([
      ["brass_brushed", brass],
      ["black_plastic_matte", plastic],
    ]);

    const result = applySemanticMaterials(
      root,
      {
        primary_metal: "brass_brushed",
        hardware_metal: "brass_brushed",
        actuator_metal: "brass_brushed",
        electrical_core: "black_plastic_matte",
      },
      materials,
    );

    expect(result.missingBindings).toEqual([]);
    const applied = root.children.map(
      (child) => (child as THREE.Mesh).material as THREE.Material,
    );
    expect(applied.slice(0, 3).every((material) => material === brass)).toBe(
      true,
    );
    expect(applied[3]).toBe(plastic);
  });

  it("reports missing bindings and uses magenta material", () => {
    const root = new THREE.Group();
    root.add(meshWithBinding("outlet_trim"));
    const materials = new Map<string, THREE.Material>();

    const result = applySemanticMaterials(
      root,
      { primary_metal: "brass_brushed" },
      materials,
    );

    expect(result.missingBindings).toEqual(["outlet_trim"]);
    const applied = (root.children[0] as THREE.Mesh)
      .material as THREE.MeshStandardMaterial;
    expect(applied.color.getHexString()).toBe("ff00ff");
  });

  it("re-applying a new finish updates every previously finished mesh", () => {
    const root = new THREE.Group();
    root.add(meshWithBinding("primary_metal"));
    root.add(meshWithBinding("actuator_metal"));

    const brass = new THREE.MeshStandardMaterial({ color: "#b88a44" });
    const steel = new THREE.MeshStandardMaterial({ color: "#c0c0c0" });
    const materials = new Map<string, THREE.Material>([
      ["brass_brushed", brass],
      ["stainless_steel_brushed", steel],
    ]);

    applySemanticMaterials(
      root,
      {
        primary_metal: "brass_brushed",
        actuator_metal: "brass_brushed",
      },
      materials,
    );
    applySemanticMaterials(
      root,
      {
        primary_metal: "stainless_steel_brushed",
        actuator_metal: "stainless_steel_brushed",
      },
      materials,
    );

    const applied = root.children.map(
      (child) => (child as THREE.Mesh).material as THREE.Material,
    );
    expect(applied.every((material) => material === steel)).toBe(true);
    expect(applied.some((material) => material === brass)).toBe(false);
  });
});
