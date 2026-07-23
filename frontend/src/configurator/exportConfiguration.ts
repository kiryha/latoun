// Builds and downloads the active assembly as a JSON file.

import type { RenderState } from "../types";

export function buildExportPayload(renderState: RenderState) {
  return {
    gang_count: renderState.assembly.gang_count,
    modules: renderState.assembly.modules,
    finish_scheme: renderState.assembly.finish_scheme,
    assignment_state_code: renderState.assembly.assignment_state_code,
    assets: renderState.assets.map((asset) => asset.asset_key),
    resolved_material_assignments: renderState.material_assignments,
    prototype_bom: renderState.bom,
  };
}

export function downloadAssemblyJson(renderState: RenderState) {
  const payload = buildExportPayload(renderState);
  const fileName = renderState.assembly.assignment_state_code
    ? `${renderState.assembly.assignment_state_code}.json`
    : "latoun_assembly_draft.json";

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
