// Compact saved-configuration picker. Uses a dropdown so the list stays
// usable even with a large number of saved configurations.

import type { ConfigurationSummary } from "../types";

interface SavedConfigurationsProps {
  configurations: ConfigurationSummary[];
  activeId: number | null;
  onLoad: (id: number) => void;
  onDelete?: (id: number) => void;
  deletingId?: number | null;
}

export function SavedConfigurations({
  configurations,
  activeId,
  onLoad,
  onDelete,
  deletingId = null,
}: SavedConfigurationsProps) {
  const selectedId = activeId ?? "";
  const canDelete = !!onDelete && selectedId !== "";

  return (
    <div className="saved-list">
      <label className="option-label" htmlFor="saved-configuration-select">
        Saved Configurations
      </label>
      {configurations.length === 0 ? (
        <p className="muted">No saved configurations yet.</p>
      ) : (
        <div className="saved-row">
          <select
            id="saved-configuration-select"
            className="text-input saved-select"
            value={selectedId}
            onChange={(event) => {
              const value = event.target.value;
              if (!value) return;
              onLoad(Number(value));
            }}
          >
            <option value="" disabled={activeId !== null}>
              Select a configuration…
            </option>
            {configurations.map((config) => (
              <option
                key={config.configuration_id}
                value={config.configuration_id}
              >
                {config.configuration_code}
              </option>
            ))}
          </select>
          {onDelete && (
            <button
              type="button"
              className="button small danger saved-delete"
              title="Delete selected configuration"
              aria-label="Delete selected configuration"
              disabled={!canDelete || deletingId !== null}
              onClick={() => {
                if (selectedId === "") return;
                onDelete(Number(selectedId));
              }}
            >
              {deletingId !== null ? "…" : "Delete"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
