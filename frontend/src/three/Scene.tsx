// The 3D preview: lit purely by an equirectangular HDRI environment (no
// discrete lights), with explicit ACES Filmic tone mapping, a contact shadow,
// and orbit controls (zoom enabled, pan disabled). The camera auto-frames the
// assembly with <Bounds> so it works regardless of asset scale.

export const HDRI_PATH = "/assets/hdri/historic_cloister_passage_1k.hdr";

import { Component, Suspense, useLayoutEffect, useRef, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import {
  Bounds,
  ContactShadows,
  Environment,
  Html,
  OrbitControls,
} from "@react-three/drei";
import * as THREE from "three";
import type { RenderState } from "../types";
import { AssetModel } from "./AssetModel";

interface SceneProps {
  renderState: RenderState;
  onAssetError: (message: string) => void;
}

interface AssemblyMeasurement {
  groundY: number;
  radius: number;
}

function Assembly({
  renderState,
  onMeasured,
}: {
  renderState: RenderState;
  onMeasured: (measurement: AssemblyMeasurement) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // Re-key the effect on the resolved asset/material set so we re-measure when
  // the device or material changes.
  const signature = `${renderState.configuration.module_type}:${renderState.material.code}`;

  useLayoutEffect(() => {
    if (!groupRef.current) return;
    const box = new THREE.Box3().setFromObject(groupRef.current);
    if (box.isEmpty()) return;
    const size = new THREE.Vector3();
    box.getSize(size);
    const radius = Math.max(size.x, size.y, size.z) * 0.75 || 0.5;
    onMeasured({ groundY: box.min.y, radius });
  }, [signature, onMeasured]);

  return (
    <group ref={groupRef}>
      {renderState.assets.map((asset) => (
        <AssetModel
          key={asset.asset_key}
          asset={asset}
          material={renderState.material}
        />
      ))}
    </group>
  );
}

interface BoundaryProps {
  onError: (message: string) => void;
  children: ReactNode;
}

class R3FErrorBoundary extends Component<BoundaryProps, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    this.props.onError(error.message || "Failed to load geometry.");
  }

  render() {
    if (this.state.hasError) {
      return (
        <Html center>
          <div className="viewport-message viewport-error">
            Could not load geometry. See the error panel for details.
          </div>
        </Html>
      );
    }
    return this.props.children;
  }
}

function LoadingFallback() {
  return (
    <Html center>
      <div className="viewport-message">Loading geometry…</div>
    </Html>
  );
}

export function Scene({ renderState, onAssetError }: SceneProps) {
  const [measurement, setMeasurement] = useState<AssemblyMeasurement>({
    groundY: -0.08,
    radius: 0.25,
  });

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{ position: [0.18, 0.14, 0.32], fov: 50, near: 0.01, far: 100 }}
      gl={{
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.0,
      }}
    >
      <color attach="background" args={["#2b3036"]} />

      <Suspense fallback={<LoadingFallback />}>
        {/* Remounting on config change resets the error boundary cleanly. */}
        <R3FErrorBoundary
          key={`${renderState.configuration.module_type}:${renderState.material.code}`}
          onError={onAssetError}
        >
          {/* Sole light source: the equirectangular HDRI environment. */}
          <Environment files={HDRI_PATH} />
          <Bounds fit clip observe margin={1.3}>
            <Assembly renderState={renderState} onMeasured={setMeasurement} />
          </Bounds>
        </R3FErrorBoundary>
      </Suspense>

      <ContactShadows
        position={[0, measurement.groundY - 0.005, 0]}
        opacity={0.55}
        scale={measurement.radius * 4}
        blur={2.5}
        far={measurement.radius * 2}
      />

      <OrbitControls
        makeDefault
        enablePan={false}
        enableZoom
        minDistance={0.05}
        maxDistance={3}
      />
    </Canvas>
  );
}
