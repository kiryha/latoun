import { useEffect, useMemo, useState } from "react";
import { Banner } from "../components/Banner";
import {
  type BulkGenerateOptions,
} from "./assetManifestGenerator";
import { entryStatusLabel } from "./assetManifestValidation";
import { GeometryPreview } from "./GeometryPreview";
import {
  ASSET_TYPE_LABELS,
  GANG_COUNTS,
  type AssetType,
  type EditableManifestEntry,
  type GangCount,
} from "./types";
import { useAssetManifestEditor } from "./useAssetManifestEditor";

type SortKey =
  | "key"
  | "type"
  | "gang"
  | "slot"
  | "module"
  | "active"
  | "status";

function hardwareLabel(code: string | undefined): string {
  if (code === "plate_screws") return "Plate Screws";
  return code ?? "—";
}

interface GeometryTabProps {
  onDirtyChange?: (dirty: boolean) => void;
}

export function GeometryTab({ onDirtyChange }: GeometryTabProps) {
  const editor = useAssetManifestEditor();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<AssetType | "all">("all");
  const [filterGang, setFilterGang] = useState<GangCount | "all">("all");
  const [filterActive, setFilterActive] = useState<"all" | "active" | "inactive">(
    "all",
  );
  const [sortKey, setSortKey] = useState<SortKey>("key");
  const [sortAsc, setSortAsc] = useState(true);
  const [showGenerator, setShowGenerator] = useState(false);
  const [generatorOptions, setGeneratorOptions] = useState<BulkGenerateOptions | null>(
    null,
  );
  const [addMenuOpen, setAddMenuOpen] = useState(false);

  useEffect(() => {
    onDirtyChange?.(editor.isDirty);
    return () => onDirtyChange?.(false);
  }, [editor.isDirty, onDirtyChange]);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const moduleLabel = (code: string) =>
      editor.moduleTypes.find((mt) => mt.code === code)?.display_name ?? code;

    let list = [...editor.rows];
    if (filterType !== "all") {
      list = list.filter((row) => row.value.asset_type === filterType);
    }
    if (filterGang !== "all") {
      list = list.filter((row) => row.value.gang_count === filterGang);
    }
    if (filterActive === "active") {
      list = list.filter(
        (row) => row.editState !== "deleted" && row.value.is_active,
      );
    } else if (filterActive === "inactive") {
      list = list.filter(
        (row) => row.editState !== "deleted" && !row.value.is_active,
      );
    }
    if (query) {
      list = list.filter((row) => {
        const moduleCode =
          row.value.asset_type === "slot_module" ? row.value.module_type : "";
        const haystack = [
          row.manifestKey,
          row.value.file,
          moduleCode,
          moduleLabel(moduleCode),
          row.value.asset_type,
        ]
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      });
    }

    list.sort((a, b) => {
      const dir = sortAsc ? 1 : -1;
      const statusA = entryStatusLabel(a, editor.validation, editor.missingFiles);
      const statusB = entryStatusLabel(b, editor.validation, editor.missingFiles);
      const slotA =
        a.value.asset_type === "slot_module" ? a.value.slot_position : 0;
      const slotB =
        b.value.asset_type === "slot_module" ? b.value.slot_position : 0;
      const moduleA =
        a.value.asset_type === "slot_module" ? a.value.module_type : "";
      const moduleB =
        b.value.asset_type === "slot_module" ? b.value.module_type : "";
      switch (sortKey) {
        case "type":
          return a.value.asset_type.localeCompare(b.value.asset_type) * dir;
        case "gang":
          return (a.value.gang_count - b.value.gang_count) * dir;
        case "slot":
          return (slotA - slotB) * dir;
        case "module":
          return moduleA.localeCompare(moduleB) * dir;
        case "active":
          return (Number(a.value.is_active) - Number(b.value.is_active)) * dir;
        case "status":
          return statusA.localeCompare(statusB) * dir;
        case "key":
        default:
          return a.manifestKey.localeCompare(b.manifestKey) * dir;
      }
    });
    return list;
  }, [
    editor.missingFiles,
    editor.moduleTypes,
    editor.rows,
    editor.validation,
    filterActive,
    filterGang,
    filterType,
    search,
    sortAsc,
    sortKey,
  ]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc((value) => !value);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const openGenerator = () => {
    setGeneratorOptions(editor.defaultBulkOptions);
    setShowGenerator(true);
  };

  const generatorPreview = generatorOptions
    ? editor.previewBulk(generatorOptions)
    : null;

  const handleDiscard = () => {
    if (!editor.isDirty) return;
    if (!window.confirm("Discard all unsaved manifest changes?")) return;
    editor.discard();
  };

  const handleDelete = (row: EditableManifestEntry) => {
    if (row.editState === "deleted") {
      editor.undoDelete(row.clientId);
      return;
    }
    if (
      !window.confirm(
        "Remove this entry from the asset manifest?\n\nThe GLB file will not be deleted.",
      )
    ) {
      return;
    }
    editor.markDeleted(row.clientId);
  };

  const selected = editor.selected;

  return (
    <div className="geometry-manager">
      <header className="geometry-toolbar">
        <div>
          <h2>Geometry Manifest</h2>
          <p className="geometry-dirty">
            {editor.isDirty
              ? `Unsaved changes: ${editor.dirtyCount}`
              : "No unsaved changes"}
          </p>
        </div>
        <div className="geometry-toolbar-actions">
          <button
            type="button"
            className="button small"
            onClick={openGenerator}
            disabled={!!editor.loadError}
          >
            Generate Wall-Plate Entries
          </button>
          <button
            type="button"
            className="button small"
            onClick={handleDiscard}
            disabled={!editor.isDirty || editor.saving}
          >
            Discard Changes
          </button>
          <button
            type="button"
            className="button primary"
            onClick={() => void editor.save()}
            disabled={!editor.isDirty || editor.saving || !!editor.loadError}
          >
            {editor.saving ? "Saving…" : "Save Manifest"}
          </button>
        </div>
      </header>

      {editor.loadError && (
        <Banner kind="error">
          {editor.loadError}{" "}
          <button type="button" className="button small" onClick={() => void editor.load()}>
            Retry
          </button>
        </Banner>
      )}
      {editor.saveError && <Banner kind="error">{editor.saveError}</Banner>}
      {editor.success && <Banner kind="success">{editor.success}</Banner>}
      {editor.moduleTypesError && (
        <Banner kind="error">
          Module types failed to load: {editor.moduleTypesError}
        </Banner>
      )}

      <div className="geometry-filters">
        <label>
          Search
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Key, file, module…"
          />
        </label>
        <label>
          Asset Type
          <select
            value={filterType}
            onChange={(event) =>
              setFilterType(event.target.value as AssetType | "all")
            }
          >
            <option value="all">All</option>
            <option value="plate">Plate</option>
            <option value="hardware">Hardware</option>
            <option value="slot_module">Slot Module</option>
          </select>
        </label>
        <label>
          Gang
          <select
            value={filterGang === "all" ? "all" : String(filterGang)}
            onChange={(event) => {
              const value = event.target.value;
              setFilterGang(value === "all" ? "all" : (Number(value) as GangCount));
            }}
          >
            <option value="all">All</option>
            {GANG_COUNTS.map((gang) => (
              <option key={gang} value={gang}>
                {gang} Gang
              </option>
            ))}
          </select>
        </label>
        <label>
          Active
          <select
            value={filterActive}
            onChange={(event) =>
              setFilterActive(event.target.value as typeof filterActive)
            }
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </label>
        <div className="geometry-add">
          <button
            type="button"
            className="button small"
            onClick={() => setAddMenuOpen((open) => !open)}
            disabled={!!editor.loadError}
          >
            Add Entry
          </button>
          {addMenuOpen && (
            <div className="geometry-add-menu" role="menu">
              {(["plate", "hardware", "slot_module"] as AssetType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    editor.addEntry(type);
                    setAddMenuOpen(false);
                  }}
                >
                  {ASSET_TYPE_LABELS[type]}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="geometry-body">
        <section className="geometry-table-panel" aria-label="Manifest entries">
          {editor.loading ? (
            <p className="muted">Loading manifest…</p>
          ) : (
            <div className="geometry-table-scroll">
              <table className="geometry-table">
                <thead>
                  <tr>
                    <th>
                      <button type="button" onClick={() => toggleSort("active")}>
                        Active
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => toggleSort("key")}>
                        Manifest Key
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => toggleSort("type")}>
                        Asset Type
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => toggleSort("gang")}>
                        Gang
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => toggleSort("slot")}>
                        Slot
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => toggleSort("module")}>
                        Module / Hardware
                      </button>
                    </th>
                    <th>File</th>
                    <th>
                      <button type="button" onClick={() => toggleSort("status")}>
                        Status
                      </button>
                    </th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row) => {
                    const selectedRow = row.clientId === editor.selectedId;
                    const status = entryStatusLabel(
                      row,
                      editor.validation,
                      editor.missingFiles,
                    );
                    return (
                      <tr
                        key={row.clientId}
                        className={[
                          selectedRow ? "is-selected" : "",
                          row.editState !== "unchanged" ? "is-dirty" : "",
                          row.editState === "deleted" ? "is-deleted" : "",
                          !row.value.is_active ? "is-inactive" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        onClick={() => editor.select(row.clientId)}
                      >
                        <td>
                          <input
                            type="checkbox"
                            checked={row.value.is_active}
                            disabled={row.editState === "deleted"}
                            aria-label={`Active ${row.manifestKey}`}
                            onChange={(event) => {
                              event.stopPropagation();
                              editor.setEntryValue(row.clientId, {
                                ...row.value,
                                is_active: event.target.checked,
                              });
                            }}
                            onClick={(event) => event.stopPropagation()}
                          />
                        </td>
                        <td>
                          <code>{row.manifestKey || "(empty)"}</code>
                          {row.editState !== "unchanged" && (
                            <em className="geometry-row-flag"> · {row.editState}</em>
                          )}
                        </td>
                        <td>{ASSET_TYPE_LABELS[row.value.asset_type]}</td>
                        <td>{row.value.gang_count}</td>
                        <td>
                          {row.value.asset_type === "slot_module"
                            ? row.value.slot_position
                            : "—"}
                        </td>
                        <td>
                          {row.value.asset_type === "slot_module"
                            ? (() => {
                                const moduleCode = row.value.module_type;
                                return (
                                  editor.moduleTypes.find(
                                    (mt) => mt.code === moduleCode,
                                  )?.display_name ?? moduleCode
                                );
                              })()
                            : row.value.asset_type === "hardware"
                              ? hardwareLabel(row.value.hardware_type)
                              : "—"}
                        </td>
                        <td className="geometry-file-cell" title={row.value.file}>
                          <code>{row.value.file}</code>
                        </td>
                        <td>{status}</td>
                        <td className="geometry-row-actions">
                          <button
                            type="button"
                            className="button small"
                            onClick={(event) => {
                              event.stopPropagation();
                              editor.duplicateEntry(row.clientId);
                            }}
                            disabled={row.editState === "deleted"}
                          >
                            Duplicate
                          </button>
                          <button
                            type="button"
                            className="button small danger"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleDelete(row);
                            }}
                          >
                            {row.editState === "deleted" ? "Undo" : "Delete"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="geometry-side">
          <section className="geometry-editor" aria-label="Selected entry editor">
            <h3>Entry Editor</h3>
            {!selected ? (
              <p className="muted">Select an entry to edit.</p>
            ) : (
              <EntryEditor
                row={selected}
                moduleTypes={editor.moduleTypes}
                moduleTypesError={editor.moduleTypesError}
                onKeyChange={(key) => editor.setManifestKey(selected.clientId, key)}
                onAssetTypeChange={(type) =>
                  editor.changeAssetType(selected.clientId, type)
                }
                onValueChange={(value) =>
                  editor.setEntryValue(selected.clientId, value)
                }
              />
            )}
          </section>
          <GeometryPreview
            filePath={
              selected && selected.editState !== "deleted"
                ? selected.value.file
                : null
            }
            missingFile={
              !!selected && editor.missingFiles.has(selected.value.file)
            }
          />
        </aside>
      </div>

      <section className="geometry-validation" aria-label="Validation">
        <h3>Validation</h3>
        {editor.validation.errors.length === 0 &&
        editor.validation.warnings.length === 0 ? (
          <p className="muted">No issues.</p>
        ) : (
          <div className="geometry-validation-lists">
            {editor.validation.errors.length > 0 && (
              <div>
                <h4>Errors</h4>
                <ul>
                  {editor.validation.errors.map((issue, index) => (
                    <li key={`e-${index}`}>
                      {issue.assetKey ? (
                        <strong>{issue.assetKey}: </strong>
                      ) : null}
                      {issue.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {editor.validation.warnings.length > 0 && (
              <div>
                <h4>Warnings</h4>
                <ul>
                  {editor.validation.warnings.map((issue, index) => (
                    <li key={`w-${index}`}>
                      {issue.assetKey ? (
                        <strong>{issue.assetKey}: </strong>
                      ) : null}
                      {issue.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      {showGenerator && generatorOptions && generatorPreview && (
        <div className="geometry-modal-backdrop" role="presentation">
          <div
            className="geometry-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="bulk-generate-title"
          >
            <h3 id="bulk-generate-title">Generate Wall-Plate Entries</h3>
            <div className="geometry-modal-grid">
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={generatorOptions.generatePlates}
                  onChange={(event) =>
                    setGeneratorOptions({
                      ...generatorOptions,
                      generatePlates: event.target.checked,
                    })
                  }
                />
                Generate plates
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={generatorOptions.generatePlateScrews}
                  onChange={(event) =>
                    setGeneratorOptions({
                      ...generatorOptions,
                      generatePlateScrews: event.target.checked,
                    })
                  }
                />
                Generate plate screws
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={generatorOptions.generateSlotModules}
                  onChange={(event) =>
                    setGeneratorOptions({
                      ...generatorOptions,
                      generateSlotModules: event.target.checked,
                    })
                  }
                />
                Generate slot modules
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={generatorOptions.activateGenerated}
                  onChange={(event) =>
                    setGeneratorOptions({
                      ...generatorOptions,
                      activateGenerated: event.target.checked,
                    })
                  }
                />
                Activate generated entries
              </label>
            </div>

            <fieldset>
              <legend>Gang counts</legend>
              <div className="geometry-chip-row">
                {GANG_COUNTS.map((gang) => {
                  const checked = generatorOptions.gangCounts.includes(gang);
                  return (
                    <label key={gang} className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          const gangCounts = event.target.checked
                            ? [...generatorOptions.gangCounts, gang]
                            : generatorOptions.gangCounts.filter((g) => g !== gang);
                          setGeneratorOptions({
                            ...generatorOptions,
                            gangCounts: gangCounts.sort(
                              (a, b) => a - b,
                            ) as GangCount[],
                          });
                        }}
                      />
                      {gang} Gang
                    </label>
                  );
                })}
              </div>
            </fieldset>

            <fieldset>
              <legend>Module types</legend>
              <div className="geometry-chip-row">
                {editor.moduleTypes.map((mt) => {
                  const checked = generatorOptions.moduleTypeCodes.includes(mt.code);
                  return (
                    <label key={mt.code} className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          const moduleTypeCodes = event.target.checked
                            ? [...generatorOptions.moduleTypeCodes, mt.code]
                            : generatorOptions.moduleTypeCodes.filter(
                                (code) => code !== mt.code,
                              );
                          setGeneratorOptions({
                            ...generatorOptions,
                            moduleTypeCodes,
                          });
                        }}
                      />
                      {mt.display_name}
                      {!mt.is_active ? " (inactive)" : ""}
                    </label>
                  );
                })}
              </div>
            </fieldset>

            <p>
              New entries to create: {generatorPreview.toCreate.length}
              <br />
              Existing entries preserved: {generatorPreview.preservedCount}
              <br />
              Conflicts skipped: {generatorPreview.conflictCount}
            </p>

            <div className="geometry-modal-actions">
              <button
                type="button"
                className="button"
                onClick={() => setShowGenerator(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button primary"
                disabled={generatorPreview.toCreate.length === 0}
                onClick={() => {
                  editor.applyBulkGeneration(generatorOptions);
                  setShowGenerator(false);
                }}
              >
                Add Generated Entries
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EntryEditor({
  row,
  moduleTypes,
  moduleTypesError,
  onKeyChange,
  onAssetTypeChange,
  onValueChange,
}: {
  row: EditableManifestEntry;
  moduleTypes: ReturnType<typeof useAssetManifestEditor>["moduleTypes"];
  moduleTypesError: string | null;
  onKeyChange: (key: string) => void;
  onAssetTypeChange: (type: AssetType) => void;
  onValueChange: (value: EditableManifestEntry["value"]) => void;
}) {
  const value = row.value;
  const disabled = row.editState === "deleted";
  const activeModuleTypes = moduleTypes.filter((mt) => mt.is_active);
  const selectedModule = moduleTypes.find(
    (mt) => value.asset_type === "slot_module" && mt.code === value.module_type,
  );

  return (
    <div className="geometry-form">
      <label>
        Manifest Key
        <input
          type="text"
          value={row.manifestKey}
          disabled={disabled}
          onChange={(event) => onKeyChange(event.target.value)}
        />
      </label>
      <label>
        Asset Type
        <select
          value={value.asset_type}
          disabled={disabled}
          onChange={(event) =>
            onAssetTypeChange(event.target.value as AssetType)
          }
        >
          <option value="plate">Plate</option>
          <option value="hardware">Hardware</option>
          <option value="slot_module">Slot Module</option>
        </select>
      </label>
      <label>
        Gang Count
        <select
          value={value.gang_count}
          disabled={disabled}
          onChange={(event) =>
            onValueChange({
              ...value,
              gang_count: Number(event.target.value) as GangCount,
            })
          }
        >
          {GANG_COUNTS.map((gang) => (
            <option key={gang} value={gang}>
              {gang} Gang
            </option>
          ))}
        </select>
      </label>

      {value.asset_type === "hardware" && (
        <label>
          Hardware Type
          <select
            value={value.hardware_type}
            disabled={disabled}
            onChange={() =>
              onValueChange({ ...value, hardware_type: "plate_screws" })
            }
          >
            <option value="plate_screws">Plate Screws</option>
          </select>
        </label>
      )}

      {value.asset_type === "slot_module" && (
        <>
          <label>
            Slot Position
            <select
              value={value.slot_position}
              disabled={disabled}
              onChange={(event) =>
                onValueChange({
                  ...value,
                  slot_position: Number(event.target.value),
                })
              }
            >
              {Array.from({ length: value.gang_count }, (_, index) => index + 1).map(
                (slot) => (
                  <option key={slot} value={slot}>
                    {slot}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            Module Type
            <select
              value={value.module_type}
              disabled={disabled || !!moduleTypesError || moduleTypes.length === 0}
              onChange={(event) =>
                onValueChange({
                  ...value,
                  module_type: event.target.value,
                })
              }
            >
              {selectedModule && !selectedModule.is_active && (
                <option value={selectedModule.code}>
                  {selectedModule.display_name} (inactive)
                </option>
              )}
              {activeModuleTypes.map((mt) => (
                <option key={mt.code} value={mt.code}>
                  {mt.display_name}
                </option>
              ))}
            </select>
          </label>
          {moduleTypesError && (
            <p className="field-error">{moduleTypesError}</p>
          )}
        </>
      )}

      <label>
        GLB File Path
        <input
          type="text"
          value={value.file}
          disabled={disabled}
          onChange={(event) =>
            onValueChange({ ...value, file: event.target.value })
          }
        />
      </label>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={value.is_active}
          disabled={disabled}
          onChange={(event) =>
            onValueChange({ ...value, is_active: event.target.checked })
          }
        />
        Active
      </label>
    </div>
  );
}
