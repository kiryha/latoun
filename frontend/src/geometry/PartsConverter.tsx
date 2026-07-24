import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { Banner } from "../components/Banner";
import type {
  GeometryConversionResponse,
  GeometryPartsInventory,
} from "./types";

function formatBytes(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function PartsConverter() {
  const [inventory, setInventory] = useState<GeometryPartsInventory | null>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [skipExisting, setSkipExisting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeometryConversionResponse | null>(null);

  const loadInventory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setInventory(await api.getWallPlateParts());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInventory();
  }, [loadInventory]);

  const handleConvert = async () => {
    setConverting(true);
    setError(null);
    setResult(null);
    try {
      const nextResult = await api.convertWallPlateParts(skipExisting);
      setResult(nextResult);
      await loadInventory();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setConverting(false);
    }
  };

  const failedFiles =
    result?.files.filter((file) => !file.success) ?? [];

  return (
    <div className="parts-converter">
      {error && (
        <Banner kind="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}
      {result && result.failed === 0 && (
        <Banner kind="success" onDismiss={() => setResult(null)}>
          {result.total === 0
            ? "No OBJ files were found to convert."
            : `Converted ${result.converted}, skipped ${result.skipped}, failed 0 of ${result.total} parts.`}
        </Banner>
      )}
      {result && result.failed > 0 && (
        <Banner kind="error" onDismiss={() => setResult(null)}>
          {`Converted ${result.converted}, skipped ${result.skipped}, failed ${result.failed} of ${result.total}. ${failedFiles
            .map((file) => `${file.source}: ${file.error ?? "unknown error"}`)
            .join("; ")}`}
        </Banner>
      )}

      <div className="parts-converter-toolbar">
        <button
          type="button"
          className="button primary"
          onClick={() => void handleConvert()}
          disabled={converting || loading || !inventory?.blender_available}
        >
          {converting ? "Converting…" : "Convert Parts"}
        </button>
        <label className="checkbox-row parts-skip-existing">
          <input
            type="checkbox"
            checked={skipExisting}
            onChange={(event) => setSkipExisting(event.target.checked)}
            disabled={converting}
          />
          Skip Existing
        </label>
        <button
          type="button"
          className="button small"
          onClick={() => void loadInventory()}
          disabled={loading || converting}
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {inventory && (
        <div className="parts-paths">
          <div>
            <span>OBJ source</span>
            <code title={inventory.source_directory}>
              {inventory.source_directory}
            </code>
          </div>
          <div>
            <span>GLB output</span>
            <code title={inventory.output_directory}>
              {inventory.output_directory}
            </code>
          </div>
          <div>
            <span>Blender</span>
            <code title={inventory.blender_executable}>
              {inventory.blender_executable}
            </code>
            <strong
              className={
                inventory.blender_available ? "status-valid" : "status-missing"
              }
            >
              {inventory.blender_available ? "Available" : "Missing"}
            </strong>
          </div>
        </div>
      )}

      {loading && !inventory ? (
        <p className="muted parts-loading">Loading parts…</p>
      ) : (
        <div className="parts-table-scroll">
          <table className="parts-table">
            <thead>
              <tr>
                <th>OBJ File</th>
                <th>GLB File</th>
                <th>OBJ Size</th>
                <th>GLB Size</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {inventory?.parts.map((part) => (
                <tr key={part.source}>
                  <td><code>{part.source}</code></td>
                  <td><code>{part.output}</code></td>
                  <td>{formatBytes(part.source_size)}</td>
                  <td>{formatBytes(part.output_size)}</td>
                  <td>
                    <span
                      className={
                        part.glb_exists ? "status-valid" : "status-missing"
                      }
                    >
                      {part.glb_exists ? "Exists" : "Missing"}
                    </span>
                  </td>
                </tr>
              ))}
              {inventory?.parts.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">No OBJ files found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
