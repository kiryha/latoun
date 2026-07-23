// Assembly tab: complete production assembly (plate + per-slot devices + finish).
// Public editing uses local UI state only. "Save Current State" (admin) persists
// an Assignment State for the Assignments tab viewport.

import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import { Banner } from "../components/Banner";
import { BomPanel } from "../components/BomPanel";
import { Scene } from "../three/Scene";
import type {
  Catalog,
  MissingMaterialReport,
  RenderState,
} from "../types";
import { isAdminMode } from "./adminMode";
import {
  changeFinishScheme,
  changeGangCount,
  changeSlotModule,
  createDefaultConfiguration,
  isModuleTypeCode,
  toResolvePayload,
  validateConfiguration,
} from "./assemblyConfigurationService";
import { AssemblyAdminActions } from "./AssemblyAdminActions";
import { AssemblySummary } from "./AssemblySummary";
import { AssemblyValidationPanel } from "./AssemblyValidationPanel";
import { buildAssemblyStateName } from "./assemblyStateNameService";
import type {
  AssemblyConfiguration,
  GangCount,
  ModuleTypeCode,
  ModuleTypeOption,
} from "./assemblyTypes";
import { downloadAssemblyJson } from "./exportConfiguration";
import { FinishSelector } from "./FinishSelector";
import { PlateSelector } from "./PlateSelector";
import { SlotDeviceList } from "./SlotDeviceList";

export { buildAssemblyStateName };

export function Configurator() {
  const adminMode = isAdminMode();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [configuration, setConfiguration] = useState<AssemblyConfiguration>(
    () => createDefaultConfiguration(),
  );

  const [renderState, setRenderState] = useState<RenderState | null>(null);
  const [missingMaterials, setMissingMaterials] = useState<
    MissingMaterialReport[]
  >([]);

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
            (scheme) => scheme.code === configuration.finishSchemeCode,
          )
        ) {
          setConfiguration((current) =>
            changeFinishScheme(current, loadedCatalog.finish_schemes[0].code),
          );
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Failed to load catalog from backend.",
        );
      }
    })();
    // Intentionally run once on mount for catalog bootstrap.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setIsResolving(true);
      setError(null);
      setMissingMaterials([]);
      try {
        const resolved = await api.resolveRender(toResolvePayload(configuration));
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
  }, [configuration]);

  const handleMissingMaterials = useCallback(
    (reports: MissingMaterialReport[]) => {
      setMissingMaterials(reports);
    },
    [],
  );

  const moduleOptions = useMemo<ModuleTypeOption[]>(
    () =>
      (catalog?.module_types ?? [])
        .filter((mt) => isModuleTypeCode(mt.code))
        .map((mt) => ({
          code: mt.code as ModuleTypeCode,
          displayName: mt.display_name,
        })),
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
      (item) => item.code === configuration.finishSchemeCode,
    );
    return scheme?.display_name ?? configuration.finishSchemeCode;
  }, [catalog, configuration.finishSchemeCode]);

  const configurationIssues = useMemo(
    () =>
      validateConfiguration(configuration, {
        moduleOptions,
        finishSchemeCodes: finishOptions.map((option) => option.code),
      }),
    [configuration, moduleOptions, finishOptions],
  );

  const missingAssets = renderState?.missing_assets ?? [];

  const handleGangChange = (gangCount: GangCount) => {
    setConfiguration((current) => changeGangCount(current, gangCount));
  };

  const handleSlotChange = (
    slotNumber: number,
    moduleTypeCode: ModuleTypeCode,
  ) => {
    setConfiguration((current) =>
      changeSlotModule(current, slotNumber, moduleTypeCode),
    );
  };

  const handleFinishChange = (finishSchemeCode: string) => {
    setConfiguration((current) =>
      changeFinishScheme(current, finishSchemeCode),
    );
  };

  const handleSaveCurrentState = async () => {
    if (!catalog || configurationIssues.length > 0) return;

    const displayName = buildAssemblyStateName(configuration);
    setIsSavingState(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const finishSchemes = await api.listFinishSchemes();
      const finish = finishSchemes.find(
        (scheme) => scheme.code === configuration.finishSchemeCode,
      );
      if (!finish) {
        throw new Error(
          `Finish scheme “${configuration.finishSchemeCode}” was not found.`,
        );
      }

      const modules = [...configuration.slots]
        .sort((a, b) => a.slotNumber - b.slotNumber)
        .map((slot) => {
          const moduleTypeRow = catalog.module_types.find(
            (item) => item.code === slot.moduleTypeCode,
          );
          if (!moduleTypeRow) {
            throw new Error(
              `Module type “${slot.moduleTypeCode}” was not found.`,
            );
          }
          return {
            slot_number: slot.slotNumber,
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
            gang_count: configuration.gangCount,
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
          gang_count: configuration.gangCount,
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
              onMissingMaterials={handleMissingMaterials}
            />
          ) : (
            <div className="viewport-message">
              {error ? "Assembly unavailable." : "Loading configurator…"}
            </div>
          )}
          {isResolving && (
            <div className="viewport-badge">Resolving assembly…</div>
          )}
          <div className="viewport-alerts">
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
            <AssemblyValidationPanel
              configurationIssues={configurationIssues}
              missingAssets={missingAssets}
              missingMaterials={missingMaterials}
              finishSchemeCode={configuration.finishSchemeCode}
            />
          </div>
        </main>

        <aside className="panel">
          <PlateSelector
            value={configuration.gangCount}
            onChange={handleGangChange}
            disabled={!catalog}
          />

          <SlotDeviceList
            slots={configuration.slots}
            options={moduleOptions}
            onChange={handleSlotChange}
            disabled={!catalog}
          />

          <FinishSelector
            value={configuration.finishSchemeCode}
            options={finishOptions}
            onChange={handleFinishChange}
            disabled={!catalog}
          />

          <AssemblySummary
            configuration={configuration}
            moduleOptions={moduleOptions}
            finishDisplayName={finishDisplayName}
          />

          {adminMode && (
            <AssemblyAdminActions
              canSave={configurationIssues.length === 0}
              canExport
              isSaving={isSavingState}
              onSave={() => void handleSaveCurrentState()}
              onExport={() => downloadAssemblyJson(configuration, renderState)}
            />
          )}
        </aside>
      </div>

      <footer className="app-footer">
        {renderState && <BomPanel bom={renderState.bom} />}
      </footer>
    </>
  );
}
