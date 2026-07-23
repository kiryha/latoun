// Builds and downloads the active assembly as structured JSON.

import type { AssemblyConfiguration } from "./assemblyTypes";
import type { RenderState } from "../types";
import { buildAssemblyStateName } from "./assemblyStateNameService";

export function buildExportPayload(
  configuration: AssemblyConfiguration,
  renderState: RenderState | null,
) {
  const payload = {
    schema_version: configuration.schemaVersion,
    gang_count: configuration.gangCount,
    finish_scheme_code: configuration.finishSchemeCode,
    slots: [...configuration.slots]
      .sort((a, b) => a.slotNumber - b.slotNumber)
      .map((slot) => ({
        slot_number: slot.slotNumber,
        module_type_code: slot.moduleTypeCode,
      })),
    state_name: buildAssemblyStateName(configuration),
  };

  if (!renderState) {
    return payload;
  }

  return {
    ...payload,
    debug: {
      assets: renderState.assets.map((asset) => asset.asset_key),
      missing_assets: renderState.missing_assets ?? [],
      resolved_material_assignments: renderState.material_assignments,
      prototype_bom: renderState.bom,
    },
  };
}

export function downloadAssemblyJson(
  configuration: AssemblyConfiguration,
  renderState: RenderState | null,
) {
  const payload = buildExportPayload(configuration, renderState);
  const fileName = `${buildAssemblyStateName(configuration)}.json`;

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
