// Authoritative public assembly configuration model.
// Geometry, summary, save, and export all derive from this state.

export type GangCount = 1 | 2 | 3 | 4;

export type ModuleTypeCode =
  | "switch"
  | "dimmer"
  | "outlet"
  | "usb_c_outlet";

export interface AssemblySlotConfiguration {
  slotNumber: number;
  moduleTypeCode: ModuleTypeCode;
}

export interface AssemblyConfiguration {
  schemaVersion: number;
  gangCount: GangCount;
  finishSchemeCode: string;
  slots: AssemblySlotConfiguration[];
}

export interface ModuleTypeOption {
  code: ModuleTypeCode;
  displayName: string;
}

export interface ConfigurationIssue {
  category: "configuration" | "asset" | "material";
  message: string;
  context?: string;
}

export const ASSEMBLY_SCHEMA_VERSION = 1;
export const DEFAULT_GANG_COUNT: GangCount = 1;
export const DEFAULT_MODULE_TYPE: ModuleTypeCode = "dimmer";
export const DEFAULT_NEW_SLOT_MODULE_TYPE: ModuleTypeCode = "switch";
export const DEFAULT_FINISH_SCHEME = "brass";
export const SUPPORTED_GANG_COUNTS: GangCount[] = [1, 2, 3, 4];
