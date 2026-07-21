// Loads a single GLB asset and applies the resolved material using the
// "replace_all" policy: every mesh material is replaced with the shared
// resolved material. Geometry and transforms are preserved and the asset is
// added at the origin (Houdini already baked final assembly coordinates).

import { useEffect, useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import type { Material, ResolvedAsset } from "../types";
import { createPhysicalMaterial } from "./materials";

interface AssetModelProps {
  asset: ResolvedAsset;
  material: Material;
}

export function AssetModel({ asset, material }: AssetModelProps) {
  // drei caches by URL. We clone so multiple configurations / hot swaps do not
  // mutate the shared cached scene.
  const { scene } = useGLTF(asset.file);

  const clonedScene = useMemo(() => scene.clone(true), [scene]);

  // Create the resolved material once per material change and dispose it when
  // it is replaced or the component unmounts, to avoid GPU memory leaks.
  const resolvedMaterial = useMemo(
    () => createPhysicalMaterial(material),
    [material],
  );

  useEffect(() => {
    return () => {
      resolvedMaterial.dispose();
    };
  }, [resolvedMaterial]);

  useEffect(() => {
    if (asset.material_policy !== "replace_all") return;
    clonedScene.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (mesh.isMesh) {
        mesh.material = resolvedMaterial;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
      }
    });
  }, [clonedScene, resolvedMaterial, asset.material_policy]);

  // Enforce origin placement per the brief; do not add per-asset transforms.
  clonedScene.position.set(0, 0, 0);
  clonedScene.rotation.set(0, 0, 0);
  clonedScene.scale.set(1, 1, 1);

  return <primitive object={clonedScene} />;
}
