// Live look-dev preview for the material manager: the edited material applied
// to the shared "material hero" model, lit by the same equirectangular HDRI and
// tone mapping as the main Assembly scene so the look matches 1:1.

import { Suspense, useEffect, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import {
  Bounds,
  Environment,
  Html,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import * as THREE from "three";
import type { Material } from "../types";
import { createPhysicalMaterial } from "../three/materials";
import { HDRI_PATH } from "../three/Scene";

const HERO_PATH = "/geo/material_hero.glb";

function PreviewModel({ material }: { material: Material }) {
  const { scene } = useGLTF(HERO_PATH);

  // Clone so the cached GLB is never mutated across material swaps.
  const clonedScene = useMemo(() => scene.clone(true), [scene]);

  const previewMaterial = useMemo(
    () => createPhysicalMaterial(material),
    [material],
  );

  useEffect(() => {
    return () => {
      previewMaterial.dispose();
    };
  }, [previewMaterial]);

  useEffect(() => {
    clonedScene.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (mesh.isMesh) {
        mesh.material = previewMaterial;
      }
    });
  }, [clonedScene, previewMaterial]);

  return <primitive object={clonedScene} />;
}

function PreviewFallback() {
  return (
    <Html center>
      <div className="viewport-message">Loading preview…</div>
    </Html>
  );
}

export function MaterialPreview({ material }: { material: Material }) {
  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [0, 0.35, 2.4], fov: 45, near: 0.01, far: 100 }}
      gl={{
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.0,
      }}
    >
      <color attach="background" args={["#2b3036"]} />
      <Suspense fallback={<PreviewFallback />}>
        <Environment files={HDRI_PATH} />
        {/* Auto-frame regardless of the model's authored scale. */}
        <Bounds fit clip observe margin={1.2}>
          <PreviewModel material={material} />
        </Bounds>
      </Suspense>
      <OrbitControls makeDefault enablePan />
    </Canvas>
  );
}

useGLTF.preload(HERO_PATH);
