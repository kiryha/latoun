# Latoun 004 — native design-review models

Scope authorized 2026-11-04: construct the revised artistic draft through parts and assemblies, preserving unresolved engineering details. These models support appearance review, factory assessment and quotations; they are not a manufacturing release.

Revision 004 supersedes the earlier 002 inspection. Its explicit nominal profiles govern, including the 70 x 120 plate, 34 x 70 insert face, 0.25 per-side reveal, 5-wide variable-length switch slot and seated decorative heads. The original inputs remain unchanged.

## Model organization

Native output directory: `output/solidworks/004`.

| File stem | Native construction | Quantity/use |
|---|---|---|
| Common_Plate_004 | Three successive two-section lofts through the four specified outer stations; loft-cut window; two-circle fixing-hole extruded cut | Shared, 1 per assembly |
| Rear_Ring_004 | Two rounded rectangular contours, extruded 2 mm | Shared, 1 per assembly |
| Fixing_Head_004 | Three hexagonal section lofts and cross-recess loft cut | Shared, 2 per assembly |
| Switch_Insert_004 | Rounded-rectangle taper loft and slot loft cut | Toggle, 1 |
| Switch_Bezel_004 | Rounded-rectangle taper loft and slot loft cut | Toggle, 1 |
| Switch_Stem_004 | Rounded rectangular extrusion and transverse diameter-1 cut | Toggle, 1 |
| Switch_Grip_004 | Rounded rectangular extrusion with cylindrical end shaping | Toggle, 1 |
| Dimmer_Insert_004 | Rounded-rectangle taper loft | Dimmer, 1 |
| Dimmer_Base_004 | Native revolved taper, diameter 24 to 17, Z=3..7 | Dimmer, 1 |
| Dimmer_Collar_004 | Native revolved cylinder, diameter 14, Z=6..11 | Dimmer, 1 |
| Dimmer_Grip_004 | Native twisted sweep of 40 smooth cosine flute splines; two short end-break lofts | Dimmer, 1 |
| Dimmer_Cap_004 | Native revolved taper plus an integral extruded L | Dimmer, 1 |

There are 12 unique part files. The saved toggle assembly contains 8 component instances and 7 lock mates; the dimmer contains 9 instances and 8 lock mates. The collar is retained separately from the fluted grip to preserve and expose the unresolved source stack overlaps. The raised L is a feature of the cap, not a separate manufactured component. This is a provisional engineering split, not a released BOM.

## Editing

The feature tree contains native sketches, dimensions, lofts, extrusions, cuts, revolves and a sweep. No mesh-derived faceted solid was imported. Important features and section sketches are named by their purpose and dimensions. Most analytic sketches are fully defined using native dimensions and relations. The first dimmer-insert section sketches remain underdefined; their intended geometry and loft are preserved and can be edited normally.

The cosine-flute and traced-L sketch coordinates are fixed to preserve the supplied decorative profile. Their native sweep/loft/extrusion features remain editable. Suppress those decorative features or edit their source sketches as needed. Re-running scripts uses the supplied parameters and refuses to overwrite an existing design file.

Coordinates use millimeters in the scripts and meters in SOLIDWORKS API calls. The common datum is the center of the plate rear face: +X right, +Y up, +Z toward the user. Actuator parts use local X/T/S coordinates with S represented by part Z. Their assembly placement applies +25 degrees about X and Z=-10 mm.

The assemblies are static design-review arrangements. The plate is grounded; minimal rigid position mates preserve the source relationships, and the grip is mated to the stem. The named reference pivot/pose/travel values in the toggle document record the placeholder study. They do not drive a finished mechanism or constitute working travel limits. Suppress or replace the review mates when developing the mechanism.

## Validation evidence

The native-part smoke test passed, including save/reopen, fully defined sketch, native extrusion, body validity, dimensions and volume. Its evidence is in `output/verification/20261104_143343/verification.json`.

All 12 native parts and both assemblies have been saved and reopened successfully. Each part contains one valid solid and checked native features with no rebuild errors. The assemblies have one fixed plate each, fully resolved references, preserved component transforms and healthy mates. Isometric previews were inspected against the reference layout.

Initial component reports are in `output/solidworks/004/parts_validation.json`; the final exact-envelope checks are in `final_geometry_validation.json`. All nominal envelopes match, including the 70 x 120 x 3 plate. The fluted grip additionally passed sampled closest-surface comparisons to the specified cosine profile and positive 45-degree twist. Assembly validation reports are saved alongside the native assemblies.

The only detected positive-volume interferences are the retained stem/grip overlap (23.490 mm³), dimmer base/collar overlap (153.938 mm³), and collar/grip overlap (461.814 mm³). Coincident contacts were excluded from interference reporting. This checks the displayed static pose, not a travel sweep.

`GetBodyBox` can return a padded approximate box; later validation uses six `GetExtremePoint` calls for the exact directional envelope. Source overlaps are reported rather than repaired. See [assumptions_004.md](assumptions_004.md) for the retained open details and cosmetic approximations.

## Handoff

All 14 AP214 STEP exports (12 parts and 2 assemblies) were reopened in SOLIDWORKS 2026. Solid validity, solid counts and aggregate volumes passed; individual part envelopes also passed. The assembly exports contain 8 and 9 solids respectively. Reports are in `output/step/004/step_validation.json`. Actual SOLIDWORKS 2016 import was not tested because that version is unavailable here. STEP transfers solid geometry, not native feature history or mates.

`output/Latoun_004_review_package.zip` contains both native assemblies and all referenced parts together, the STEP exports, previews, validation reports and these notes. Extract the whole package before opening an assembly. Keep the SLDPRT files beside the SLDASM files. Use the STEP assemblies for the older factory CAD environment.
