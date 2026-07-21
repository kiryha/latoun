// List of saved configurations with a load action.

import type { ConfigurationSummary } from "../types";

interface SavedConfigurationsProps {
  configurations: ConfigurationSummary[];
  activeId: number | null;
  onLoad: (id: number) => void;
}

export function SavedConfigurations({
  configurations,
  activeId,
  onLoad,
}: SavedConfigurationsProps) {
  return (
    <div className="saved-list">
      <h3>Saved Configurations</h3>
      {configurations.length === 0 ? (
        <p className="muted">No saved configurations yet.</p>
      ) : (
        <ul>
          {configurations.map((config) => (
            <li
              key={config.configuration_id}
              className={config.configuration_id === activeId ? "is-active" : ""}
            >
              <button type="button" onClick={() => onLoad(config.configuration_id)}>
                <span className="mono">{config.configuration_code}</span>
                <span className="saved-meta">
                  {config.module_type_code} · {config.material_code}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
