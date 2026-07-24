import { describe, expect, it } from "vitest";
import {
  defaultBulkGenerateOptions,
  previewBulkGeneration,
} from "./assetManifestGenerator";
import {
  createDefaultEntry,
  suggestFilePath,
  suggestManifestKey,
} from "./assetManifestNormalization";
import { validateWorkingManifest } from "./assetManifestValidation";
import type { EditableManifestEntry, ModuleTypeOption } from "./types";

const MODULE_TYPES: ModuleTypeOption[] = [
  {
    module_type_id: 1,
    code: "switch",
    display_name: "Switch",
    is_active: true,
    is_customer_visible: true,
    sort_order: 10,
  },
  {
    module_type_id: 2,
    code: "dimmer",
    display_name: "Dimmer",
    is_active: true,
    is_customer_visible: true,
    sort_order: 20,
  },
  {
    module_type_id: 3,
    code: "outlet",
    display_name: "Outlet",
    is_active: true,
    is_customer_visible: true,
    sort_order: 30,
  },
  {
    module_type_id: 4,
    code: "usb_c_outlet",
    display_name: "USB-C Outlet",
    is_active: true,
    is_customer_visible: true,
    sort_order: 40,
  },
];

function row(
  key: string,
  value: EditableManifestEntry["value"],
  editState: EditableManifestEntry["editState"] = "unchanged",
): EditableManifestEntry {
  return {
    clientId: key,
    manifestKey: key,
    originalManifestKey: key,
    value,
    editState,
  };
}

describe("assetManifestGenerator", () => {
  it("generates 48 entries from an empty manifest", () => {
    const options = defaultBulkGenerateOptions(MODULE_TYPES);
    const preview = previewBulkGeneration(new Set(), options);
    expect(preview.toCreate).toHaveLength(48);
    expect(
      preview.toCreate.filter((item) => item.value.category === "plate"),
    ).toHaveLength(4);
    expect(
      preview.toCreate.filter((item) => item.value.category === "hardware"),
    ).toHaveLength(4);
    expect(
      preview.toCreate.filter((item) => item.value.category === "slot_module"),
    ).toHaveLength(40);
  });

  it("does not overwrite existing entries", () => {
    const options = defaultBulkGenerateOptions(MODULE_TYPES);
    const preview = previewBulkGeneration(new Set(["plate.1gang"]), options);
    expect(preview.toCreate).toHaveLength(47);
    expect(preview.conflictCount).toBe(1);
    expect(
      preview.toCreate.some((item) => item.manifestKey === "plate.1gang"),
    ).toBe(false);
  });

  it("suggests bare file names with unpadded slots", () => {
    const value = createDefaultEntry("slot_module", "usb_c_outlet");
    if (value.category !== "slot_module") throw new Error("expected slot");
    value.gang_count = 4;
    value.slot_position = 4;
    expect(suggestManifestKey(value)).toBe("module.4gang.slot4.usb_c_outlet");
    expect(suggestFilePath(value)).toBe("4gang_slot4_usb_c_outlet.glb");
  });
});

describe("assetManifestValidation", () => {
  it("accepts valid plate / hardware / slot module entries", () => {
    const result = validateWorkingManifest(
      [
        row("plate.1gang", {
          category: "plate",
          gang_count: 1,
          file: "1gang_plate.glb",
          is_active: true,
        }),
        row("hardware.1gang.plate_screws", {
          category: "hardware",
          hardware_type: "plate_screws",
          gang_count: 1,
          file: "1gang_plate_screws.glb",
          is_active: true,
        }),
        row("module.1gang.slot1.switch", {
          category: "slot_module",
          gang_count: 1,
          module_type: "switch",
          slot_position: 1,
          file: "1gang_slot1_switch.glb",
          is_active: true,
        }),
      ],
      MODULE_TYPES,
    );
    expect(result.ok).toBe(true);
  });

  it("blocks slot greater than gang count", () => {
    const result = validateWorkingManifest(
      [
        row("module.2gang.slot3.switch", {
          category: "slot_module",
          gang_count: 2,
          module_type: "switch",
          slot_position: 3,
          file: "2gang_slot3_switch.glb",
          is_active: true,
        }),
      ],
      MODULE_TYPES,
    );
    expect(result.ok).toBe(false);
    expect(result.errors.some((issue) => issue.message.includes("Slot 3"))).toBe(
      true,
    );
  });

  it("blocks duplicate active resolver identity", () => {
    const result = validateWorkingManifest(
      [
        row("module.2gang.slot1.switch", {
          category: "slot_module",
          gang_count: 2,
          module_type: "switch",
          slot_position: 1,
          file: "2gang_slot1_switch.glb",
          is_active: true,
        }),
        row("module.2gang.slot1.switch.alt", {
          category: "slot_module",
          gang_count: 2,
          module_type: "switch",
          slot_position: 1,
          file: "2gang_slot1_switch_alt.glb",
          is_active: true,
        }),
      ],
      MODULE_TYPES,
    );
    expect(result.ok).toBe(false);
  });

  it("warns for inactive duplicates", () => {
    const result = validateWorkingManifest(
      [
        row("module.2gang.slot1.switch", {
          category: "slot_module",
          gang_count: 2,
          module_type: "switch",
          slot_position: 1,
          file: "2gang_slot1_switch.glb",
          is_active: true,
        }),
        row("module.2gang.slot1.switch.alt", {
          category: "slot_module",
          gang_count: 2,
          module_type: "switch",
          slot_position: 1,
          file: "2gang_slot1_switch_alt.glb",
          is_active: false,
        }),
      ],
      MODULE_TYPES,
    );
    expect(result.ok).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  it("rejects file names that include a folder path", () => {
    const result = validateWorkingManifest(
      [
        row("plate.1gang", {
          category: "plate",
          gang_count: 1,
          file: "/assets/glb/1gang_plate.glb",
          is_active: true,
        }),
      ],
      MODULE_TYPES,
    );
    expect(result.ok).toBe(false);
  });
});
