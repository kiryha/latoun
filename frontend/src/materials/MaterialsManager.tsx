// Material manager: master-detail UI to list, create, rename, delete materials
// and adjust their MeshPhysicalMaterial parameters, with a live 3D preview.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { Banner } from "../components/Banner";
import type { MaterialAdmin } from "../types";
import { MaterialPreview } from "./MaterialPreview";

const TWO_PI = Math.PI * 2;

// Keep the code valid as the user types: lowercase, spaces -> underscores, and
// strip anything outside [a-z0-9_-].
function sanitizeCode(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "");
}

const NEW_MATERIAL_DRAFT: MaterialAdmin = {
  code: "",
  display_name: "",
  base_color: "#CCCCCC",
  metalness: 1,
  roughness: 0.5,
  anisotropy: 0,
  anisotropy_rotation: 0,
  normal_texture_path: null,
  roughness_texture_path: null,
  is_active: true,
};

export function MaterialsManager() {
  const [materials, setMaterials] = useState<MaterialAdmin[]>([]);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [draft, setDraft] = useState<MaterialAdmin | null>(null);
  const [isNew, setIsNew] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadMaterials = useCallback(async (selectAfter?: string) => {
    setLoading(true);
    try {
      const list = await api.listMaterials();
      setMaterials(list);
      const target =
        selectAfter && list.find((m) => m.code === selectAfter)
          ? list.find((m) => m.code === selectAfter)!
          : list[0] ?? null;
      if (target) {
        setSelectedCode(target.code);
        setDraft({ ...target });
        setIsNew(false);
      } else {
        setSelectedCode(null);
        setDraft(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMaterials();
  }, [loadMaterials]);

  const original = useMemo(
    () => materials.find((m) => m.code === selectedCode) ?? null,
    [materials, selectedCode],
  );

  const isDirty = useMemo(() => {
    if (isNew) return true;
    if (!draft || !original) return false;
    return JSON.stringify(draft) !== JSON.stringify(original);
  }, [draft, original, isNew]);

  const handleSelect = (code: string) => {
    const material = materials.find((m) => m.code === code);
    if (!material) return;
    setSelectedCode(code);
    setDraft({ ...material });
    setIsNew(false);
    setError(null);
    setSuccess(null);
  };

  const handleNew = () => {
    setSelectedCode(null);
    setDraft({ ...NEW_MATERIAL_DRAFT });
    setIsNew(true);
    setError(null);
    setSuccess(null);
  };

  const setField = <K extends keyof MaterialAdmin>(
    key: K,
    value: MaterialAdmin[K],
  ) => {
    setDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const handleSave = async () => {
    if (!draft) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      if (isNew) {
        const created = await api.createMaterial(draft);
        setSuccess(`Created material “${created.display_name}”.`);
        await loadMaterials(created.code);
      } else if (selectedCode) {
        // The URL keeps the original code; the body may carry a renamed code.
        const updated = await api.updateMaterial(selectedCode, draft);
        setSuccess(`Saved material “${updated.display_name}”.`);
        await loadMaterials(updated.code);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!draft || isNew) return;
    if (!window.confirm(`Delete material “${draft.display_name}” (${draft.code})?`))
      return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.deleteMaterial(draft.code);
      setSuccess(`Deleted material ${draft.code}.`);
      await loadMaterials();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const canSave =
    !!draft &&
    !saving &&
    isDirty &&
    draft.display_name.trim().length > 0 &&
    /^[a-z0-9_-]+$/.test(draft.code);

  return (
    <div className="materials-manager">
      <aside className="materials-list">
        <div className="materials-list-header">
          <h3>Materials</h3>
          <button type="button" className="button small" onClick={handleNew}>
            + New
          </button>
        </div>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <ul>
            {materials.map((m) => (
              <li
                key={m.code}
                className={m.code === selectedCode ? "is-active" : ""}
              >
                <button type="button" onClick={() => handleSelect(m.code)}>
                  <span
                    className="material-swatch"
                    style={{ background: m.base_color }}
                  />
                  <span className="material-name">
                    {m.display_name}
                    {!m.is_active && <em className="material-flag"> · inactive</em>}
                  </span>
                  <span className="mono material-code">{m.code}</span>
                </button>
              </li>
            ))}
            {isNew && (
              <li className="is-active is-draft">
                <button type="button" disabled>
                  <span
                    className="material-swatch"
                    style={{ background: draft?.base_color }}
                  />
                  <span className="material-name">
                    {draft?.display_name || "New material"}
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

        {draft ? (
          <>
            <div className="option-group">
              <label className="option-label" htmlFor="mat-code">
                Code
              </label>
              <input
                id="mat-code"
                className="text-input mono"
                value={draft.code}
                placeholder="e.g. copper"
                onChange={(e) => setField("code", sanitizeCode(e.target.value))}
              />
            </div>

            <div className="option-group">
              <label className="option-label" htmlFor="mat-name">
                Display name
              </label>
              <input
                id="mat-name"
                className="text-input"
                value={draft.display_name}
                placeholder="e.g. Copper"
                onChange={(e) => setField("display_name", e.target.value)}
              />
            </div>

            <div className="option-group">
              <label className="option-label" htmlFor="mat-color">
                Base color
              </label>
              <div className="color-field">
                <input
                  id="mat-color"
                  type="color"
                  value={draft.base_color}
                  onChange={(e) => setField("base_color", e.target.value)}
                />
                <input
                  className="text-input mono"
                  value={draft.base_color}
                  onChange={(e) => setField("base_color", e.target.value)}
                />
              </div>
            </div>

            <SliderField
              label="Metalness"
              value={draft.metalness}
              min={0}
              max={1}
              step={0.01}
              onChange={(v) => setField("metalness", v)}
            />
            <SliderField
              label="Roughness"
              value={draft.roughness}
              min={0}
              max={1}
              step={0.01}
              onChange={(v) => setField("roughness", v)}
            />
            <SliderField
              label="Anisotropy"
              value={draft.anisotropy}
              min={0}
              max={1}
              step={0.01}
              onChange={(v) => setField("anisotropy", v)}
            />
            <SliderField
              label="Anisotropy rotation (rad)"
              value={draft.anisotropy_rotation}
              min={0}
              max={TWO_PI}
              step={0.01}
              onChange={(v) => setField("anisotropy_rotation", v)}
            />

            <div className="option-group">
              <label className="checkbox-field">
                <input
                  type="checkbox"
                  checked={draft.is_active}
                  onChange={(e) => setField("is_active", e.target.checked)}
                />
                Active (available in the configurator)
              </label>
            </div>

            <div className="actions actions-row">
              <button
                type="button"
                className="button primary"
                onClick={handleSave}
                disabled={!canSave}
              >
                {saving ? "Saving…" : isNew ? "Create Material" : "Save Changes"}
              </button>
              {!isNew && (
                <button
                  type="button"
                  className="button danger"
                  onClick={handleDelete}
                  disabled={saving}
                >
                  Delete
                </button>
              )}
            </div>
          </>
        ) : (
          !loading && <p className="muted">No material selected.</p>
        )}
      </section>

      <section className="material-preview">
        {draft ? (
          <MaterialPreview material={draft} />
        ) : (
          <div className="viewport-message">Select a material to preview.</div>
        )}
      </section>
    </div>
  );
}

interface SliderFieldProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}

function SliderField({ label, value, min, max, step, onChange }: SliderFieldProps) {
  return (
    <div className="option-group">
      <label className="option-label slider-label">
        <span>{label}</span>
        <span className="mono">{value.toFixed(2)}</span>
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}
