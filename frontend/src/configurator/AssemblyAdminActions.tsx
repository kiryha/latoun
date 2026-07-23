interface AssemblyAdminActionsProps {
  canSave: boolean;
  canExport: boolean;
  isSaving: boolean;
  onSave: () => void;
  onExport: () => void;
}

export function AssemblyAdminActions({
  canSave,
  canExport,
  isSaving,
  onSave,
  onExport,
}: AssemblyAdminActionsProps) {
  return (
    <section className="option-group">
      <h3 className="option-label">Admin Actions</h3>
      <div className="actions">
        <button
          type="button"
          className="button primary"
          onClick={onSave}
          disabled={!canSave || isSaving}
        >
          {isSaving ? "Saving…" : "Save Current State"}
        </button>
        <button
          type="button"
          className="button"
          onClick={onExport}
          disabled={!canExport}
        >
          Export JSON
        </button>
      </div>
    </section>
  );
}
