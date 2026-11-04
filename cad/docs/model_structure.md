# Latoun 002: inspection and proposed CAD structure

Status: Phase 1 inspection and modeling proposal, 2026-11-04. Product CAD has not been constructed or validated. This document is not a manufacturing release.

## Sources and workspace

The working project is `D:/projects/latoun`. The requested `C:/projects/latoun_cad` and original OneDrive reference directory were unavailable. References were found in the existing `inputs/002` folder (plural); retain that folder unchanged rather than duplicate or rename it. No pre-existing AGENTS.md was found in the checked workspace/ancestor locations.

The complete disk and archive listing is in [reference_inventory.md](reference_inventory.md). The package contains:

| Sheet | Drawing content |
|---|---|
| 01_switch_assembly_002.jpg | Front, left and isometric switch assembly; pose and envelope |
| 02_dimmer_assembly_002.jpg | Front, left and isometric dimmer assembly; envelope |
| 03_common_plate_002.jpg | Plate, rear ring, fixing centers and holes |
| 04_plate_insert_sections_002.jpg | Plate edge and insert taper; five section stations |
| 05_switch_insert_bezel_002.jpg | Insert, bezel and changing slot section; stem overlap |
| 06_switch_lever_pivot_002.jpg | Straightened lever, pivot and local coordinate system |
| 07_dimmer_stack_002.jpg | Insert, base, collar, grip, cap and raised L positions |
| 08_dimmer_helical_grip_002.jpg | Flute count, twist, crest/root diameters and phase |
| 09_fixing_heads_002.jpg | Decorative hex heads and nonstandard cross recess |

The nine sheets are 4200 x 2970 JPEGs. `sketch_overview_002.jpg` is a montage. `measurements_002.json` holds bounds for 14 connected mesh components and hashes of four original OBJs. Those OBJ files are not included. `READ_ME_002.txt` defines coordinates, scale and known defects. The ZIP contains byte-identical copies of the nine sheets, README and JSON, plus 112 ASCII R12 DXFs and `profile_segments_002.csv`. ZIP CRC verification passed.

DXFs contain planar LINE segments sampled from triangulated source geometry, in millimeters. They are neither analytic CAD profiles nor production toolpaths. Their coordinates and the CSV should guide small constrained sketches and fitted curves; importing every segment into the final solid would preserve tessellation artifacts.

The eight `work/*.py` files generate/analyze the references. They depend on original OBJ files, an external `inspect_geometry` module, NumPy and Pillow; they are not SOLIDWORKS build scripts and were inspected without execution. `work/switch_preview.jpg` and `work/test_render.jpg` are supplementary previews, not dimension authorities.

An existing `us_mcm_nGang_plate.SLDPRT` and a corresponding lock file are present at project root. Their design contents have not been evaluated; do not treat them as validated output from this task or overwrite them.

## Controlling geometry

The user selected a nominal **70 x 120 mm plate**, preserving other dimensions. Keep the assembly origin at the plate rear-center; X right, Y up, Z outward. Plate spans Z=0..3 mm; ring spans Z=-2..0 mm. Preserve hole centers, opening, inserts and module positions. Implement the size correction symmetrically in the outer plate boundary, without global scaling. Exact propagation through the outer taper/blends must be documented during the profile fit.

All other numbers on these sheets are explicit measurements of an appearance mesh, not tolerance specifications. See [assumptions.md](assumptions.md) for the dimension register, derivations and unresolved interfaces.

## Proposed assemblies and parts

Use two assemblies, `Latoun_Toggle_002.SLDASM` and `Latoun_Dimmer_002.SLDASM`, referencing shared parts. They are alternative products, not two modules installed simultaneously in the same one-gang opening.

The following is a provisional 11-part-file structure. It does not claim that mesh separation proves manufacturing separation. Material, finish, retention and assembly sequence may justify later consolidation.

| Proposed part | Use | Minimal native features and rationale |
|---|---|---|
| Common_Plate | Both | Centered dimensioned blank/extrusion, independently controlled X/Y outer bevels or drafted cuts, tapered rounded-rectangle opening, two through holes using a linear pattern, late edge blends. Plate outer taper is not uniform in X and Y. |
| Rear_Ring | Both | Concentric rectangular contours, 2 mm extrusion, fitted edge treatment. Preserve separately until integral rear rim versus attached ring is decided. |
| Fixing_Head | Two instances in each | Hex extrusion, edge chamfer/blend, shaped cross-recess cut. Head only; no invented shank/thread or standard-drive designation. |
| Switch_Insert | Toggle | Constrained rounded-rectangle profile, tapered extrusion or drafted cuts, slot with angled end walls and small edge blends. |
| Switch_Bezel | Toggle | Tapered rounded-rectangle boss and matching variable-length slot. Keep separate provisionally; a single machined insert/bezel is a candidate if materials/finish permit. |
| Switch_Stem | Toggle | Rounded rectangular section extrusion along local S; transverse 1 mm pivot hole. No invented pin or rear mechanism. |
| Switch_Grip | Toggle | Rounded square section, axial extrusion and fitted end shaping. Inspect local sections before choosing end cuts/fillets; not assumed rotationally symmetric. Grip/stem attachment is unknown. |
| Dimmer_Insert | Dimmer | Same dimensional family as switch insert but without its slot. Separate part avoids an assembly-context dependency; no invented shaft hole. |
| Dimmer_Base | Dimmer | Revolved axial profile with fitted end blends; distinguish presumed stationary trim from rotating knob until mechanism is selected. |
| Dimmer_Knob | Dimmer | One turned core combining the collar and grip's underlying blank, followed by one helical flute cut patterned 40 times; end transitions fitted to supplied sections. Collar and body are coaxial overlapping mesh islands, not sufficient evidence of separate manufactured pieces. |
| Dimmer_Cap | Dimmer | Revolved cap plus raised L as a sketch/boss on the same part. Use the actual outline; a replacement font would alter the design. Cap/body joint remains unresolved. |

Keep the cap separate initially: its bottom is approximately 0.000803 mm forward of the grip end in the source, so blindly merging them requires changing geometry. The L overlaps the cap axially and can naturally be an integral feature. These are geometric observations, not validated joint designs.

For the helical grip, preserve the 40-flute decorative appearance in a detailed configuration. Derive a small analytic flute profile from the section and validate intermediate stations. A patterned swept cut should be tried first; a swept full section with controlled twist is a fallback if it better matches the actual profile. Avoid a generic knurl texture: the source explicitly has helical flutes. A simplified configuration may suppress flutes for assembly performance, while a manufacturing note records their specification. A note alone does not reproduce the requested detailed appearance or STEP geometry.

## Assembly relationships

- Ground Common_Plate at the assembly origin.
- Locate the ring and trim parts by stable datum planes, centerplanes and axial distances. Do not use tiny blend edges as mate references.
- Reuse the fixing-head part at X=0, Y=+/-41.5 mm, with source Z positions. Flag the gap rather than changing it automatically.
- Place the toggle pivot reference at (0,0,-10) mm with axis along X. Locate the lever in the shown 25-degree pose toward -Y using datum/angle mates. The angle is a reference pose, not a travel limit. Without a real pin/support, this is geometric placement only.
- Locate dimmer components concentrically along Z with explicit axial dimensions and logo orientation. Do not infer torque transfer, rotation limits, shaft retention or fixed-versus-rotating behavior from mesh islands.
- Retain source interferences in an initial reference reconstruction unless corrections are approved. Report them as unresolved design defects, not successful functional fits.

## Implementation and validation sequence

1. Complete the isolated COM native-feature test and document its outcome.
2. Fit straight segments, circular corners and end profiles to the DXF sections; log fitted parameters and maximum residuals. Obtain a reconstruction-deviation target before accepting approximate cosmetic surfaces.
3. Build common parts, then toggle and dimmer parts. Use mm for input and m for API calls; name sketches/features and use driving dimensions/relations. No mesh-to-faceted-B-rep conversion.
4. Rebuild each part; inspect every feature error, body count, body validity, dimensions and section residuals. Save/reopen before assembly.
5. Add minimal mates and check their state, component transforms, missing references, overlaps and toggle travel once functional limits are defined.
6. Compare against original section stations, with the approved plate-boundary correction accounted for separately.
7. Save native files under `output/solidworks`. Export AP214 STEP to `output/step`; reopen and compare units, body counts, bounds and volume. Test representative files in the manufacturer's SOLIDWORKS 2016 installation when available.

STEP communicates geometry; it does not carry the native SOLIDWORKS feature tree or assembly mates. Do not promise native 2026 feature editability in the factory's 2016 environment.

Keep implementation small: `scripts/build_parts.py` and `scripts/build_assembly.py` when construction begins, with a few shared helpers only if needed. Those product-build scripts have deliberately not been created in this inspection phase.
