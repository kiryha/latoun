// Internal Assignments admin: finish schemes, semantic binding rows, and a
// live preview. With no assembly state selected, the material hero is shown.
// Selecting an Assembly State loads assembly geometry; materials always come
// from the finish scheme being edited.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { Banner } from "../components/Banner";
import { MaterialPreview } from "../materials/MaterialPreview";
import { Scene } from "../three/Scene";
import type {
  AssignmentState,
  FinishScheme,
  FinishSchemeCreate,
  MaterialAdmin,
  MaterialAssignment,
  RenderState,
} from "../types";
import { normalizeBindingName, validateBindingName } from "./bindingNames";

const INIT_SCHEME_CODE = "init";

interface AssignmentDraft {
  clientKey: string;
  material_assignment_id: number | null;
  binding_name: string;
  material_code: string;
}

const NEW_SCHEME_DRAFT: FinishSchemeCreate = {
  code: "",
  display_name: "",
  description: "",
  is_active: true,
  is_customer_visible: true,
  sort_order: 40,
};

function toAssignmentDrafts(rows: MaterialAssignment[]): AssignmentDraft[] {
  return rows.map((row) => ({
    clientKey: `id-${row.material_assignment_id}`,
    material_assignment_id: row.material_assignment_id,
    binding_name: row.binding_name,
    material_code: row.material_code,
  }));
}

function sanitizeSchemeCode(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "");
}

function newClientKey(): string {
  return `new-${crypto.randomUUID()}`;
}

type BindingResolution = "current" | "init" | "missing";

export function AssignmentsManager() {
  const [schemes, setSchemes] = useState<FinishScheme[]>([]);
  const [materials, setMaterials] = useState<MaterialAdmin[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [schemeDraft, setSchemeDraft] = useState<FinishScheme | FinishSchemeCreate | null>(
    null,
  );
  const [isNewScheme, setIsNewScheme] = useState(false);
  const [assignmentDrafts, setAssignmentDrafts] = useState<AssignmentDraft[]>([]);
  const [savedAssignments, setSavedAssignments] = useState<AssignmentDraft[]>([]);

  const [resolvedPreview, setResolvedPreview] = useState<RenderState | null>(null);
  const [discoveredBindings, setDiscoveredBindings] = useState<string[]>([]);
  const [missingBindings, setMissingBindings] = useState<string[]>([]);
  const [assignmentStates, setAssignmentStates] = useState<AssignmentState[]>([]);
  const [previewAssignmentStateId, setPreviewAssignmentStateId] = useState<
    number | null
  >(null);

  const [loading, setLoading] = useState(true);
  const [savingScheme, setSavingScheme] = useState(false);
  const [savingAssignments, setSavingAssignments] = useState(false);
  const [resolvingPreview, setResolvingPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const selectedScheme = useMemo(
    () => schemes.find((scheme) => scheme.finish_scheme_id === selectedId) ?? null,
    [schemes, selectedId],
  );

  const activeMaterials = useMemo(
    () => materials.filter((material) => material.is_active),
    [materials],
  );

  const loadSchemes = useCallback(async (selectAfterId?: number) => {
    setLoading(true);
    try {
      const [schemeList, materialList, stateList] = await Promise.all([
        api.listFinishSchemes(),
        api.listMaterials(),
        api.listAssignmentStates({ isActive: true }),
      ]);
      setSchemes(schemeList);
      setMaterials(materialList);
      setAssignmentStates(stateList);

      const target =
        (selectAfterId !== undefined &&
          schemeList.find((scheme) => scheme.finish_scheme_id === selectAfterId)) ||
        schemeList.find((scheme) => scheme.code === "brass") ||
        schemeList[0] ||
        null;

      if (target) {
        setSelectedId(target.finish_scheme_id);
        setSchemeDraft({ ...target });
        setIsNewScheme(false);
        const rows = await api.listAssignments(target.finish_scheme_id);
        const drafts = toAssignmentDrafts(rows);
        setAssignmentDrafts(drafts);
        setSavedAssignments(drafts);
      } else {
        setSelectedId(null);
        setSchemeDraft(null);
        setAssignmentDrafts([]);
        setSavedAssignments([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSchemes();
  }, [loadSchemes]);

  const handleSelect = async (finishSchemeId: number) => {
    const scheme = schemes.find((item) => item.finish_scheme_id === finishSchemeId);
    if (!scheme) return;
    setSelectedId(finishSchemeId);
    setSchemeDraft({ ...scheme });
    setIsNewScheme(false);
    setError(null);
    setSuccess(null);
    setDiscoveredBindings([]);
    setMissingBindings([]);
    try {
      const rows = await api.listAssignments(finishSchemeId);
      const drafts = toAssignmentDrafts(rows);
      setAssignmentDrafts(drafts);
      setSavedAssignments(drafts);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleNewScheme = () => {
    setSelectedId(null);
    setSchemeDraft({ ...NEW_SCHEME_DRAFT });
    setIsNewScheme(true);
    setAssignmentDrafts([]);
    setSavedAssignments([]);
    setResolvedPreview(null);
    setDiscoveredBindings([]);
    setMissingBindings([]);
    setError(null);
    setSuccess(null);
  };

  const setSchemeField = <K extends keyof FinishSchemeCreate>(
    key: K,
    value: FinishSchemeCreate[K],
  ) => {
    setSchemeDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const schemeIsDirty = useMemo(() => {
    if (isNewScheme) return true;
    if (!schemeDraft || !selectedScheme) return false;
    return (
      schemeDraft.display_name !== selectedScheme.display_name ||
      (schemeDraft.description ?? "") !== (selectedScheme.description ?? "") ||
      schemeDraft.is_active !== selectedScheme.is_active ||
      schemeDraft.is_customer_visible !== selectedScheme.is_customer_visible ||
      schemeDraft.sort_order !== selectedScheme.sort_order
    );
  }, [isNewScheme, schemeDraft, selectedScheme]);

  const assignmentsAreDirty = useMemo(() => {
    if (isNewScheme) return false;
    return JSON.stringify(assignmentDrafts) !== JSON.stringify(savedAssignments);
  }, [assignmentDrafts, savedAssignments, isNewScheme]);

  const handleSaveScheme = async () => {
    if (!schemeDraft) return;
    setSavingScheme(true);
    setError(null);
    setSuccess(null);
    try {
      if (isNewScheme) {
        const created = await api.createFinishScheme({
          code: schemeDraft.code,
          display_name: schemeDraft.display_name,
          description: schemeDraft.description || null,
          is_active: schemeDraft.is_active,
          is_customer_visible: schemeDraft.is_customer_visible,
          sort_order: schemeDraft.sort_order,
        });
        setSuccess(`Created finish scheme “${created.display_name}”.`);
        await loadSchemes(created.finish_scheme_id);
      } else if (selectedId) {
        const updated = await api.updateFinishScheme(selectedId, {
          display_name: schemeDraft.display_name,
          description: schemeDraft.description || null,
          is_active: schemeDraft.is_active,
          is_customer_visible: schemeDraft.is_customer_visible,
          sort_order: schemeDraft.sort_order,
        });
        setSuccess(`Saved finish scheme “${updated.display_name}”.`);
        await loadSchemes(updated.finish_scheme_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingScheme(false);
    }
  };

  const handleDeleteScheme = async () => {
    if (!selectedScheme || isNewScheme) return;
    if (selectedScheme.code === INIT_SCHEME_CODE) {
      setError(
        "The init scheme holds static assignments shared by all configurations and cannot be deleted.",
      );
      return;
    }
    if (
      !window.confirm(
        `Delete finish scheme “${selectedScheme.display_name}” (${selectedScheme.code})? Its assignments will also be deleted.`,
      )
    ) {
      return;
    }
    setSavingScheme(true);
    setError(null);
    setSuccess(null);
    try {
      await api.deleteFinishScheme(selectedScheme.finish_scheme_id);
      setSuccess(`Deleted finish scheme ${selectedScheme.code}.`);
      await loadSchemes();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingScheme(false);
    }
  };

  const handleAddAssignment = () => {
    const defaultMaterial = activeMaterials[0]?.code ?? "";
    setAssignmentDrafts((prev) => [
      ...prev,
      {
        clientKey: newClientKey(),
        material_assignment_id: null,
        binding_name: "",
        material_code: defaultMaterial,
      },
    ]);
  };

  const handleRemoveAssignment = (clientKey: string) => {
    setAssignmentDrafts((prev) => prev.filter((row) => row.clientKey !== clientKey));
  };

  const updateAssignment = (
    clientKey: string,
    patch: Partial<Pick<AssignmentDraft, "binding_name" | "material_code">>,
  ) => {
    setAssignmentDrafts((prev) =>
      prev.map((row) => (row.clientKey === clientKey ? { ...row, ...patch } : row)),
    );
  };

  const handleSaveAssignments = async () => {
    if (!selectedId || isNewScheme) return;

    const normalizedRows: AssignmentDraft[] = [];
    const seenBindings = new Set<string>();
    for (const row of assignmentDrafts) {
      const validationError = validateBindingName(row.binding_name);
      if (validationError) {
        setError(validationError);
        return;
      }
      const bindingName = normalizeBindingName(row.binding_name);
      if (seenBindings.has(bindingName)) {
        setError(`Duplicate binding “${bindingName}” in this finish scheme.`);
        return;
      }
      if (!row.material_code) {
        setError(`Choose a render material for binding “${bindingName}”.`);
        return;
      }
      seenBindings.add(bindingName);
      normalizedRows.push({ ...row, binding_name: bindingName });
    }

    setSavingAssignments(true);
    setError(null);
    setSuccess(null);
    try {
      const saved = await api.bulkSaveAssignments(selectedId, {
        assignments: normalizedRows.map((row) => ({
          binding_name: row.binding_name,
          material_code: row.material_code,
        })),
      });
      const drafts = toAssignmentDrafts(saved);
      setAssignmentDrafts(drafts);
      setSavedAssignments(drafts);
      setSuccess("Saved semantic assignments.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingAssignments(false);
    }
  };

  const handleLoadPreviewAssignmentState = (assignmentStateId: number | null) => {
    setPreviewAssignmentStateId(assignmentStateId);
    if (assignmentStateId === null) {
      setResolvedPreview(null);
      setDiscoveredBindings([]);
      setMissingBindings([]);
    }
  };

  // Hero material for the "None" preview: prefer primary_metal, else first row.
  const heroMaterial = useMemo(() => {
    const preferredBinding = assignmentDrafts.find(
      (row) => normalizeBindingName(row.binding_name) === "primary_metal",
    );
    const fallbackRow = preferredBinding ?? assignmentDrafts[0] ?? null;
    const materialCode = fallbackRow?.material_code;
    if (!materialCode) {
      return activeMaterials[0] ?? materials[0] ?? null;
    }
    return (
      materials.find((material) => material.code === materialCode) ??
      activeMaterials[0] ??
      null
    );
  }, [assignmentDrafts, materials, activeMaterials]);

  // Assembly preview: geometry from Assembly State; materials from the
  // finish scheme currently being edited.
  useEffect(() => {
    if (isNewScheme || !selectedScheme || previewAssignmentStateId === null) {
      setResolvedPreview(null);
      setResolvingPreview(false);
      return;
    }
    if (!selectedScheme.is_active) {
      setResolvedPreview(null);
      setResolvingPreview(false);
      return;
    }

    let cancelled = false;
    (async () => {
      setResolvingPreview(true);
      try {
        const resolved = await api.resolveAssignmentStateRender(
          previewAssignmentStateId,
          selectedScheme.code,
        );
        if (!cancelled) {
          setResolvedPreview(resolved);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setResolvedPreview(null);
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setResolvingPreview(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    selectedScheme,
    isNewScheme,
    savedAssignments,
    previewAssignmentStateId,
  ]);

  const bindingStatus = useMemo(() => {
    if (!resolvedPreview) return new Map<string, BindingResolution>();
    const schemeCode = selectedScheme?.code;
    const resolvedMap = resolvedPreview.material_assignments;
    const status = new Map<string, BindingResolution>();
    for (const binding of discoveredBindings) {
      if (!(binding in resolvedMap)) {
        status.set(binding, "missing");
        continue;
      }
      const assignedLocally = assignmentDrafts.some(
        (row) => normalizeBindingName(row.binding_name) === binding,
      );
      if (schemeCode === INIT_SCHEME_CODE || assignedLocally) {
        status.set(binding, "current");
      } else {
        status.set(binding, "init");
      }
    }
    return status;
  }, [
    discoveredBindings,
    resolvedPreview,
    selectedScheme,
    assignmentDrafts,
  ]);

  const canSaveScheme =
    !!schemeDraft &&
    !savingScheme &&
    schemeIsDirty &&
    schemeDraft.display_name.trim().length > 0 &&
    (isNewScheme ? /^[a-z0-9_-]+$/.test(schemeDraft.code) : true);

  const canSaveAssignments =
    !isNewScheme &&
    !!selectedId &&
    !savingAssignments &&
    assignmentsAreDirty;

  return (
    <div className="materials-manager assignments-manager">
      <aside className="materials-list">
        <div className="materials-list-header">
          <h3>Finish Schemes</h3>
          <button type="button" className="button small" onClick={handleNewScheme}>
            + New
          </button>
        </div>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <ul>
            {schemes.map((scheme) => (
              <li
                key={scheme.finish_scheme_id}
                className={
                  scheme.finish_scheme_id === selectedId ? "is-active" : ""
                }
              >
                <button
                  type="button"
                  onClick={() => void handleSelect(scheme.finish_scheme_id)}
                >
                  <span className="scheme-status">
                    {scheme.code === INIT_SCHEME_CODE
                      ? "I"
                      : scheme.is_customer_visible
                        ? "C"
                        : "H"}
                  </span>
                  <span className="material-name">
                    {scheme.display_name}
                    {!scheme.is_active && (
                      <em className="material-flag"> · inactive</em>
                    )}
                    {scheme.code === INIT_SCHEME_CODE && (
                      <em className="material-flag"> · internal</em>
                    )}
                  </span>
                  <span className="mono material-code">{scheme.code}</span>
                </button>
              </li>
            ))}
            {isNewScheme && (
              <li className="is-active is-draft">
                <button type="button" disabled>
                  <span className="scheme-status">+</span>
                  <span className="material-name">
                    {schemeDraft && "display_name" in schemeDraft
                      ? schemeDraft.display_name || "New finish scheme"
                      : "New finish scheme"}
                    <em className="material-flag"> · unsaved</em>
                  </span>
                </button>
              </li>
            )}
          </ul>
        )}
      </aside>

      <section className="material-editor">
        {error && (
          <Banner kind="error" onDismiss={() => setError(null)}>
            {error}
          </Banner>
        )}
        {success && (
          <Banner kind="success" onDismiss={() => setSuccess(null)}>
            {success}
          </Banner>
        )}

        {schemeDraft ? (
          <>
            <div className="option-group">
              <label className="option-label" htmlFor="scheme-code">
                Code
              </label>
              <input
                id="scheme-code"
                className="text-input mono"
                value={schemeDraft.code}
                placeholder="e.g. copper"
                readOnly={!isNewScheme}
                onChange={(event) =>
                  setSchemeField("code", sanitizeSchemeCode(event.target.value))
                }
              />
              {!isNewScheme && (
                <p className="field-hint">
                  Code is a stable identifier and cannot be changed after creation.
                </p>
              )}
              {selectedScheme?.code === INIT_SCHEME_CODE && (
                <p className="field-hint">
                  Internal · Static assignments · Not customer visible
                </p>
              )}
            </div>

            <div className="option-group">
              <label className="option-label" htmlFor="scheme-name">
                Display name
              </label>
              <input
                id="scheme-name"
                className="text-input"
                value={schemeDraft.display_name}
                placeholder="e.g. Copper"
                onChange={(event) =>
                  setSchemeField("display_name", event.target.value)
                }
              />
            </div>

            <div className="option-group">
              <label className="option-label" htmlFor="scheme-description">
                Description
              </label>
              <textarea
                id="scheme-description"
                className="text-input"
                rows={3}
                value={schemeDraft.description ?? ""}
                onChange={(event) =>
                  setSchemeField("description", event.target.value)
                }
              />
            </div>

            <div className="option-group">
              <label className="option-label" htmlFor="scheme-sort">
                Sort order
              </label>
              <input
                id="scheme-sort"
                className="text-input mono"
                type="number"
                value={schemeDraft.sort_order}
                onChange={(event) =>
                  setSchemeField("sort_order", Number(event.target.value) || 0)
                }
              />
            </div>

            <div className="option-group">
              <label className="checkbox-field">
                <input
                  type="checkbox"
                  checked={schemeDraft.is_active}
                  onChange={(event) =>
                    setSchemeField("is_active", event.target.checked)
                  }
                />
                Active
              </label>
            </div>

            <div className="option-group">
              <label className="checkbox-field">
                <input
                  type="checkbox"
                  checked={schemeDraft.is_customer_visible}
                  disabled={
                    !isNewScheme && selectedScheme?.code === INIT_SCHEME_CODE
                  }
                  onChange={(event) =>
                    setSchemeField("is_customer_visible", event.target.checked)
                  }
                />
                Customer visible
              </label>
            </div>

            <div className="actions actions-row">
              <button
                type="button"
                className="button primary"
                onClick={() => void handleSaveScheme()}
                disabled={!canSaveScheme}
              >
                {savingScheme
                  ? "Saving…"
                  : isNewScheme
                    ? "Create Finish Scheme"
                    : "Save Scheme"}
              </button>
              {!isNewScheme && selectedScheme?.code !== INIT_SCHEME_CODE && (
                <button
                  type="button"
                  className="button danger"
                  onClick={() => void handleDeleteScheme()}
                  disabled={savingScheme}
                >
                  Delete
                </button>
              )}
            </div>

            {!isNewScheme && (
              <>
                <hr className="section-divider" />

                <div className="assignments-header">
                  <h3>Semantic Assignments</h3>
                  <button
                    type="button"
                    className="button small"
                    onClick={handleAddAssignment}
                  >
                    + Add Assignment
                  </button>
                </div>
                <p className="field-hint">
                  Maps finish scheme + binding name → render material.
                </p>

                <table className="assignments-table">
                  <thead>
                    <tr>
                      <th>Semantic binding</th>
                      <th>Render material</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {assignmentDrafts.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="muted">
                          No assignments yet.
                        </td>
                      </tr>
                    ) : (
                      assignmentDrafts.map((row) => (
                        <tr key={row.clientKey}>
                          <td>
                            <input
                              className="text-input mono"
                              value={row.binding_name}
                              placeholder="primary_metal"
                              onChange={(event) =>
                                updateAssignment(row.clientKey, {
                                  binding_name: event.target.value,
                                })
                              }
                              onBlur={(event) =>
                                updateAssignment(row.clientKey, {
                                  binding_name: normalizeBindingName(
                                    event.target.value,
                                  ),
                                })
                              }
                            />
                          </td>
                          <td>
                            <select
                              className="text-input"
                              value={row.material_code}
                              onChange={(event) =>
                                updateAssignment(row.clientKey, {
                                  material_code: event.target.value,
                                })
                              }
                            >
                              {activeMaterials.length === 0 && (
                                <option value="">No active materials</option>
                              )}
                              {activeMaterials.map((material) => (
                                <option key={material.code} value={material.code}>
                                  {material.display_name}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="button small danger"
                              onClick={() => handleRemoveAssignment(row.clientKey)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                <div className="actions actions-row">
                  <button
                    type="button"
                    className="button primary"
                    onClick={() => void handleSaveAssignments()}
                    disabled={!canSaveAssignments}
                  >
                    {savingAssignments ? "Saving…" : "Save Assignments"}
                  </button>
                </div>

                {discoveredBindings.length > 0 && (
                  <>
                    <hr className="section-divider" />
                    <h3>Bindings Found in Loaded Assembly</h3>
                    <table className="assignments-table discovery-table">
                      <thead>
                        <tr>
                          <th>Binding</th>
                          <th>Resolution</th>
                          <th>Material</th>
                        </tr>
                      </thead>
                      <tbody>
                        {discoveredBindings.map((binding) => {
                          const resolution = bindingStatus.get(binding) ?? "missing";
                          const materialCode =
                            resolvedPreview?.material_assignments[binding] ?? "—";
                          return (
                            <tr key={binding}>
                              <td className="mono">{binding || "(empty)"}</td>
                              <td>
                                {resolution === "current"
                                  ? "Current scheme"
                                  : resolution === "init"
                                    ? "Init"
                                    : "Missing"}
                              </td>
                              <td className="mono">{materialCode}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </>
                )}

                {missingBindings.length > 0 && (
                  <Banner kind="error">
                    Missing assignments for:{" "}
                    {missingBindings
                      .map((binding) => (binding === "" ? "(empty)" : binding))
                      .join(", ")}
                    . Affected geometry is shown in magenta.
                  </Banner>
                )}
              </>
            )}
          </>
        ) : (
          !loading && <p className="muted">No finish scheme selected.</p>
        )}
      </section>

      <section className="material-preview">
        {!isNewScheme && selectedScheme && (
          <div className="preview-toolbar">
            <div className="preview-toolbar-row">
              <label className="option-label" htmlFor="preview-assignment-state">
                Assembly State
              </label>
              <select
                id="preview-assignment-state"
                className="text-input"
                value={previewAssignmentStateId ?? ""}
                onChange={(event) => {
                  const value = event.target.value;
                  handleLoadPreviewAssignmentState(
                    value ? Number(value) : null,
                  );
                }}
              >
                <option value="">None</option>
                {assignmentStates.map((state) => (
                  <option
                    key={state.assignment_state_id}
                    value={state.assignment_state_id}
                  >
                    {state.display_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        <div className="preview-viewport">
          {isNewScheme ? (
            <div className="viewport-message">
              Create the finish scheme before previewing assignments.
            </div>
          ) : selectedScheme && !selectedScheme.is_active ? (
            <div className="viewport-message">
              Activate this finish scheme to preview with the assembly resolver.
            </div>
          ) : previewAssignmentStateId === null ? (
            heroMaterial ? (
              <MaterialPreview material={heroMaterial} />
            ) : (
              <div className="viewport-message">
                Add an assignment to preview a material.
              </div>
            )
          ) : resolvedPreview ? (
            <>
              <Scene
                renderState={resolvedPreview}
                onAssetError={setError}
                onMissingBindings={setMissingBindings}
                onDiscoveredBindings={setDiscoveredBindings}
              />
              {resolvingPreview && (
                <div className="viewport-badge">Refreshing preview…</div>
              )}
            </>
          ) : (
            <div className="viewport-message">
              {resolvingPreview
                ? "Resolving preview…"
                : "Select an active finish scheme to preview."}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
