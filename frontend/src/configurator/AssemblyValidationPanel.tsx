import type { ConfigurationIssue } from "./assemblyTypes";
import type { MissingAssetWarning, MissingMaterialReport } from "../types";

interface AssemblyValidationPanelProps {
  configurationIssues: ConfigurationIssue[];
  missingAssets: MissingAssetWarning[];
  missingMaterials: MissingMaterialReport[];
  finishSchemeCode: string;
}

export function AssemblyValidationPanel({
  configurationIssues,
  missingAssets,
  missingMaterials,
  finishSchemeCode,
}: AssemblyValidationPanelProps) {
  if (
    configurationIssues.length === 0 &&
    missingAssets.length === 0 &&
    missingMaterials.length === 0
  ) {
    return null;
  }

  return (
    <div className="validation-stack">
      {configurationIssues.length > 0 && (
        <div className="banner banner-error" role="alert">
          <div>
            <strong>Configuration errors</strong>
            <ul className="validation-list">
              {configurationIssues.map((issue) => (
                <li key={issue.message}>{issue.message}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {missingAssets.length > 0 && (
        <div className="banner banner-warning" role="status">
          <div>
            <strong>Missing geometry</strong>
            <ul className="validation-list">
              {missingAssets.map((asset) => (
                <li key={asset.asset_key}>{asset.message}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {missingMaterials.length > 0 && (
        <div className="banner banner-error" role="alert">
          <div>
            <strong>Missing material assignments</strong>
            <ul className="validation-list">
              {missingMaterials.map((item) => {
                const binding = item.binding === "" ? "(empty)" : item.binding;
                const pair = `${finishSchemeCode} + ${binding}`;
                const where =
                  item.contexts.length > 0
                    ? ` — ${item.contexts.join(", ")}`
                    : "";
                return (
                  <li key={`${item.binding}:${item.contexts.join("|")}`}>
                    {pair}
                    {where}
                  </li>
                );
              })}
            </ul>
            Affected geometry is shown in magenta.
          </div>
        </div>
      )}
    </div>
  );
}
