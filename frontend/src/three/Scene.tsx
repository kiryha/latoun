// The 3D preview: lit purely by an equirectangular HDRI environment (no
// discrete lights), with explicit ACES Filmic tone mapping, a contact shadow,
// and orbit controls (zoom enabled, pan disabled). The camera auto-frames the
// assembly with <Bounds> so it works regardless of asset scale.
//
// Materials are applied per semantic binding using the resolved assignment map
// and render-material definitions from the backend.

export const HDRI_PATH = "/assets/hdri/historic_cloister_passage_1k.hdr";

import {
  Component,
  Suspense,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
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
import { buildRenderMaterialMap } from "./materials";

interface SceneProps {
  renderState: RenderState;
  onAssetError: (message: string) => void;
  // Reports the union of unresolved semantic bindings across all loaded assets.
  onMissingBindings?: (missingBindings: string[]) => void;
  // Reports the union of all imported binding names across all loaded assets.
  onDiscoveredBindings?: (discoveredBindings: string[]) => void;
}

interface AssemblyMeasurement {
  groundY: number;
  radius: number;
}

function Assembly({
  renderState,
  renderMaterials,
  onResult,
  onMeasured,
}: {
  renderState: RenderState;
  renderMaterials: Map<string, THREE.Material>;
  onResult: (
    assetKey: string,
    missingBindings: string[],
    discoveredBindings: string[],
  ) => void;
  onMeasured: (measurement: AssemblyMeasurement) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // Re-key the effect on the resolved asset/finish set so we re-measure when
  // the device or finish changes.
  const signature = `${renderState.configuration.module_type}:${renderState.configuration.finish_scheme}`;

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
          materialAssignments={renderState.material_assignments}
          renderMaterials={renderMaterials}
          onResult={onResult}
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

export function Scene({
  renderState,
  onAssetError,
  onMissingBindings,
  onDiscoveredBindings,
}: SceneProps) {
  const [measurement, setMeasurement] = useState<AssemblyMeasurement>({
    groundY: -0.08,
    radius: 0.25,
  });

  // One THREE.Material instance per render-material code, shared across meshes.
  // Rebuilt and disposed when the resolved materials change.
  const renderMaterials = useMemo(
    () => buildRenderMaterialMap(renderState.materials),
    [renderState.materials],
  );

  useEffect(() => {
    return () => {
      renderMaterials.forEach((material) => material.dispose());
    };
  }, [renderMaterials]);

  // Aggregate per-asset binding results into unions over the current asset set.
  const missingByAsset = useRef<Record<string, string[]>>({});
  const discoveredByAsset = useRef<Record<string, string[]>>({});
  const resultEpoch = `${renderState.configuration.module_type}:${renderState.configuration.finish_scheme}`;
  const resultEpochRef = useRef(resultEpoch);
  if (resultEpochRef.current !== resultEpoch) {
    resultEpochRef.current = resultEpoch;
    missingByAsset.current = {};
    discoveredByAsset.current = {};
  }

  const handleResult = useCallback(
    (assetKey: string, missing: string[], discovered: string[]) => {
      missingByAsset.current[assetKey] = missing;
      discoveredByAsset.current[assetKey] = discovered;

      const assetKeys = renderState.assets.map((asset) => asset.asset_key);
      if (onMissingBindings) {
        const union = Array.from(
          new Set(assetKeys.flatMap((key) => missingByAsset.current[key] ?? [])),
        ).sort();
        onMissingBindings(union);
      }
      if (onDiscoveredBindings) {
        const union = Array.from(
          new Set(
            assetKeys.flatMap((key) => discoveredByAsset.current[key] ?? []),
          ),
        ).sort();
        onDiscoveredBindings(union);
      }
    },
    [renderState.assets, onMissingBindings, onDiscoveredBindings],
  );

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
          key={`${renderState.configuration.module_type}:${renderState.configuration.finish_scheme}`}
          onError={onAssetError}
        >
          {/* Sole light source: the equirectangular HDRI environment. */}
          <Environment files={HDRI_PATH} />
          <Bounds fit clip observe margin={1.3}>
            <Assembly
              renderState={renderState}
              renderMaterials={renderMaterials}
              onResult={handleResult}
              onMeasured={setMeasurement}
            />
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
