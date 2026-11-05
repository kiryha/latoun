# Product and file structure

## How a product is assembled

SOLIDWORKS stores an individual component in a **part file** (`.SLDPRT`). An **assembly file** (`.SLDASM`) references those parts and records their positions and relationships. Multiple assemblies can reuse the same part file. An assembly therefore needs its referenced parts beside it when shared.

We currently have two complete product assemblies: a toggle switch and a dimmer. Both reuse the outer plate, rear ring and decorative fixing heads. Each has its own insert and controls.

```text
Wall-plate product
├── Shared parts
│   ├── Outer plate
│   ├── Rear ring
│   └── Decorative fixing heads (two copies of one part)
├── Switch version
│   ├── Insert — fills the plate opening
│   ├── Bezel — surrounds the lever opening
│   ├── Stem — carries the lever
│   └── Grip — the part touched by the user
└── Dimmer version
    ├── Insert — fills the plate opening
    ├── Base — tapered transition to the plate
    ├── Collar — intermediate section behind the grip
    ├── Grip — fluted rotating control
    └── Cap — front end, including the raised L
```

This division lets us reuse common components and develop the controls independently. It is a proposed component breakdown; the factory may recommend combining or separating parts once the mechanism and manufacturing process are chosen.

## Which files to open

The current models are in `output/solidworks/`:

| Product | Assembly | Referenced parts |
|---|---|---|
| Toggle switch | `1gang_switch.SLDASM` | `1gang_plate`, `1gang_rear_ring`, `plate_fixing_head`, plus the four `switch_*` parts |
| Dimmer | `1gang_dimmer.SLDASM` | The same shared parts, plus the five `dimmer_*` parts |

Part files use the `.SLDPRT` extension. The assemblies hold the controls in the illustrated position so the appearance can be reviewed. Movement and functional connections will be developed with the mechanism.

For factory exchange, use the corresponding assembly STEP file in `output/step/`. STEP carries the solid geometry; the SOLIDWORKS files retain the editable construction and assembly relationships. AP214 was chosen for the factory's SOLIDWORKS 2016 environment. The exports were reopened in 2026; import in 2016 has not been tested here.

## Bringing parts into Houdini

Use the STL files in `output/houdini/`, one per unique part, with the same base names as the SOLIDWORKS files. Load them through a File SOP. All exported parts were successfully loaded by the installed Houdini 22 geometry reader.

STL was chosen because SOLIDWORKS exports it directly and Houdini reads it using its bundled STL reader ([supported formats](https://www.sidefx.com/docs/houdini/io/formats/geometry_formats.html)). These are triangulated meshes for further visual work; use the STEP files for factory exchange. The meshes carry no UVs or materials.

Coordinates are preserved from the individual parts, with **one numeric unit equal to one millimeter**. STL does not store a unit definition. If your Houdini scene uses meters, apply a scale of `0.001` on import. The parts retain their own placement coordinates; placing the lever and making the second fixing head are assembly operations.

## Naming within the Latoun project

The [main project](../../README.md) describes wall plates as a plate, hardware and modules placed in slots. The current [configurator assets](../../frontend/public/assets/wall_plates/) use names such as:

- `1gang_plate.glb` — the outer plate for a one-gang layout.
- `1gang_plate_screws.glb` — its visible fixing hardware.
- `1gang_slot1_switch.glb` — the switch module in its first slot.
- `1gang_slot1_dimmer.glb` — the dimmer module in its first slot.

A configurator module can represent several physical CAD parts. Its slot number identifies placement; a reusable CAD part does not need a separate identity for each slot. Likewise, a GLB named `plate_screws` can contain multiple heads while CAD reuses one head part.

### CAD naming convention

Use lowercase names with underscores and the project's terms `plate`, `switch`, `dimmer` and `slot`. CAD filenames and output folders have no revision suffixes. Versioning is managed manually by the owner.

| Purpose | Example |
|---|---|
| Complete product assembly | `1gang_switch.SLDASM` |
| Plate sized for a layout | `1gang_plate.SLDPRT` |
| Reusable component within a module | `switch_grip.SLDPRT`, `dimmer_cap.SLDPRT` |
| Reusable fixing component | `plate_fixing_head.SLDPRT` |
| Positioned module exported for the configurator | `1gang_slot1_switch.glb` |

Use a layout prefix on a component only when its geometry depends on that layout. Keep the same base name for a native model and its STEP export. The CAD names now follow this convention. Configurator assets keep their existing names; the two formats describe different levels of the same product.
