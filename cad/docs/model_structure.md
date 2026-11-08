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

## SLA fit-test files

`output/004/` is a print preparation derived from the saved `003` models, not a replacement for the engineering assembly. It contains four single-solid items, each as SLDPRT, STEP and STL:

- `1gang_print_plate`: metal plate with both decorative heads joined; silicone excluded.
- `1gang_print_inner`: switch insert and raised collar joined.
- `1gang_print_actuator`: stem and grip joined.
- `1gang_print_dimmer`: dimmer insert, base, neck, fluted grip and cap joined.

The heads are lowered 0.30 mm to overlap the plate. The dimmer cap is lowered 0.002 mm to close its tiny source gap and join the grip. No fit clearance or resin shrink compensation is added, as requested. These files are for an SLA fit test; actual fit depends on the printing and curing process. STL coordinates are in millimeters, with the original assembly positions retained. The print provider can choose orientation and supports.

The native print files contain copied analytic source solids and Combine features. Their original sketch histories remain in `003`; the print files are self-contained and do not link back to it.

## Files to use

Output lives in `D:/projects/latoun/cad/output/<version>/`. The current version is `003`, built from `inputs/005/`. Earlier versions remain unchanged. Each version contains `solidworks/`, `step/`, `stl/` and `validation/`.

Open `solidworks/1gang_switch.SLDASM` or `solidworks/1gang_dimmer.SLDASM` inside the chosen version to review a complete product. Keep assembly references within that version so older versions remain independent.

For the manufacturer, the version's `step/` folder contains the same six basenames: four assets and two complete products. Send the complete product STEP for an overall quotation, and individual assets when discussing them separately. STEP AP214 was chosen for the manufacturer's SOLIDWORKS 2016. Import is checked in SOLIDWORKS 2026; 2016 is unavailable here.

The version's `validation/` folder contains internal JSON check results. These do not need to accompany a factory handoff.

## Houdini

The version's `stl/` folder contains the four manifest assets. Load the plate, screws and chosen module through File SOPs and merge them. Their coordinates include the fixing positions and lever pose, so they align without further placement.

STL meshes contain no UVs, materials or internal body names. Keep the native files for CAD editing. One numeric unit equals one millimeter; apply an import scale of `0.001` if the Houdini scene uses meters.

## Naming

Assets use the exact manifest basename, such as `1gang_slot1_switch`. Complete products use `1gang_switch` and `1gang_dimmer`. Internal bodies use descriptive names such as `switch_grip` and `1gang_plate_silicone`.

A model keeps the same basename across native and exported formats. Versions belong in the three-digit parent folder, never in filenames. Preserve earlier version folders; do not overwrite them when producing the next version.
