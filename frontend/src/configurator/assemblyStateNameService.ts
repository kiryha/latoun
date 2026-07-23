// Deterministic readable state names from geometry only (slots / modules).
// Finish is not part of the name — assignment states describe geometry.

import type { AssemblyConfiguration } from "./assemblyTypes";

const MODULE_STATE_ALIASES: Record<string, string> = {
  switch: "switch",
  dimmer: "dimmer",
  outlet: "outlet",
  usb_c_outlet: "usb-c",
};

function normalizeModuleToken(moduleTypeCode: string): string {
  return (
    MODULE_STATE_ALIASES[moduleTypeCode] ??
    moduleTypeCode.split("_").join("-")
  );
}

export function buildAssemblyStateName(
  configuration: AssemblyConfiguration,
): string {
  return [...configuration.slots]
    .sort((a, b) => a.slotNumber - b.slotNumber)
    .map((slot) => normalizeModuleToken(slot.moduleTypeCode))
    .join("-");
}
