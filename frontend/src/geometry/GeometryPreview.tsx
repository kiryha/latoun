// Isolated GLB preview for a single manifest entry (Geometry tab).

import { Component, Suspense, useEffect, useMemo, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import {
  Bounds,
  Environment,
  Grid,
  Html,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import * as THREE from "three";
import { HDRI_PATH } from "../three/Scene";
import { collectBindingNames } from "../three/applySemanticMaterials";

export interface SceneObjectRow {
  /** Stable unique id for React keys (Three.js uuid). */
  objectId: string;
  objectName: string;
  objectType: string;
  materialNames: string[];
}

export interface PreviewMetadata {
  sceneObjects: SceneObjectRow[];
  bindings: string[];
  size: { x: number; y: number; z: number } | null;
}

interface GeometryPreviewProps {
  filePath: string | null;
  missingFile?: boolean;
  onMetadata?: (meta: PreviewMetadata | null) => void;
}

class PreviewErrorBoundary extends Component<
  { children: ReactNode; resetKey: string },
  { error: string | null }
> {
  state = { error: null as string | null };

  static getDerivedStateFromError(error: Error) {
    return { error: error.message || "Failed to load GLB." };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    // Keep the Geometry editor usable when a preview fails.
  }

  componentDidUpdate(prevProps: { resetKey: string }) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="geometry-preview-status is-error">
          GLB parse error: {this.state.error}
        </div>
      );
    }
    return this.props.children;
  }
}

function PreviewModel({
  filePath,
  onMetadata,
}: {
  filePath: string;
  onMetadata: (meta: PreviewMetadata) => void;
}) {
  const { scene } = useGLTF(filePath);
  const cloned = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    const sceneObjects: SceneObjectRow[] = [];
    cloned.traverse((object) => {
      // Skip the glTF Scene root group; list authored objects only.
      if (object === cloned) return;

      const mesh = object as THREE.Mesh;
      const materialNames: string[] = [];
      if (mesh.isMesh) {
        const materials = Array.isArray(mesh.material)
          ? mesh.material
          : [mesh.material];
        for (const [slotIndex, material] of materials.entries()) {
          const name = material?.name?.trim();
          // One row-cell entry per material slot so multi-material meshes
          // surface every assignment.
          materialNames.push(
            name && name.length > 0 ? name : `(unnamed slot ${slotIndex})`,
          );
        }
      }

      sceneObjects.push({
        objectId: object.uuid,
        objectName: object.name?.trim() || `(unnamed ${object.type})`,
        objectType: object.type,
        materialNames,
      });
    });

    const box = new THREE.Box3().setFromObject(cloned);
    const size = new THREE.Vector3();
    const empty = box.isEmpty();
    if (!empty) box.getSize(size);

    onMetadata({
      sceneObjects,
      bindings: collectBindingNames(cloned),
      size: empty ? null : { x: size.x, y: size.y, z: size.z },
    });
  }, [cloned, onMetadata]);

  cloned.position.set(0, 0, 0);
  cloned.rotation.set(0, 0, 0);
  cloned.scale.set(1, 1, 1);

  return <primitive object={cloned} />;
}

function PreviewFallback() {
  return (
    <Html center>
      <div className="viewport-message">Loading GLB…</div>
    </Html>
  );
}

/** Viewport-only preview. Scene data / semantic materials live in the editor scroll. */
export function GeometryPreview({
  filePath,
  missingFile = false,
  onMetadata,
}: GeometryPreviewProps) {
  const [showGrid, setShowGrid] = useState(true);
  const [showAxes, setShowAxes] = useState(true);
  const resetKey = filePath ?? "";

  useEffect(() => {
    onMetadata?.(null);
  }, [filePath, onMetadata]);

  if (!filePath) {
    return (
      <div className="geometry-preview">
        <div className="geometry-preview-status">No entry selected</div>
      </div>
    );
  }

  if (!filePath.startsWith("/") || !filePath.endsWith(".glb")) {
    return (
      <div className="geometry-preview">
        <div className="geometry-preview-status is-warning">Invalid path</div>
      </div>
    );
  }

  if (missingFile) {
    return (
      <div className="geometry-preview">
        <div className="geometry-preview-status is-warning">
          <p>GLB file not found</p>
          <code>{filePath}</code>
          <p className="muted">
            The manifest entry may still be saved because geometry can be added
            later.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="geometry-preview">
      <div className="geometry-preview-toolbar">
        <button
          type="button"
          className="button small"
          onClick={() => setShowGrid((value) => !value)}
        >
          {showGrid ? "Hide grid" : "Show grid"}
        </button>
        <button
          type="button"
          className="button small"
          onClick={() => setShowAxes((value) => !value)}
        >
          {showAxes ? "Hide axes" : "Show axes"}
        </button>
      </div>
      <div className="geometry-preview-canvas">
        <PreviewErrorBoundary resetKey={resetKey}>
          <Canvas
            dpr={[1, 2]}
            camera={{ position: [0.35, 0.25, 0.55], fov: 45, near: 0.01, far: 100 }}
            gl={{
              antialias: true,
              toneMapping: THREE.ACESFilmicToneMapping,
              toneMappingExposure: 1.0,
            }}
          >
            <color attach="background" args={["#2b3036"]} />
            <Suspense fallback={<PreviewFallback />}>
              <Environment files={HDRI_PATH} />
              <Bounds fit clip observe margin={1.35}>
                <PreviewModel
                  filePath={filePath}
                  onMetadata={(meta) => onMetadata?.(meta)}
                />
              </Bounds>
              {showGrid && (
                <Grid
                  infiniteGrid
                  fadeDistance={4}
                  sectionColor="#4a515a"
                  cellColor="#343a41"
                />
              )}
              {showAxes && <axesHelper args={[0.2]} />}
            </Suspense>
            <OrbitControls makeDefault enablePan />
          </Canvas>
        </PreviewErrorBoundary>
      </div>
    </div>
  );
}

export function SemanticMaterialsPanel({
  metadata,
  filePath,
}: {
  metadata: PreviewMetadata | null;
  filePath: string | null;
}) {
  return (
    <div className="geometry-preview-meta-block">
      <h4>Scene Data</h4>
      {!filePath ? (
        <p className="muted">Select an entry to inspect materials.</p>
      ) : !metadata ? (
        <p className="muted">Waiting for GLB…</p>
      ) : metadata.sceneObjects.length === 0 ? (
        <p className="muted">No scene objects found.</p>
      ) : (
        <table className="geometry-semantic-table">
          <thead>
            <tr>
              <th scope="col">Object</th>
              <th scope="col">Material</th>
            </tr>
          </thead>
          <tbody>
            {metadata.sceneObjects.map((row) => (
              <tr key={row.objectId}>
                <td>
                  <code>{row.objectName}</code>
                  <span className="geometry-object-type">{row.objectType}</span>
                </td>
                <td>
                  {row.materialNames.length === 0
                    ? "—"
                    : row.materialNames.map((name, index) => (
                        <code key={`${row.objectId}-${index}`}>{name}</code>
                      ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {metadata?.size && filePath && (
        <dl className="geometry-preview-stats">
          <div>
            <dt>Scene Boundary</dt>
            <dd>
              {metadata.size.x.toFixed(3)} × {metadata.size.y.toFixed(3)} ×{" "}
              {metadata.size.z.toFixed(3)}
            </dd>
          </div>
        </dl>
      )}
    </div>
  );
}
