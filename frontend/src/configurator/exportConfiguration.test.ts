import { describe, expect, it } from "vitest";
import {
  changeGangCount,
  changeSlotModule,
  createDefaultConfiguration,
} from "./assemblyConfigurationService";
import { buildExportPayload } from "./exportConfiguration";
import type { RenderState } from "../types";

describe("buildExportPayload", () => {
  it("exports the complete structured multi-slot assembly", () => {
    let configuration = changeGangCount(createDefaultConfiguration(), 4);
    configuration = changeSlotModule(configuration, 1, "usb_c_outlet");
    configuration = changeSlotModule(configuration, 2, "switch");
    configuration = changeSlotModule(configuration, 3, "outlet");
    configuration = changeSlotModule(configuration, 4, "dimmer");
    configuration = {
      ...configuration,
      finishSchemeCode: "steel",
    };

    const payload = buildExportPayload(configuration, null);

    expect(payload).toMatchObject({
      schema_version: 1,
      gang_count: 4,
      finish_scheme_code: "steel",
      slots: [
        { slot_number: 1, module_type_code: "usb_c_outlet" },
        { slot_number: 2, module_type_code: "switch" },
        { slot_number: 3, module_type_code: "outlet" },
        { slot_number: 4, module_type_code: "dimmer" },
      ],
    });
    expect(payload).not.toHaveProperty("assignment_state_id");
  });

  it("keeps debug geometry/materials separated from the public payload", () => {
    const configuration = createDefaultConfiguration();
    const renderState = {
      assets: [{ asset_key: "plate.1gang", file: "/assets/glb/1gang_plate.glb" }],
      missing_assets: [],
      material_assignments: { primary_metal: "brass_brushed" },
      bom: [],
    } as unknown as RenderState;

    const payload = buildExportPayload(configuration, renderState);
    expect(payload).toHaveProperty("debug.assets");
    expect(payload).not.toHaveProperty("assets");
  });
});
