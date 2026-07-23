// Assembly tab: live preview of a device + finish scheme.
// "Save Current State" stores the assembly as an Assembly State for the
// Assignments tab viewport.

import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import { Banner } from "../components/Banner";
import { BomPanel } from "../components/BomPanel";
import { SegmentedControl } from "../components/SegmentedControl";
import { Scene } from "../three/Scene";
import type { Catalog, RenderState, ResolvedSlotModule } from "../types";
import { downloadAssemblyJson } from "./exportConfiguration";

const DEFAULT_MODULE_TYPE = "dimmer";
const DEFAULT_FINISH_SCHEME = "brass";
const GANG_COUNT = 1;

/** Build Assembly State display name from slot module type codes. */
export function buildAssignmentStateDisplayName(
  modules: ResolvedSlotModule[],
): string {
  return [...modules]
    .sort((a, b) => a.slot_number - b.slot_number)
    .map((module) => module.module_type)
    .join("-");
}

export function Configurator() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [moduleType, setModuleType] = useState(DEFAULT_MODULE_TYPE);
  const [finishScheme, setFinishScheme] = useState(DEFAULT_FINISH_SCHEME);

  const [renderState, setRenderState] = useState<RenderState | null>(null);
  const [missingBindings, setMissingBindings] = useState<string[]>([]);

  const [isResolving, setIsResolving] = useState(false);
  const [isSavingState, setIsSavingState] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const loadedCatalog = await api.getCatalog();
        setCatalog(loadedCatalog);
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
    })();
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setIsResolving(true);
      setError(null);
      setMissingBindings([]);
      try {
        const resolved = await api.resolveRender({
          gang_count: GANG_COUNT,
          modules: [{ slot_number: 1, module_type: moduleType }],
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

  const moduleDisplayName = useMemo(() => {
    const module = catalog?.module_types.find((item) => item.code === moduleType);
    return module?.display_name ?? moduleType;
  }, [catalog, moduleType]);

  const handleSaveCurrentState = async () => {
    if (!renderState || !catalog) return;

    const displayName = buildAssignmentStateDisplayName(
      renderState.assembly.modules,
    );
    setIsSavingState(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const finishSchemes = await api.listFinishSchemes();
      const finish = finishSchemes.find((scheme) => scheme.code === finishScheme);
      if (!finish) {
        throw new Error(`Finish scheme “${finishScheme}” was not found.`);
      }

      const modules = [...renderState.assembly.modules]
        .sort((a, b) => a.slot_number - b.slot_number)
        .map((slot) => {
          const moduleTypeRow = catalog.module_types.find(
            (item) => item.code === slot.module_type,
          );
          if (!moduleTypeRow) {
            throw new Error(`Module type “${slot.module_type}” was not found.`);
          }
          return {
            slot_number: slot.slot_number,
            module_type_id: moduleTypeRow.module_type_id,
          };
        });

      const existing = (await api.listAssignmentStates()).find(
        (state) => state.display_name === displayName,
      );

      if (existing) {
        const updated = await api.updateAssignmentState(
          existing.assignment_state_id,
          {
            display_name: displayName,
            gang_count: renderState.assembly.gang_count,
            default_finish_scheme_id: finish.finish_scheme_id,
            is_active: true,
            modules,
          },
        );
        setSuccessMessage(
          `Updated assembly state “${updated.display_name}” (${updated.assignment_state_code}).`,
        );
      } else {
        const created = await api.createAssignmentState({
          display_name: displayName,
          gang_count: renderState.assembly.gang_count,
          default_finish_scheme_id: finish.finish_scheme_id,
          is_active: true,
          sort_order: 0,
          modules,
        });
        setSuccessMessage(
          `Saved assembly state “${created.display_name}” (${created.assignment_state_code}).`,
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSavingState(false);
    }
  };

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
              {error ? "Assembly unavailable." : "Loading configurator…"}
            </div>
          )}
          {isResolving && (
            <div className="viewport-badge">Resolving assembly…</div>
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
              {missingBindings.length === 1 ? "Binding: " : "Bindings: "}
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
              onChange={setModuleType}
              disabled={!catalog}
            />
          </section>

          <section className="option-group">
            <label className="option-label">Finish</label>
            <SegmentedControl
              options={finishOptions}
              value={finishScheme}
              onChange={setFinishScheme}
              disabled={!catalog}
            />
          </section>

          <section className="summary">
            <h3>Assembly</h3>
            {renderState ? (
              <dl>
                <div>
                  <dt>Gang count</dt>
                  <dd>{renderState.assembly.gang_count}</dd>
                </div>
                <div>
                  <dt>Device</dt>
                  <dd>{moduleDisplayName}</dd>
                </div>
                <div>
                  <dt>Finish</dt>
                  <dd>{finishDisplayName}</dd>
                </div>
                <div>
                  <dt>State name</dt>
                  <dd className="mono">
                    {buildAssignmentStateDisplayName(renderState.assembly.modules)}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="muted">No resolved assembly.</p>
            )}
          </section>

          <div className="actions">
            <button
              type="button"
              className="button primary"
              onClick={() => void handleSaveCurrentState()}
              disabled={!renderState || isSavingState}
            >
              {isSavingState ? "Saving…" : "Save Current State"}
            </button>
            <button
              type="button"
              className="button"
              onClick={() => {
                if (!renderState) return;
                downloadAssemblyJson(renderState);
              }}
              disabled={!renderState}
            >
              Export JSON
            </button>
          </div>
        </aside>
      </div>

      <footer className="app-footer">
        {renderState && <BomPanel bom={renderState.bom} />}
      </footer>
    </>
  );
}
