import { describe, expect, it } from "vitest";
import {
  changeFinishScheme,
  changeGangCount,
  changeSlotModule,
  createDefaultConfiguration,
  toResolvePayload,
  validateConfiguration,
} from "./assemblyConfigurationService";
import { buildAssemblyStateName } from "./assemblyStateNameService";
import type { ModuleTypeOption } from "./assemblyTypes";

const MODULE_OPTIONS: ModuleTypeOption[] = [
  { code: "switch", displayName: "Switch" },
  { code: "dimmer", displayName: "Dimmer" },
  { code: "outlet", displayName: "Outlet" },
  { code: "usb_c_outlet", displayName: "USB-C Outlet" },
];

const FINISHES = ["brass", "steel"];

describe("assemblyConfigurationService", () => {
  it("creates a valid default configuration", () => {
    const config = createDefaultConfiguration();
    expect(config.gangCount).toBe(1);
    expect(config.slots).toEqual([
      { slotNumber: 1, moduleTypeCode: "dimmer" },
    ]);
    expect(config.finishSchemeCode).toBe("brass");
    expect(
      validateConfiguration(config, {
        moduleOptions: MODULE_OPTIONS,
        finishSchemeCodes: FINISHES,
      }),
    ).toEqual([]);
  });

  it.each([1, 2, 3, 4] as const)(
    "produces %i sequential slot(s) for gang count",
    (gangCount) => {
      const config = changeGangCount(createDefaultConfiguration(), gangCount);
      expect(config.slots).toHaveLength(gangCount);
      expect(config.slots.map((slot) => slot.slotNumber)).toEqual(
        Array.from({ length: gangCount }, (_, index) => index + 1),
      );
    },
  );

  it("preserves existing slots when increasing gang count and defaults new ones", () => {
    let config = createDefaultConfiguration();
    config = changeSlotModule(config, 1, "dimmer");
    config = changeGangCount(config, 2);
    expect(config.slots).toEqual([
      { slotNumber: 1, moduleTypeCode: "dimmer" },
      { slotNumber: 2, moduleTypeCode: "switch" },
    ]);
  });

  it("removes excess slots when decreasing gang count", () => {
    let config = changeGangCount(createDefaultConfiguration(), 4);
    config = changeSlotModule(config, 1, "switch");
    config = changeSlotModule(config, 2, "outlet");
    config = changeSlotModule(config, 3, "dimmer");
    config = changeSlotModule(config, 4, "usb_c_outlet");
    config = changeGangCount(config, 2);
    expect(config.slots).toEqual([
      { slotNumber: 1, moduleTypeCode: "switch" },
      { slotNumber: 2, moduleTypeCode: "outlet" },
    ]);
  });

  it("changing one slot does not change other slots", () => {
    let config = changeGangCount(createDefaultConfiguration(), 3);
    config = changeSlotModule(config, 2, "outlet");
    expect(config.slots[0]?.moduleTypeCode).toBe("dimmer");
    expect(config.slots[1]?.moduleTypeCode).toBe("outlet");
    expect(config.slots[2]?.moduleTypeCode).toBe("switch");
  });

  it("accepts all four module types in every slot", () => {
    let config = changeGangCount(createDefaultConfiguration(), 4);
    const codes = [
      "usb_c_outlet",
      "switch",
      "outlet",
      "dimmer",
    ] as const;
    codes.forEach((code, index) => {
      config = changeSlotModule(config, index + 1, code);
    });
    expect(config.slots.map((slot) => slot.moduleTypeCode)).toEqual([...codes]);
    expect(
      validateConfiguration(config, {
        moduleOptions: MODULE_OPTIONS,
        finishSchemeCodes: FINISHES,
      }),
    ).toEqual([]);
  });

  it("applies finish globally", () => {
    const config = changeFinishScheme(
      changeGangCount(createDefaultConfiguration(), 3),
      "steel",
    );
    expect(config.finishSchemeCode).toBe("steel");
    expect(toResolvePayload(config).finish_scheme).toBe("steel");
  });

  it("builds resolve payload from UI state without assignment_state_id", () => {
    const config = changeGangCount(createDefaultConfiguration(), 2);
    const payload = toResolvePayload(config);
    expect(payload).toEqual({
      gang_count: 2,
      modules: [
        { slot_number: 1, module_type: "dimmer" },
        { slot_number: 2, module_type: "switch" },
      ],
      finish_scheme: "brass",
    });
    expect(payload).not.toHaveProperty("assignment_state_id");
  });
});

describe("buildAssemblyStateName", () => {
  it("normalizes module codes from geometry only (no finish)", () => {
    let config = changeGangCount(createDefaultConfiguration(), 3);
    config = changeSlotModule(config, 1, "switch");
    config = changeSlotModule(config, 2, "outlet");
    config = changeSlotModule(config, 3, "usb_c_outlet");
    config = { ...config, finishSchemeCode: "steel" };
    expect(buildAssemblyStateName(config)).toBe("switch-outlet-usb-c");
  });
});
