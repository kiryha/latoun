// Working-copy editor state for the Geometry manifest tab.

import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import {
  defaultBulkGenerateOptions,
  previewBulkGeneration,
  type BulkGenerateOptions,
} from "./assetManifestGenerator";
import {
  createDefaultEntry,
  reshapeEntryForCategory,
  uniqueCopyKey,
} from "./assetManifestNormalization";
import { validateWorkingManifest } from "./assetManifestValidation";
import type {
  AssetCategory,
  AssetManifest,
  AssetManifestEntry,
  EditableManifestEntry,
  EntryEditState,
  ModuleTypeOption,
} from "./types";
import { DEFAULT_GLB_FOLDER } from "./types";

let clientIdCounter = 0;
function nextClientId(): string {
  clientIdCounter += 1;
  return `entry-${clientIdCounter}`;
}

function entriesFromManifest(manifest: AssetManifest): EditableManifestEntry[] {
  return Object.entries(manifest.parts).map(([manifestKey, value]) => ({
    clientId: nextClientId(),
    manifestKey,
    originalManifestKey: manifestKey,
    value: structuredClone(value),
    editState: "unchanged" as EntryEditState,
  }));
}

function markModified(row: EditableManifestEntry): EntryEditState {
  if (row.editState === "added" || row.editState === "deleted") {
    return row.editState;
  }
  return "modified";
}

export function useAssetManifestEditor() {
  const [rows, setRows] = useState<EditableManifestEntry[]>([]);
  const [baseline, setBaseline] = useState<AssetManifest | null>(null);
  const [glbFolder, setGlbFolder] = useState<string>(DEFAULT_GLB_FOLDER);
  const [revision, setRevision] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [moduleTypes, setModuleTypes] = useState<ModuleTypeOption[]>([]);
  const [missingFiles, setMissingFiles] = useState<Set<string>>(new Set());

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [moduleTypesError, setModuleTypesError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setSaveError(null);
    try {
      const [manifestResponse, types] = await Promise.all([
        api.getWallPlateAssetManifest(),
        api.listModuleTypes().catch((err: unknown) => {
          setModuleTypesError(
            err instanceof Error ? err.message : String(err),
          );
          return [] as ModuleTypeOption[];
        }),
      ]);
      setModuleTypes(types);
      if (types.length > 0) setModuleTypesError(null);
      const nextRows = entriesFromManifest(manifestResponse.manifest);
      const nextFolder =
        manifestResponse.manifest.properties?.glb_folder ?? DEFAULT_GLB_FOLDER;
      setRows(nextRows);
      setGlbFolder(nextFolder);
      setBaseline(structuredClone(manifestResponse.manifest));
      setRevision(manifestResponse.revision);
      setSelectedId(nextRows[0]?.clientId ?? null);

      // Ask the backend which GLBs exist. We send full public URLs but track
      // missing state by bare file name (matches how rows store `file`).
      const files = nextRows
        .map((row) => row.value.file)
        .filter((file) => file.trim().length > 0);
      if (files.length > 0) {
        try {
          const urls = files.map((file) => `${nextFolder}${file}`);
          const status = await api.getWallPlateAssetFileStatus(urls);
          const missing = new Set<string>();
          for (const file of files) {
            if (status.files[`${nextFolder}${file}`] === false) missing.add(file);
          }
          setMissingFiles(missing);
        } catch {
          setMissingFiles(new Set());
        }
      } else {
        setMissingFiles(new Set());
      }
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : String(err),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const dirtyCount = useMemo(
    () => rows.filter((row) => row.editState !== "unchanged").length,
    [rows],
  );
  const isDirty = dirtyCount > 0;

  useEffect(() => {
    if (!isDirty) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  const validation = useMemo(
    () => validateWorkingManifest(rows, moduleTypes),
    [rows, moduleTypes],
  );

  const selected = useMemo(
    () => rows.find((row) => row.clientId === selectedId) ?? null,
    [rows, selectedId],
  );

  const liveKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const row of rows) {
      if (row.editState === "deleted") continue;
      if (row.manifestKey.trim()) keys.add(row.manifestKey.trim());
    }
    return keys;
  }, [rows]);

  const updateRow = useCallback(
    (clientId: string, updater: (row: EditableManifestEntry) => EditableManifestEntry) => {
      setRows((current) =>
        current.map((row) => {
          if (row.clientId !== clientId) return row;
          const next = updater(row);
          return { ...next, editState: markModified(next) };
        }),
      );
      setSuccess(null);
      setSaveError(null);
    },
    [],
  );

  const select = useCallback((clientId: string) => {
    setSelectedId(clientId);
    setSuccess(null);
  }, []);

  const addEntry = useCallback(
    (category: AssetCategory) => {
      const defaultModule =
        moduleTypes.find((mt) => mt.is_active)?.code ??
        moduleTypes[0]?.code ??
        "switch";
      const value = createDefaultEntry(category, defaultModule);
      const preferredKey =
        category === "plate"
          ? "plate.1gang"
          : category === "hardware"
            ? "hardware.1gang.plate_screws"
            : `module.1gang.slot01.${defaultModule}`;
      let key = preferredKey;
      if (liveKeys.has(key)) {
        key = uniqueCopyKey(preferredKey, liveKeys);
      }
      const row: EditableManifestEntry = {
        clientId: nextClientId(),
        manifestKey: key,
        value,
        editState: "added",
      };
      setRows((current) => [...current, row]);
      setSelectedId(row.clientId);
      setSuccess(null);
      setSaveError(null);
    },
    [liveKeys, moduleTypes],
  );

  const duplicateEntry = useCallback(
    (clientId: string) => {
      const source = rows.find((row) => row.clientId === clientId);
      if (!source || source.editState === "deleted") return;
      const key = uniqueCopyKey(source.manifestKey, liveKeys);
      const row: EditableManifestEntry = {
        clientId: nextClientId(),
        manifestKey: key,
        value: structuredClone(source.value),
        editState: "added",
      };
      setRows((current) => [...current, row]);
      setSelectedId(row.clientId);
      setSuccess(null);
    },
    [liveKeys, rows],
  );

  const markDeleted = useCallback((clientId: string) => {
    setRows((current) => {
      const target = current.find((row) => row.clientId === clientId);
      if (!target) return current;
      if (target.editState === "added") {
        return current.filter((row) => row.clientId !== clientId);
      }
      return current.map((row) =>
        row.clientId === clientId ? { ...row, editState: "deleted" } : row,
      );
    });
    setSelectedId((current) => (current === clientId ? null : current));
    setSuccess(null);
  }, []);

  const undoDelete = useCallback((clientId: string) => {
    setRows((current) =>
      current.map((row) => {
        if (row.clientId !== clientId) return row;
        if (!row.originalManifestKey) {
          return { ...row, editState: "added" };
        }
        return { ...row, editState: "modified" };
      }),
    );
  }, []);

  const setEntryValue = useCallback(
    (clientId: string, value: AssetManifestEntry) => {
      updateRow(clientId, (row) => ({ ...row, value }));
    },
    [updateRow],
  );

  const setManifestKey = useCallback(
    (clientId: string, manifestKey: string) => {
      updateRow(clientId, (row) => ({ ...row, manifestKey }));
    },
    [updateRow],
  );

  const changeCategory = useCallback(
    (clientId: string, category: AssetCategory) => {
      const defaultModule =
        moduleTypes.find((mt) => mt.is_active)?.code ?? "switch";
      updateRow(clientId, (row) => ({
        ...row,
        value: reshapeEntryForCategory(row.value, category, defaultModule),
      }));
    },
    [moduleTypes, updateRow],
  );

  const discard = useCallback(() => {
    if (!baseline) return;
    const nextRows = entriesFromManifest(baseline);
    setRows(nextRows);
    setSelectedId(nextRows[0]?.clientId ?? null);
    setSaveError(null);
    setSuccess(null);
  }, [baseline]);

  const applyBulkGeneration = useCallback((options: BulkGenerateOptions) => {
    const preview = previewBulkGeneration(liveKeys, options);
    if (preview.toCreate.length === 0) return 0;
    const newRows: EditableManifestEntry[] = preview.toCreate.map((item) => ({
      clientId: nextClientId(),
      manifestKey: item.manifestKey,
      value: item.value,
      editState: "added",
    }));
    setRows((current) => [...current, ...newRows]);
    setSelectedId(newRows[0]?.clientId ?? null);
    setSuccess(null);
    return newRows.length;
  }, [liveKeys]);

  const save = useCallback(async () => {
    if (!validation.ok) {
      setSaveError("Fix validation errors before saving the manifest.");
      return false;
    }

    const hasMissing = rows.some(
      (row) =>
        row.editState !== "deleted" && missingFiles.has(row.value.file),
    );
    if (hasMissing) {
      const confirmed = window.confirm(
        "Some GLB files are missing. Save the manifest anyway?\n\nGeometry can be added later.",
      );
      if (!confirmed) return false;
    }

    const parts: Record<string, AssetManifestEntry> = {};
    for (const row of rows) {
      if (row.editState === "deleted") continue;
      // Strip incompatible fields by reshaping through category.
      parts[row.manifestKey.trim()] = reshapeEntryForCategory(
        row.value,
        row.value.category,
        row.value.category === "slot_module" ? row.value.module_type : "switch",
      );
    }

    setSaving(true);
    setSaveError(null);
    setSuccess(null);
    try {
      const saved = await api.saveWallPlateAssetManifest({
        manifest: { properties: { glb_folder: glbFolder }, parts },
        expected_revision: revision,
      });
      const nextRows = entriesFromManifest(saved.manifest);
      setRows(nextRows);
      setGlbFolder(saved.manifest.properties?.glb_folder ?? glbFolder);
      setBaseline(structuredClone(saved.manifest));
      setRevision(saved.revision);
      setSelectedId((current) => {
        if (!current) return nextRows[0]?.clientId ?? null;
        const previous = rows.find((row) => row.clientId === current);
        if (!previous || previous.editState === "deleted") {
          return nextRows[0]?.clientId ?? null;
        }
        const match = nextRows.find(
          (row) => row.manifestKey === previous.manifestKey,
        );
        return match?.clientId ?? nextRows[0]?.clientId ?? null;
      });
      setSuccess(
        saved.warnings.length > 0
          ? `Manifest saved with ${saved.warnings.length} warning(s).`
          : "Manifest saved.",
      );
      return true;
    } catch (err) {
      setSaveError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : String(err),
      );
      return false;
    } finally {
      setSaving(false);
    }
  }, [glbFolder, missingFiles, revision, rows, validation.ok]);

  const fileUrl = useCallback(
    (file: string) => (file.trim().length > 0 ? `${glbFolder}${file}` : ""),
    [glbFolder],
  );

  return {
    rows,
    selected,
    selectedId,
    moduleTypes,
    missingFiles,
    glbFolder,
    fileUrl,
    validation,
    dirtyCount,
    isDirty,
    loading,
    saving,
    loadError,
    moduleTypesError,
    saveError,
    success,
    load,
    select,
    addEntry,
    duplicateEntry,
    markDeleted,
    undoDelete,
    setEntryValue,
    setManifestKey,
    changeCategory,
    discard,
    save,
    applyBulkGeneration,
    defaultBulkOptions: defaultBulkGenerateOptions(moduleTypes),
    previewBulk: (options: BulkGenerateOptions) =>
      previewBulkGeneration(liveKeys, options),
  };
}
