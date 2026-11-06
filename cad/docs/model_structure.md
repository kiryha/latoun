# Product and file structure

A complete wall plate combines three assets: the plate, its fixing heads, and a switch or dimmer module. The native files follow the grouping and names in the [Latoun asset manifest](../../config/wall_plates/asset_manifest.json).

Each asset is one **part file** (`.SLDPRT`) containing several separate solid bodies. A body is a solid inside a part file; it does not require another file. This keeps the file structure small while preserving the distinction between metal, silicone, and control components.

```text
1gang_switch.SLDASM
  1gang_plate.SLDPRT          metal plate + silicone ring
  1gang_plate_screws.SLDPRT   two fixing heads
  1gang_slot1_switch.SLDPRT   insert + bezel + stem + grip

1gang_dimmer.SLDASM
  1gang_plate.SLDPRT          shared plate asset
  1gang_plate_screws.SLDPRT   shared fixing asset
  1gang_slot1_dimmer.SLDPRT   insert + base + collar + grip + cap
```

There are **four part files and two assembly files** in each version's `solidworks/` folder. Assemblies reference the part files, so keep all six together. Native sketches and modeling features remain editable inside each part. The second fixing head is a body copy driven by the first head's geometry.

Grouping is for product organization, not a manufacturing decision. Bodies remain separate even where the draft overlaps. The controls retain a static review pose; this is not a simulation of mechanism travel. Only the existing one-gang switch and dimmer are modeled.

## Files to use

Output lives in `H:/@transfer_vdi_pc/latoun/output/<version>/`. The latest completed version is `002`; the next build is `003`. `001` holds the previous backup. Each version contains `solidworks/`, `step/`, `stl/` and `validation/`.

Open `solidworks/1gang_switch.SLDASM` or `solidworks/1gang_dimmer.SLDASM` inside the chosen version to review a complete product. Keep assembly references within that version so older versions remain independent.

For the manufacturer, the version's `step/` folder contains the same six basenames: four assets and two complete products. Send the complete product STEP for an overall quotation, and individual assets when discussing them separately. STEP AP214 was chosen for the manufacturer's SOLIDWORKS 2016. Import is checked in SOLIDWORKS 2026; 2016 is unavailable here.

The version's `validation/` folder contains internal JSON check results. These do not need to accompany a factory handoff.

## Houdini

The version's `stl/` folder contains the four manifest assets. Load the plate, screws and chosen module through File SOPs and merge them. Their coordinates include the fixing positions and lever pose, so they align without further placement.

STL meshes contain no UVs, materials or internal body names. Keep the native files for CAD editing. One numeric unit equals one millimeter; apply an import scale of `0.001` if the Houdini scene uses meters.

## Naming

Assets use the exact manifest basename, such as `1gang_slot1_switch`. Complete products use `1gang_switch` and `1gang_dimmer`. Internal bodies use descriptive names such as `switch_grip` and `1gang_plate_silicone`.

A model keeps the same basename across native and exported formats. Versions belong in the three-digit parent folder, never in filenames. Preserve earlier version folders; do not overwrite them when producing the next version.
