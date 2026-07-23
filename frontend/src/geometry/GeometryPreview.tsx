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

export interface SemanticMaterialRow {
  meshName: string;
  materialNames: string[];
}

export interface PreviewMetadata {
  objectCount: number;
  meshCount: number;
  semanticMaterials: SemanticMaterialRow[];
  bindings: string[];
  size: { x: number; y: number; z: number } | null;
}

interface GeometryPreviewProps {
  filePath: string | null;
  missingFile?: boolean;
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
    let objectCount = 0;
    let meshCount = 0;
    const semanticMaterials: SemanticMaterialRow[] = [];
    cloned.traverse((object) => {
      objectCount += 1;
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      meshCount += 1;
      const materials = Array.isArray(mesh.material)
        ? mesh.material
        : [mesh.material];
      const materialNames = materials
        .map((material) => material?.name?.trim())
        .filter((name): name is string => !!name);
      semanticMaterials.push({
        meshName: mesh.name || "(unnamed mesh)",
        materialNames,
      });
    });

    const box = new THREE.Box3().setFromObject(cloned);
    const size = new THREE.Vector3();
    const empty = box.isEmpty();
    if (!empty) box.getSize(size);

    onMetadata({
      objectCount,
      meshCount,
      semanticMaterials,
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

export function GeometryPreview({
  filePath,
  missingFile = false,
}: GeometryPreviewProps) {
  const [showGrid, setShowGrid] = useState(true);
  const [showAxes, setShowAxes] = useState(true);
  const [metadata, setMetadata] = useState<PreviewMetadata | null>(null);
  const resetKey = filePath ?? "";

  useEffect(() => {
    setMetadata(null);
  }, [filePath]);

  if (!filePath) {
    return (
      <div className="geometry-preview">
        <div className="geometry-preview-status">No entry selected</div>
      </div>
    );
  }

  if (!filePath.startsWith("/assets/wall_plates/") || !filePath.endsWith(".glb")) {
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
                <PreviewModel filePath={filePath} onMetadata={setMetadata} />
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
      <div className="geometry-preview-meta">
        <div className="geometry-preview-meta-block">
          <h4>Preview</h4>
          <dl>
            <div>
              <dt>File</dt>
              <dd>
                <code>{filePath}</code>
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{metadata ? "GLB loaded" : "Loading GLB"}</dd>
            </div>
            {metadata && (
              <>
                <div>
                  <dt>Objects</dt>
                  <dd>{metadata.objectCount}</dd>
                </div>
                <div>
                  <dt>Meshes</dt>
                  <dd>{metadata.meshCount}</dd>
                </div>
                {metadata.size && (
                  <div>
                    <dt>Bounds</dt>
                    <dd>
                      {metadata.size.x.toFixed(3)} × {metadata.size.y.toFixed(3)} ×{" "}
                      {metadata.size.z.toFixed(3)}
                    </dd>
                  </div>
                )}
              </>
            )}
          </dl>
        </div>
        <div className="geometry-preview-meta-block">
          <h4>Semantic Materials</h4>
          {!metadata ? (
            <p className="muted">Waiting for GLB…</p>
          ) : metadata.semanticMaterials.length === 0 ? (
            <p className="muted">No semantic material names found.</p>
          ) : (
            <table className="geometry-semantic-table">
              <thead>
                <tr>
                  <th scope="col">Mesh</th>
                  <th scope="col">Semantic Material</th>
                </tr>
              </thead>
              <tbody>
                {metadata.semanticMaterials.map((row) => (
                  <tr key={`${row.meshName}-${row.materialNames.join(",")}`}>
                    <td>
                      <code>{row.meshName}</code>
                    </td>
                    <td>
                      {row.materialNames.length === 0
                        ? "—"
                        : row.materialNames.map((name) => (
                            <code key={name}>{name}</code>
                          ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
