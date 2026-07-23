// Pure helpers for creating and mutating the public assembly configuration.
// No Assignment State dependency — UI state is the source of truth.

import type {
  AssemblyConfiguration,
  AssemblySlotConfiguration,
  ConfigurationIssue,
  GangCount,
  ModuleTypeCode,
  ModuleTypeOption,
} from "./assemblyTypes";
import {
  ASSEMBLY_SCHEMA_VERSION,
  DEFAULT_FINISH_SCHEME,
  DEFAULT_GANG_COUNT,
  DEFAULT_MODULE_TYPE,
  DEFAULT_NEW_SLOT_MODULE_TYPE,
  SUPPORTED_GANG_COUNTS,
} from "./assemblyTypes";

function buildSlots(
  gangCount: GangCount,
  existing: AssemblySlotConfiguration[] = [],
  defaultModuleType: ModuleTypeCode = DEFAULT_NEW_SLOT_MODULE_TYPE,
): AssemblySlotConfiguration[] {
  const bySlot = new Map(
    existing.map((slot) => [slot.slotNumber, slot.moduleTypeCode]),
  );
  const slots: AssemblySlotConfiguration[] = [];
  for (let slotNumber = 1; slotNumber <= gangCount; slotNumber += 1) {
    slots.push({
      slotNumber,
      moduleTypeCode: bySlot.get(slotNumber) ?? defaultModuleType,
    });
  }
  return slots;
}

export function createDefaultConfiguration(
  overrides: Partial<
    Pick<AssemblyConfiguration, "gangCount" | "finishSchemeCode">
  > & {
    defaultModuleType?: ModuleTypeCode;
  } = {},
): AssemblyConfiguration {
  const gangCount = overrides.gangCount ?? DEFAULT_GANG_COUNT;
  const defaultModuleType = overrides.defaultModuleType ?? DEFAULT_MODULE_TYPE;
  return {
    schemaVersion: ASSEMBLY_SCHEMA_VERSION,
    gangCount,
    finishSchemeCode: overrides.finishSchemeCode ?? DEFAULT_FINISH_SCHEME,
    slots: buildSlots(gangCount, [], defaultModuleType),
  };
}

export function changeGangCount(
  configuration: AssemblyConfiguration,
  gangCount: GangCount,
  defaultModuleType: ModuleTypeCode = DEFAULT_NEW_SLOT_MODULE_TYPE,
): AssemblyConfiguration {
  if (!SUPPORTED_GANG_COUNTS.includes(gangCount)) {
    throw new Error(`Unsupported gang count: ${gangCount}`);
  }
  return {
    ...configuration,
    gangCount,
    slots: buildSlots(gangCount, configuration.slots, defaultModuleType),
  };
}

export function changeSlotModule(
  configuration: AssemblyConfiguration,
  slotNumber: number,
  moduleTypeCode: ModuleTypeCode,
): AssemblyConfiguration {
  if (slotNumber < 1 || slotNumber > configuration.gangCount) {
    throw new Error(`Slot ${slotNumber} is outside the active assembly.`);
  }
  return {
    ...configuration,
    slots: configuration.slots.map((slot) =>
      slot.slotNumber === slotNumber ? { ...slot, moduleTypeCode } : slot,
    ),
  };
}

export function changeFinishScheme(
  configuration: AssemblyConfiguration,
  finishSchemeCode: string,
): AssemblyConfiguration {
  return {
    ...configuration,
    finishSchemeCode,
  };
}

export function toResolvePayload(configuration: AssemblyConfiguration) {
  return {
    gang_count: configuration.gangCount,
    modules: [...configuration.slots]
      .sort((a, b) => a.slotNumber - b.slotNumber)
      .map((slot) => ({
        slot_number: slot.slotNumber,
        module_type: slot.moduleTypeCode,
      })),
    finish_scheme: configuration.finishSchemeCode,
  };
}

export function validateConfiguration(
  configuration: AssemblyConfiguration,
  options: {
    moduleOptions: ModuleTypeOption[];
    finishSchemeCodes: string[];
  },
): ConfigurationIssue[] {
  const issues: ConfigurationIssue[] = [];
  const activeCodes = new Set(options.moduleOptions.map((item) => item.code));

  if (!SUPPORTED_GANG_COUNTS.includes(configuration.gangCount)) {
    issues.push({
      category: "configuration",
      message: `Gang count must be 1, 2, 3, or 4 (got ${configuration.gangCount}).`,
    });
  }

  if (configuration.slots.length !== configuration.gangCount) {
    issues.push({
      category: "configuration",
      message: `Expected ${configuration.gangCount} slot(s); found ${configuration.slots.length}.`,
    });
  }

  const expected = Array.from(
    { length: configuration.gangCount },
    (_, index) => index + 1,
  );
  const actual = [...configuration.slots]
    .map((slot) => slot.slotNumber)
    .sort((a, b) => a - b);
  if (actual.join(",") !== expected.join(",")) {
    issues.push({
      category: "configuration",
      message: `Slot numbers must be sequential from 1 to ${configuration.gangCount}.`,
    });
  }

  for (const slot of configuration.slots) {
    if (!slot.moduleTypeCode) {
      issues.push({
        category: "configuration",
        message: `Slot ${slot.slotNumber} has no selected device.`,
        context: `slot ${slot.slotNumber}`,
      });
      continue;
    }
    if (!activeCodes.has(slot.moduleTypeCode)) {
      issues.push({
        category: "configuration",
        message: `Slot ${slot.slotNumber} uses unavailable device “${slot.moduleTypeCode}”.`,
        context: `slot ${slot.slotNumber}`,
      });
    }
  }

  if (!options.finishSchemeCodes.includes(configuration.finishSchemeCode)) {
    issues.push({
      category: "configuration",
      message: `Finish scheme “${configuration.finishSchemeCode}” is not available.`,
    });
  }

  return issues;
}

export function isGangCount(value: number): value is GangCount {
  return SUPPORTED_GANG_COUNTS.includes(value as GangCount);
}

export function isModuleTypeCode(value: string): value is ModuleTypeCode {
  return (
    value === "switch" ||
    value === "dimmer" ||
    value === "outlet" ||
    value === "usb_c_outlet"
  );
}
