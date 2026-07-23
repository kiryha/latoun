// The 3D preview: lit purely by an equirectangular HDRI environment (no
// discrete lights), with explicit ACES Filmic tone mapping, a contact shadow,
// and orbit controls (zoom enabled, pan disabled). The camera auto-frames the
// assembly with <Bounds> so it works regardless of asset scale.
//
// Materials are applied per semantic binding using the resolved assignment map
// and render-material definitions from the backend.

export const HDRI_PATH = "/hdri/historic_cloister_passage_1k.hdr";

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
import type { MissingMaterialReport, RenderState } from "../types";
import { AssetModel } from "./AssetModel";
import {
  describeAssetContext,
  placeholderOffsetX,
} from "./assetContext";
import { buildRenderMaterialMap } from "./materials";
import { MissingModulePlaceholder } from "./MissingModulePlaceholder";

interface SceneProps {
  renderState: RenderState;
  onAssetError: (message: string) => void;
  // Reports missing bindings with asset/slot context for the validation panel.
  onMissingMaterials?: (reports: MissingMaterialReport[]) => void;
  // Reports the union of all imported binding names across all loaded assets.
  onDiscoveredBindings?: (discoveredBindings: string[]) => void;
}

interface AssemblyMeasurement {
  groundY: number;
  radius: number;
}

function slotGroupName(slotNumber: number): string {
  return `Slot_${String(slotNumber).padStart(2, "0")}`;
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

  // Geometry signature excludes finish so finish changes do not remount GLBs.
  const geometrySignature = `${renderState.assembly.gang_count}:${renderState.assembly.modules
    .map((module) => `${module.slot_number}:${module.module_type}`)
    .join(",")}`;

  useLayoutEffect(() => {
    if (!groupRef.current) return;
    const box = new THREE.Box3().setFromObject(groupRef.current);
    if (box.isEmpty()) return;
    const size = new THREE.Vector3();
    box.getSize(size);
    const radius = Math.max(size.x, size.y, size.z) * 0.75 || 0.5;
    onMeasured({ groundY: box.min.y, radius });
  }, [geometrySignature, onMeasured]);

  const plate = renderState.assets.find((asset) => asset.role === "plate");
  const screws = renderState.assets.find(
    (asset) => asset.role === "plate_screws",
  );
  const modules = renderState.assets.filter((asset) => asset.role === "module");
  const missingAssets = renderState.missing_assets ?? [];
  const missingPlate = missingAssets.some((asset) => asset.role === "plate");
  const missingModules = missingAssets.filter(
    (asset) => asset.role === "module" && asset.slot_number != null,
  );
  const plateWidth = 0.08 + renderState.assembly.gang_count * 0.05;

  return (
    <group ref={groupRef} name="AssemblyRoot">
      {plate && (
        <group name="Plate">
          <AssetModel
            key={plate.asset_key}
            asset={plate}
            materialAssignments={renderState.material_assignments}
            renderMaterials={renderMaterials}
            onResult={onResult}
          />
        </group>
      )}

      {missingPlate && (
        <mesh name="PlatePlaceholder">
          <boxGeometry args={[plateWidth, 0.1, 0.012]} />
          <meshStandardMaterial color="#5c636b" roughness={0.9} metalness={0.05} />
        </mesh>
      )}

      {screws && (
        <group name="PlateScrews">
          <AssetModel
            key={screws.asset_key}
            asset={screws}
            materialAssignments={renderState.material_assignments}
            renderMaterials={renderMaterials}
            onResult={onResult}
          />
        </group>
      )}

      {modules.map((asset) => {
        const slotNumber = asset.slot_number ?? 0;
        return (
          <group key={asset.asset_key} name={slotGroupName(slotNumber)}>
            <AssetModel
              asset={asset}
              materialAssignments={renderState.material_assignments}
              renderMaterials={renderMaterials}
              onResult={onResult}
            />
          </group>
        );
      })}

      {missingModules.map((warning) => {
        const slotNumber = warning.slot_number ?? 1;
        return (
          <MissingModulePlaceholder
            key={warning.asset_key}
            slotNumber={slotNumber}
            moduleType={warning.module_type ?? "module"}
            offsetX={placeholderOffsetX(
              slotNumber,
              renderState.assembly.gang_count,
            )}
          />
        );
      })}
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
  onMissingMaterials,
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

  const contextByAsset = useMemo(() => {
    const map = new Map<string, string>();
    for (const asset of renderState.assets) {
      map.set(asset.asset_key, describeAssetContext(asset));
    }
    return map;
  }, [renderState.assets]);

  // Aggregate per-asset binding results into contextual material reports.
  const missingByAsset = useRef<Record<string, string[]>>({});
  const discoveredByAsset = useRef<Record<string, string[]>>({});
  const geometryEpoch = `${renderState.assembly.gang_count}:${renderState.assembly.modules
    .map((module) => `${module.slot_number}:${module.module_type}`)
    .join(",")}`;
  const resultEpochRef = useRef(geometryEpoch);
  if (resultEpochRef.current !== geometryEpoch) {
    resultEpochRef.current = geometryEpoch;
    missingByAsset.current = {};
    discoveredByAsset.current = {};
  }

  const handleResult = useCallback(
    (assetKey: string, missing: string[], discovered: string[]) => {
      missingByAsset.current[assetKey] = missing;
      discoveredByAsset.current[assetKey] = discovered;

      const assetKeys = renderState.assets.map((asset) => asset.asset_key);
      if (onMissingMaterials) {
        const byBinding = new Map<string, Set<string>>();
        for (const key of assetKeys) {
          const context = contextByAsset.get(key) ?? key;
          for (const binding of missingByAsset.current[key] ?? []) {
            const contexts = byBinding.get(binding) ?? new Set<string>();
            contexts.add(context);
            byBinding.set(binding, contexts);
          }
        }
        const reports: MissingMaterialReport[] = Array.from(byBinding.entries())
          .map(([binding, contexts]) => ({
            binding,
            contexts: Array.from(contexts).sort(),
          }))
          .sort((a, b) => a.binding.localeCompare(b.binding));
        onMissingMaterials(reports);
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
    [
      renderState.assets,
      contextByAsset,
      onMissingMaterials,
      onDiscoveredBindings,
    ],
  );

  // Remount error boundary on gang/module geometry changes only — not finish.
  const boundaryKey = geometryEpoch;

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
        <R3FErrorBoundary key={boundaryKey} onError={onAssetError}>
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
