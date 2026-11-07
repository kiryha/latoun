# Latoun Houdini scene guide

This guide explains how to navigate and extract the procedural design for the
[Houdini-to-drawings skill](skills/latoun-houdini-drawings/SKILL.md).
The [input handoff contract](input_handoff_prompt.md) defines the deliverables.
It is a scene map and extraction guide, not a second dimension register.

## Authority and verified scope

Houdini currently owns visual geometry. SOLIDWORKS is used for parametric
reconstruction, mechanical engineering and DFM. A newer scene or an explicit
owner decision can supersede this snapshot; re-evaluate rather than carrying
old numerical assumptions forward.

Verified on 2026-11-06:

- Scene: `switch_rnd_010.hiplc`.
- SHA-256: `014ff7607a89ef657d75c1f741f1a2280c80ae3ff5c177868ac8e45cdbf747d1`.
- Houdini evaluation: 22.0.466.
- Owner confirmed the current insert starting profile **34 x 67 mm**, superseding
  the earlier 34 x 70 request.
- Evaluation covered 38 manifest asset groups using 19 reusable provisional
  components. These are snapshot counts, not requirements for all future jobs.
- Electrical mechanisms are unselected. Materials, finishes and manufacturing
  tolerances remain unconfirmed.

Earlier CAD construction assumptions do not override the supplied 010 scene.
The current one-gang CAD reconstruction uses input 005; see
[design assumptions](assumptions.md) for its documented differences. A new
reference package does not automatically migrate or validate CAD models.

## Locations on the author's PC

| Resource | Verified location |
|---|---|
| CAD/application repository | `C:/Users/kiryha/OneDrive/dev/latoun` |
| Houdini project | `C:/Users/kiryha/OneDrive/projects/latoun/prod/3D` |
| Scene | `scenes/rnd/switch_rnd_010.hiplc` relative to the Houdini project |
| Supplied OBJ exports | `caches/assets/OBJ` relative to the Houdini project |
| Evaluated 005 handoff and scripts | `render/model_to_blueprint/005` relative to the Houdini project |
| Houdini Python executable | `C:/Program Files/Side Effects Software/Houdini 22.0.466/bin/hython.exe` |

These paths describe two existing locations with different roles; do not create
another checkout or synchronize them automatically. Resolve current paths on a
different host. Heavy reference packages are local inputs, not skill assets.
Follow the owner's output directory; never rerun a writer into 005 merely
because it is the example package.

## Units and coordinates

The owner uses **1 numeric scene unit = 1 mm**, irrespective of Houdini's
meter-oriented unit display.

The verified `EXPORT_XFORM_*` nodes apply uniform scale **0.001**. Supplied OBJs
exported through that branch therefore contain numeric meters and require
multiplication by **1000** to recover mm. Direct upstream SOP geometry already
has mm-sized coordinates and needs no multiplication. Recheck the export
transform for every new source; OBJ does not carry a reliable unit declaration.
CAD-return STLs can already be numeric mm and must not inherit the OBJ conversion.

The product frame is right-handed:

- Origin: center of the metal plate's rear face, at Z=0.
- +X: right; +Y: up; +Z: toward the user.
- The backing extends behind this datum to Z=-2 in this snapshot.

The handoff uses column vectors, translation in the final matrix column, and
last row `[0,0,0,1]`. Houdini matrices commonly operate on row vectors; an
actual Houdini matrix must be converted appropriately. Bake unit conversion
into component-local geometry before creating rigid instance matrices.
For a source-local origin `o`, use `p_local = p_source - o` and account for
that origin once in placement.

## Stage and controls

SOP Create container: `/stage/ASSEMBLY`.

Geometry network: **`/stage/ASSEMBLY/sopnet/create`**.
All node names below are relative to that network.

The controller is named **`Controls`** (plural). Parameter spellings matter:

| Parameter | Meaning in the verified scene |
|---|---|
| `gung_nuber` | Gang count, currently 1; preserve this misspelling in API calls |
| `current_slot` | One-based selected module slot, currently 1 |
| `plate_width` | Per-gang width/pitch, currently 70 |
| `plate_height` | Plate height, currently 120 |
| `box_fastener_dist` | Vertical fixing-center pitch, currently 83 |
| `plate_depth` | Metal face depth, currently 3 |
| `plate_radius_out` | Input to the outer profile bevel, currently 1 |
| `metal_bevel` | Metal edge bevel distance, currently 0.15 |

`plate/sizex` is an expression multiplying gang count by plate width.
`module_points` creates the gang centers:
`x_i = (i - (n-1)/2) * pitch`, for zero-based `i`.

The saved `switch_parts/input` is 1. Its inputs are:

| Index | Preview module |
|---|---|
| 0 | `get_assembly_dimmer` |
| 1 | `get_assembly_switch` |
| 2 | `get_assembly_outlet` |

`merge_full_scale_assembly` combines plate, screws and `switch_parts`.
`full_scale_preview` is its output; `assembly` is the final SOP output.
The saved preview shows the selected module branch/slot. It is not an inventory
of all devices or all gang combinations.

## Manifest outputs and instancing

| Output SOP | Manifest group |
|---|---|
| `us_mcm_nGang_plate` | `Ngang_plate` |
| `us_mcm_nGang_plate_screws` | `Ngang_plate_screws` |
| `us_mcm_nGang_slotN_dimmer` | `Ngang_slotS_dimmer` |
| `us_mcm_nGang_slotN_switch` | `Ngang_slotS_switch` |
| `us_mcm_nGang_slotN_outlet` | `Ngang_slotS_outlet` |

Read IDs and basenames from the current manifest rather than generating IDs by
string convention. The verified manifest contains the anomalous ID
`module.4gang.slot1outlet`; its basename is `4gang_slot1_outlet`.
Preserve it unless the manifest itself changes.

The module loops `foreach_end1`, `foreach_end2` and `foreach_end4` use
single-pass selection for the current slot. Set gang and slot in memory before
cooking each requested variant. Merely renaming a one-gang mesh does not
produce a multi-gang plate.

`box_fasteners_points` supplies two fixing centers per gang, at each slot X
and Y=+/-41.5 in this snapshot. `foreach_end3` and `transform24` produce the
complete screws group: 2, 4, 6 or 8 head instances. Check the cooked count
rather than inferring duplicate copies from the node names.

Export scaling nodes are `EXPORT_XFORM_PLATE`, `EXPORT_XFORM_DIMMER`,
`EXPORT_XFORM_SWITCH`, `EXPORT_XFORM_PLATE_SCREWS` and `EXPORT_XFORM_OUTLET`.
Avoid cooking `export_obj_*` file nodes or executing `export_GLTF_*` ROPs
during investigation. Read their upstream geometry.

## Component extraction map

These semantic groups were used in 005. They are provisional physical splits,
not a released bill of materials. Use scene connectivity and active branches
to confirm them in a new revision.

| Component ID | Source SOP | Local frame / product placement in 010 |
|---|---|---|
| `plate_face_Ngang` | `normal2` | Source frame; identity |
| `plate_back_Ngang` | `normal6` | Source frame; identity |
| `screw_head` | `out_screw_D` | One head at source origin; instance at fixing X/Y and Z=3.28183 |
| `insert_dimmer` | `out_inner_panel` | Source frame; translate slot X |
| `insert_switch` | `out_inner_plate` | Source frame; translate slot X |
| `insert_outlet` | `normal13` | Source frame; translate slot X |
| `switch_collar` | `normal16` | Subtract [0,0,7] for local mesh; instance [slot X,0,7] |
| `switch_grip` | `boolean13` | Source lever frame; instance [slot X,0,-12] in neutral pose |
| `switch_stem` | `boolean14` | Same lever frame and pose |
| `dimmer_base` | `normal8` | Source Z already retained; translate slot X only |
| `dimmer_neck` | `tube6` | Source Z already retained; translate slot X only |
| `dimmer_grip` | `actuator_WATCHES` | Translate slot X and `transform22/tz` |
| `dimmer_cap` | `merge4` | Includes logo; translate slot X and `transform23/tz` |

Plate face/back are extracted separately for each gang count. The logo remains
with the cap despite disconnected/open topology. Do not split every polygon
island into a manufactured component.

### Plate and insert construction

`plate -> reverse1 -> polybevel2` defines the rear construction contour.
`transform16` creates the front contour at Z=3 with X/Y scale 0.93/0.962;
`skin2 -> reverse4` joins the sections. Consequently, front corners are
anisotropically scaled, not necessarily constant-radius circles.

`plate_slot -> polybevel3 -> out_plate_slot_shape` defines the insert contour.
`transform26 -> out_inner_panel_nobevel -> polybevel25 -> normal3` makes the
tapered, edge-treated insert. Its pre-edge-treatment stations are 34 x 67 at
Z=3 and 38 x 71 at Z=0. `get_slot_shape_1` references the same unrounded
insert for the plate opening cutter.

This explains why nominal construction dimensions and mesh bounds differ.
For example, a 70 x 120 rear plate contour becomes approximately 69.8445 x
119.8518 in the finished one-gang mesh. This is not evidence of a global
unit-conversion error. Do not label a finished extremum as the original contour.

The rear backing comes from the inward-offset rectangular loops
`polyexpand2d2` and `polyexpand2d3`, followed by `skin1`,
`polyextrude4` and `polybevel1`.

### Switch construction and pose

The active output uses **`out_switch_actuator_B`**.
`out_switch_actuator_A` is another branch, not the selected asset geometry.

- `switch_cap_shape -> polybevel31 -> extrude_taper` builds the collar.
- `switch_cap_shape1/2 -> polybevel33/34 -> crosssectionsurface2` builds
  `out_actuator_cutter`, shared by insert and collar.
- Cutter stations: 4.1 x 18.5 at Z=-0.81 and 4.1 x 27.5 at Z=7.6.
- `boolean13` intersects the rounded grip prism with `tube9`; that cylinder
  shapes the grip rather than representing a drilled hole.
- `boolean14` subtracts the pivot-hole cutter `tube11` from the stem.
- `merge19 -> ON-OFF -> adjust_actuator_POSITION` places the moving pieces.
  The saved rotation is [0,0,0], the local pivot is [0,0,2], and the subsequent
  translation is [0,0,-12]. Thus the provisional product pivot is [0,0,-10].
  For a changed rotation, compose the complete pivoted transform; adding
  translation alone is valid only for this verified neutral pose.

The earlier 25-degree pose and approximately 0.496 mm interference are not
requirements of this snapshot. Certified mechanism selection must establish
the actual pivot and travel.

### Dimmer and outlet

`switch1` chooses the dimmer design, independently of `switch_parts`.
Saved input 0 selects `actuator_round`; input 1 is `actuator_square`.
The round assembly currently uses `actuator_WATCHES`, not `actuator_MUSIC`.

`circle_dimmer_actuator1` starts with 80 vertices at radius 8. Alternating
vertices are scaled by 0.95, producing 40 peaks and 40 valleys.
`bevel_bottom2` and `bever_top2` treat the profile; `polyextrude17`
extrudes it 20; `polybevel26` treats the ends; `twist1` twists +46 degrees
about +Z. Positive rotation was verified as counterclockwise viewed from +Z
toward the origin. Preserve the sampled phase and profile rather than inventing
a sinusoidal flute function.

`merge4` combines cap and logo. The logo branch includes a scale of 10 in
`transform8`; it is shape construction, not a second instance unit conversion.

Outlet cutters come from `contact_hot`, `contact_netural` (source spelling),
edited `circle2`, and `out_NEMA_5-15R`. `boolean6 -> polybevel28 -> normal13`
produces the insert. The node name does not establish certified dimensions
or electrical compliance.

## Useful profiles and known limitations

Profile extraction points:

| Profile | Source SOP |
|---|---|
| Insert front contour | `out_plate_slot_shape` |
| Tapered switch opening | `polybevel33`, `polybevel34` |
| Dimmer flute section | `bever_top2` |
| Logo | `font1`, with downstream construction transforms recorded separately |
| Outlet apertures | `out_NEMA_5-15R` |

The 005 package records exact ordered source polygon vertices as sampled
contours, not exact splines or proven analytic arcs. Sampling error relative
to an imagined smooth surface is unknown.

Known findings to recheck, not automatically correct:

- Plate opening and insert use the same nominal taper: no defined fit clearance.
- Head underside Z=3.28183 versus nominal plate front Z=3 leaves a 0.28183 gap.
- Stem has removed end faces; outlet and some multi-gang plate outputs have
  open/non-manifold topology; cap/Logo geometry is not a validated united solid.
- `polybevel15` contains fixed point-number edge selections. Topology changes
  with gang count, so the intended hole-edge treatment needs procedural groups.
- Dimmer pieces and switch grip/stem retain overlapping visual envelopes.
  Physical split, shaft passage, retention and joining details are unfinished.
- The supplied `1gang_slot1_outlet.obj` was empty; some other OBJ exports
  differed from the scene in counts or bounds. Do not treat the folder as a
  synchronized snapshot or mix its old parts into the evaluated scene silently.

## Reusing the verified implementation

Under the local 005 package, `_work/` contains:

| Script | Purpose |
|---|---|
| `extract_scene.py` | Parameter/expression extraction, semantic meshes, profiles and variant cooking |
| `geometry_details.py` | Supporting bounds, operation parameters and twist-direction evidence |
| `build_design.py` | CAD recipes, provenance, instances, source comparisons and issues |
| `drawings.py` | ReportLab drawings from the handoff and extracted mesh arrays |
| `render.py`, `model.py` | Software orthographic renderer and small shared configuration |
| `validate_package.py` | Delivered-file integrity and source-preservation checks |

Reuse this implementation when available rather than inventing a generic
converter. It is **scene-specific**, with hardcoded paths, recipes, dimensions,
page layouts and 005 counts. It is not a drop-in command for the next revision.
Copy/adapt only required scripts into the newly authorized working directory,
update their paths and changed source assumptions, and derive validation
expectations from the new inputs. If the local package is absent, ask for its
location or use the contract and this map; do not invent an installed generator.

Houdini 22 triangulation was performed with the `divide` SOP verb using
`usemaxsides=1`, `numsides=3`; the parameter is not named `maxsides`.
A SOP transform does not expose the OBJ-node `parmTransform()` method used by
some examples. Read actual SOP transform parameters and their order/pivot, or
use a verified transform extraction method.

Only the Houdini extraction steps need `hython`. JSON generation, raster views,
PDF creation and checks use ordinary Python with NumPy, Pillow, ReportLab and
pypdf; Poppler renders PDFs for visual inspection. Avoid assuming the same
packages are installed in both Python environments.

Restricted execution caused procedural nodes to exit even though simple grids
cooked successfully. Evaluation succeeded through the normal approved execution
route. A silent process exit is not proof that the source geometry is invalid.

The 005 checks matched all 38 assembled point sets to independently cooked
outputs within 0.0001 mm, using spatial matching rather than unstable sorting.
The largest observed difference was about 0.00000382 mm. These are numerical
comparison results, not production tolerances or proof of mechanical readiness.
See that package's `design.json` for the numerical findings instead of
maintaining another dimension register here.
