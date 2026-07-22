// Top-level configurator: owns selection state, talks to the backend, and
// renders the 3D preview, option panel, summary, prototype BOM, and saved list.
//
// The customer-facing selector chooses a FINISH scheme (brass, steel, …). A
// finish scheme resolves multiple render materials per semantic binding.

import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import { Banner } from "../components/Banner";
import { BomPanel } from "../components/BomPanel";
import { SavedConfigurations } from "../components/SavedConfigurations";
import { SegmentedControl } from "../components/SegmentedControl";
import { Scene } from "../three/Scene";
import type {
  Catalog,
  ConfigurationSummary,
  RenderState,
} from "../types";
import { downloadConfigurationJson } from "./exportConfiguration";

const DEFAULT_MODULE_TYPE = "dimmer";
const DEFAULT_FINISH_SCHEME = "brass";
const GANG_COUNT = 1;

export function Configurator() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [moduleType, setModuleType] = useState(DEFAULT_MODULE_TYPE);
  const [finishScheme, setFinishScheme] = useState(DEFAULT_FINISH_SCHEME);

  const [renderState, setRenderState] = useState<RenderState | null>(null);
  const [missingBindings, setMissingBindings] = useState<string[]>([]);
  const [savedConfigurations, setSavedConfigurations] = useState<
    ConfigurationSummary[]
  >([]);
  const [activeConfigCode, setActiveConfigCode] = useState<string | null>(null);
  const [activeConfigId, setActiveConfigId] = useState<number | null>(null);

  const [isResolving, setIsResolving] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const refreshSavedList = useCallback(async () => {
    try {
      const list = await api.listConfigurations();
      setSavedConfigurations(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  // Initial load: catalog + saved configurations.
  useEffect(() => {
    (async () => {
      try {
        const loadedCatalog = await api.getCatalog();
        setCatalog(loadedCatalog);
        // Default to the first customer-visible finish scheme if brass is absent.
        if (
          loadedCatalog.finish_schemes.length > 0 &&
          !loadedCatalog.finish_schemes.some(
            (scheme) => scheme.code === DEFAULT_FINISH_SCHEME,
          )
        ) {
          setFinishScheme(loadedCatalog.finish_schemes[0].code);
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Failed to load catalog from backend.",
        );
      }
      await refreshSavedList();
    })();
  }, [refreshSavedList]);

  // Resolve the configuration whenever the selection changes.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setIsResolving(true);
      setError(null);
      setMissingBindings([]);
      try {
        const resolved = await api.resolveConfiguration({
          gang_count: GANG_COUNT,
          module_type: moduleType,
          finish_scheme: finishScheme,
        });
        if (!cancelled) setRenderState(resolved);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setIsResolving(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [moduleType, finishScheme]);

  const handleSelectModule = (code: string) => {
    setModuleType(code);
    // Selection now differs from any saved record -> treat as a draft.
    setActiveConfigCode(null);
    setActiveConfigId(null);
    setSuccessMessage(null);
  };

  const handleSelectFinish = (code: string) => {
    setFinishScheme(code);
    setActiveConfigCode(null);
    setActiveConfigId(null);
    setSuccessMessage(null);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const saved = await api.saveConfiguration({
        gang_count: GANG_COUNT,
        module_type: moduleType,
        finish_scheme: finishScheme,
      });
      setActiveConfigCode(saved.configuration_code);
      setActiveConfigId(saved.configuration_id);
      setSuccessMessage(`Saved configuration ${saved.configuration_code}.`);
      await refreshSavedList();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoad = async (configurationId: number) => {
    setError(null);
    setSuccessMessage(null);
    try {
      const detail = await api.getConfiguration(configurationId);
      setModuleType(detail.configuration.module_type_code);
      setFinishScheme(detail.configuration.finish_scheme_code);
      setRenderState(detail.render_state);
      setActiveConfigCode(detail.configuration.configuration_code);
      setActiveConfigId(detail.configuration.configuration_id);
      setSuccessMessage(
        `Loaded configuration ${detail.configuration.configuration_code}.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDelete = async (configurationId: number) => {
    const target = savedConfigurations.find(
      (config) => config.configuration_id === configurationId,
    );
    const label = target?.configuration_code ?? `configuration ${configurationId}`;
    if (!window.confirm(`Delete saved configuration ${label}?`)) {
      return;
    }
    setDeletingId(configurationId);
    setError(null);
    setSuccessMessage(null);
    try {
      await api.deleteConfiguration(configurationId);
      if (activeConfigId === configurationId) {
        setActiveConfigCode(null);
        setActiveConfigId(null);
      }
      setSuccessMessage(`Deleted ${label}.`);
      await refreshSavedList();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleExport = () => {
    if (!renderState) return;
    downloadConfigurationJson(renderState, activeConfigCode);
  };

  const handleMissingBindings = useCallback((bindings: string[]) => {
    setMissingBindings(bindings);
  }, []);

  const moduleOptions = useMemo(
    () =>
      catalog?.module_types.map((mt) => ({
        code: mt.code,
        label: mt.display_name,
      })) ?? [],
    [catalog],
  );

  const finishOptions = useMemo(
    () =>
      catalog?.finish_schemes.map((scheme) => ({
        code: scheme.code,
        label: scheme.display_name,
      })) ?? [],
    [catalog],
  );

  const finishDisplayName = useMemo(() => {
    const scheme = catalog?.finish_schemes.find(
      (item) => item.code === finishScheme,
    );
    return scheme?.display_name ?? finishScheme;
  }, [catalog, finishScheme]);

  return (
    <>
      <div className="app-body">
        <main className="viewport">
          {renderState ? (
            <Scene
              renderState={renderState}
              onAssetError={setError}
              onMissingBindings={handleMissingBindings}
            />
          ) : (
            <div className="viewport-message">
              {error ? "Configuration unavailable." : "Loading configurator…"}
            </div>
          )}
          {isResolving && (
            <div className="viewport-badge">Resolving configuration…</div>
          )}
        </main>

        <aside className="panel">
          {error && (
            <Banner kind="error" onDismiss={() => setError(null)}>
              {error}
            </Banner>
          )}
          {successMessage && (
            <Banner kind="success" onDismiss={() => setSuccessMessage(null)}>
              {successMessage}
            </Banner>
          )}
          {missingBindings.length > 0 && (
            <Banner kind="error">
              <strong>Missing material assignment</strong>
              <br />
              Finish scheme: {finishDisplayName}
              <br />
              {missingBindings.length === 1
                ? "Binding: "
                : "Bindings: "}
              {missingBindings.map((b) => (b === "" ? "(empty)" : b)).join(", ")}
              <br />
              No assignment was found in {finishDisplayName} or Init. Affected
              geometry is shown in magenta.
            </Banner>
          )}

          <section className="option-group">
            <label className="option-label">Device</label>
            <SegmentedControl
              options={moduleOptions}
              value={moduleType}
              onChange={handleSelectModule}
              disabled={!catalog}
            />
          </section>

          <section className="option-group">
            <label className="option-label">Finish</label>
            <SegmentedControl
              options={finishOptions}
              value={finishScheme}
              onChange={handleSelectFinish}
              disabled={!catalog}
            />
          </section>

          <section className="summary">
            <h3>Configuration</h3>
            {renderState ? (
              <dl>
                <div>
                  <dt>Code</dt>
                  <dd className="mono">{activeConfigCode ?? "draft (unsaved)"}</dd>
                </div>
                <div>
                  <dt>Gang count</dt>
                  <dd>{renderState.configuration.gang_count}</dd>
                </div>
                <div>
                  <dt>Device</dt>
                  <dd className="capitalize">
                    {renderState.configuration.module_type}
                  </dd>
                </div>
                <div>
                  <dt>Finish</dt>
                  <dd>{finishDisplayName}</dd>
                </div>
              </dl>
            ) : (
              <p className="muted">No resolved configuration.</p>
            )}
          </section>

          <div className="actions">
            <button
              type="button"
              className="button primary"
              onClick={handleSave}
              disabled={isSaving || !renderState}
            >
              {isSaving ? "Saving…" : "Save Configuration"}
            </button>
            <button
              type="button"
              className="button"
              onClick={handleExport}
              disabled={!renderState}
            >
              Export JSON
            </button>
          </div>

          <SavedConfigurations
            configurations={savedConfigurations}
            activeId={activeConfigId}
            onLoad={handleLoad}
            onDelete={handleDelete}
            deletingId={deletingId}
          />
        </aside>
      </div>

      <footer className="app-footer">
        {renderState && <BomPanel bom={renderState.bom} />}
      </footer>
    </>
  );
}
