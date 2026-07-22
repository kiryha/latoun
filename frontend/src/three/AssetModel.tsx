// Loads a single GLB asset and applies materials per semantic binding.
//
// Each mesh's imported material name is a semantic binding, resolved through the
// backend-provided assignment map to a shared render material. Missing bindings
// render magenta and are reported upward. Geometry and transforms are preserved
// and the asset is added at the origin (Houdini baked final assembly coords).

import { useEffect, useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import type { ResolvedAsset } from "../types";
import {
  applySemanticMaterials,
  collectBindingNames,
} from "./applySemanticMaterials";

interface AssetModelProps {
  asset: ResolvedAsset;
  materialAssignments: Record<string, string>;
  renderMaterials: Map<string, THREE.Material>;
  onResult: (
    assetKey: string,
    missingBindings: string[],
    discoveredBindings: string[],
  ) => void;
}

export function AssetModel({
  asset,
  materialAssignments,
  renderMaterials,
  onResult,
}: AssetModelProps) {
  // drei caches by URL. We clone so multiple configurations / hot swaps do not
  // mutate the shared cached scene.
  const { scene } = useGLTF(asset.file);
  const clonedScene = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    const discoveredBindings = collectBindingNames(clonedScene);
    const { missingBindings } = applySemanticMaterials(
      clonedScene,
      materialAssignments,
      renderMaterials,
    );
    onResult(asset.asset_key, missingBindings, discoveredBindings);
  }, [clonedScene, materialAssignments, renderMaterials, asset.asset_key, onResult]);

  // Enforce origin placement per the brief; do not add per-asset transforms.
  clonedScene.position.set(0, 0, 0);
  clonedScene.rotation.set(0, 0, 0);
  clonedScene.scale.set(1, 1, 1);

  return <primitive object={clonedScene} />;
}
