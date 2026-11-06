---
name: latoun-solidworks
description: Build or modify Latoun native SOLIDWORKS models on the licensed Windows VDI using the project's Python COM scripts. Use for geometry changes, manifest-aligned assembly structure, and validated STEP or STL exports.
---

# Latoun SOLIDWORKS modeling

Work in the `cad/` directory containing `AGENTS.md`, `scripts/` and `inputs/`.
Read its `AGENTS.md`, `docs/model_structure.md` and `docs/assumptions.md` first.
Keep all changes inside `cad/`; the application manifest is read-only.

## Choose the smallest appropriate operation

- **Structure or naming only:** preserve native features and geometry. The current structure is four multibody asset parts and two product assemblies; do not reintroduce external files for individual bodies.
- **Dimensions or shapes changed:** inspect the changed references and edit the relevant construction functions. Reuse only components whose geometry is unchanged.
- **Export only:** use the saved current native files and their validation reports. Do not rebuild geometry just to change export format.
- **Documentation only:** do not launch SOLIDWORKS.

The user handles backups and versions. Scripts refuse to overwrite native designs.
Before a geometry rebuild, confirm the intended output names are available. If they
are occupied and replacement has not been authorized, ask the user to back them up
or explicitly authorize replacement. Do not generate extra version suffixes.

## Read inputs and decide what they mean

The current source is `inputs/004/`: a nominal dimension register, drawing sheets
and a ZIP containing analytic DXFs and decorative profiles. The dimensions in
the register describe design intent; drawing pixels are not a precision source.

For future handoffs, read `design.json` first, then the relevant drawings and
profiles. The producer contract is [input_handoff_prompt.md](../../input_handoff_prompt.md).
The existing scripts do **not** parse that whole contract automatically. Translate
the affected data into the construction functions; avoid creating a generic CAD
framework to handle a small change.

For each changed feature, identify its source value, unit, coordinate frame and
status: intended, measured, derived, estimated or unknown. Compare nominal intent
with measured source geometry. Do not round, globally scale or invent critical
dimensions. Ask a concise question only when an unresolved value blocks the
requested result. Preserve documented placeholder interfaces and overlaps.

Keep reference data read-only. Preserve input meshes as comparison geometry;
do not turn polygon meshes into faceted CAD solids. For complex profiles, use
analytic curves where supported, or a documented smooth approximation.

## Where to make changes

| File | Responsibility |
|---|---|
| `scripts/build_parts.py` | Native multibody asset parts. `plate`, `ring`, `insert`, `bezel`, `stem`, `grip`, `base`, `collar`, `fluted_body`, `cap`, `head` construct their features. `JOBS` maps body builders; `BODY_JOBS` groups them into four files. |
| `scripts/profiles.py` | Reads decorative line profiles from the current input ZIP. Change this reader only when the source format changes. |
| `scripts/model_layout.py` | Manifest asset IDs, product membership and assembly placement. |
| `scripts/sw_helpers.py` | Verified COM binding, native feature helpers, save/reopen, geometry checks and session cleanup. |
| `scripts/build_assembly.py` | Builds the hierarchy and validates mates, paths and global leaf-component positions. |
| `scripts/validate_and_export.py` | Reference-based dimensional checks and AP214 export/reimport. |
| `scripts/export_houdini.py` | One assembled STL per manifest asset, in numeric millimeters. |

Use `rg` to locate the relevant function before reading the whole builder.
Dimensions are currently explicit numbers in construction functions, not a central
parameter database. Update related section profiles consistently. Update expected
dimensions in validation from the **input reference**, not merely to agree with
whatever geometry the implementation happens to produce.

Use revolved profiles for turned shapes, sketches and extrusions for prismatic
parts, and lofts only where sections change. Retain descriptive feature names and
native dimensions. Existing dimmer-insert sketches are partly underdefined;
decorative curves use fixed coordinates. Do not promise every feature is fully
constrained or driven by a single parameter.

## Product hierarchy and coordinates

`model_layout.py` reads `../config/wall_plates/asset_manifest.json` and checks the
four implemented one-gang asset names. The other manifest variants are not yet
modeled. Do not manufacture them by renaming existing geometry.

- `1gang_plate.SLDPRT`: metal plate and silicone ring (2 bodies).
- `1gang_plate_screws.SLDPRT`: original fixing head plus native body copy (2 bodies).
- `1gang_slot1_switch.SLDPRT`: insert, bezel, stem and grip (4 bodies).
- `1gang_slot1_dimmer.SLDPRT`: insert, base, collar, grip and cap (5 bodies).
- `1gang_switch.SLDASM` and `1gang_dimmer.SLDASM`: three asset parts each.

Each asset part is modeled in the same product coordinate system. The datum
is the plate rear-face center, with +Z toward the user. Layout entries currently
support X rotation plus Y/Z translation; see `pose_values` and `leaf_instances`.
Do not pass a Houdini transform matrix directly to SOLIDWORKS: conventions and
translation units differ. Extend the transform code and its independent placement
checks if a requested design needs additional rotation axes or X translation.

Ground one reference component per assembly. Use the existing rigid review mates
for static models. They do not define working mechanism travel. Keep physical
bodies separate inside manifest parts; do not boolean-union overlapping
controls to make the interference report empty.

## Run the existing pipeline

Use the project `.venv` and the licensed Windows desktop. The configured
SOLIDWORKS installation is in `sw_helpers.INSTALL`. Do not install another CAD
library or change corporate security settings to work around COM restrictions.
Use the tool's approval mechanism for desktop COM access when needed.

For a fresh output area:

```powershell
.\.venv\Scripts\python.exe scripts\build_parts.py
.\.venv\Scripts\python.exe scripts\build_assembly.py
.\.venv\Scripts\python.exe scripts\validate_and_export.py
.\.venv\Scripts\python.exe scripts\export_houdini.py
```

`build_parts.py --only <asset names>` builds selected assets. Existing recorded
parts are reopened and checked, not rebuilt. There is no legacy single-part
backup conversion option. Preserve user backups unchanged.

The body builders share a part document. Call `begin_body` before each physical
component. The first boss starts a separate solid; later bosses and cuts use
explicit body scope (body selection mark 8). Keep `remember_body` calls after
custom feature operations.
The lever uses separate native Move/Copy Body rotation and translation features;
SOLIDWORKS does not combine both operations in one such feature. Preserve the
head copy's dependency on the original head. In 2026 the insertion angles are
interpreted as Euler rotations; `move_body` sets the feature data
`TransformX/Y/Z` explicitly for the required Cartesian X rotation.

`build_assembly.py --only <product names>` requires its asset parts to exist.
Existing assemblies are checked, not replaced. STEP's `--only` selects export
basenames; existing STEP files are reimported and checked against current native
geometry, not silently refreshed. Existing STL files are likewise checked against
current native geometry and preserved.
Resolve stale output through the user's backup/replacement decision.

## Evidence required before completion

All JSON reports go in `output/validation/`, never beside the model files.

1. Each asset part: expected 2/2/4/5 valid bodies, intended envelope, named features without
   rebuild errors, successful save and reopen.
2. Each product: three asset parts, correct referenced paths,
   exactly one fixed reference, healthy mates, and global leaf positions matching
   the layout. The complete switch/dimmer currently contain 8/9 solids.
3. Interference: preserve the documented stem/grip and dimmer-stack overlaps;
   investigate new collisions. Do not silently repair reference defects.
4. STEP: reopen each export in an isolated session; compare solid count, total
   and individual volumes, and the assembly envelope. Confirm AP214. A nonempty
   file or successful SaveAs is insufficient evidence.
5. STL: compare mesh bounds and signed-volume magnitude with the native group.
   Check all four meshes with Houdini's installed `ginfo -s <file>` when available.
   Numeric units are millimeters; do not auto-center or scale the meshes.
6. Verify that native references use current files rather than `.backup/` paths.
   Keep the source backup unchanged. Check actual outputs, not only logs.

The shipped export checks use numerical comparison thresholds, not production
tolerances. Retain them unless a diagnosed numerical issue justifies a change;
never relax a check simply to make a failed run pass.

## COM and cleanup pitfalls

- Use the generated 2026 type-library bindings and `interface()` helper. Some
  automatically returned COM objects need an explicit interface before use.
- API geometry is in meters; script input dimensions are in millimeters.
  Verify new signatures against the installed interop assemblies or official
  SOLIDWORKS API help instead of guessing argument lists.
- `IBody2.Check()` returns **1** for valid. `swAddMateError_NoError` is also **1**.
  Save/open error outputs use **0** for success. Read the appropriate enum.
- Suppress dimension-entry prompts during sketch creation and restore the prior
  preference in `finally`. STL setters can report false even when the requested
  value is set; verify preferences by reading them back.
- Use `GetExtremePoint` for exact envelopes; `GetBodyBox` is padded/approximate.
- Clear selection before exporting. For STEP, close saved native documents
  before import, then close all temporary imported documents including children.
  Duplicate document titles can leave hidden imports open and disrupt exports.
- Use `close_session` in `finally`. Save completed native work and close each
  file after use; exit the application when no documents remain. Never terminate
  unrelated processes or discard unknown unsaved user documents. If a failed
  operation leaves recovery work open, identify it explicitly.
- Do not start multiple COM clients against the same SOLIDWORKS instance. If an
  operation stalls, inspect the existing session before launching another.

Report the output locations, checks passed and any unresolved limitation briefly.
Update current user docs only when structure, decisions or usage changed. Do not
create a separate document for every run. Do not commit or push.
