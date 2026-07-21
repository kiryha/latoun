// Builds and downloads the active configuration as a JSON file.

import type { RenderState } from "../types";

export function buildExportPayload(
  renderState: RenderState,
  configurationCode: string | null,
) {
  return {
    configuration_code: configurationCode ?? null,
    gang_count: renderState.configuration.gang_count,
    module_type: renderState.configuration.module_type,
    material: renderState.configuration.material,
    assets: renderState.assets.map((asset) => asset.asset_key),
    prototype_bom: renderState.bom,
  };
}

export function downloadConfigurationJson(
  renderState: RenderState,
  configurationCode: string | null,
) {
  const payload = buildExportPayload(renderState, configurationCode);
  const fileName = configurationCode
    ? `${configurationCode}.json`
    : "latoun_configuration_draft.json";

  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
