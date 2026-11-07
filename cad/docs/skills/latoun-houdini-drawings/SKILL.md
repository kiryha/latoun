---
name: latoun-houdini-drawings
description: Produce Latoun review drawings and structured CAD handoffs from Houdini scenes or OBJ exports. Use for sketches, dimensions, profiles and assembly placement intended for later SOLIDWORKS reconstruction; not for building native CAD files.
---

# Latoun Houdini-to-drawings

Produce a reviewable visual reference and precise reconstruction data. Houdini is
the visual source of truth until the owner explicitly changes that authority.

## Read only what this task needs

1. Read the applicable repository instructions and the current
   [handoff contract](../../input_handoff_prompt.md). That document owns the JSON
   schema and deliverable requirements; do not create a competing schema.
2. For Houdini input, read the relevant sections of
   [Houdini scene guide](../../houdini_scene.md). Its node map is a verified
   starting point, not a substitute for inspecting a newer scene.
3. Read the current `config/wall_plates/asset_manifest.json` in the supplied
   repository. Resolve actual paths rather than assuming the historical drive
   or checkout location. Preserve exact IDs, including spelling anomalies.
4. Inspect the existing generator only where adaptation is needed. The scene
   guide locates the proven 005 implementation and explains its limitations.

Use the owner's selected scene/OBJ, scope and output directory. A new source
does not authorize rebuilding unrelated assets or overwriting older handoffs.
For documentation-only work, do not launch Houdini or SOLIDWORKS.

## Extract once, then work from structured data

Prefer installed Houdini `hython` and `hou` over GUI inspection. Evaluate the
supplied scene, read controlling parameters **and expressions**, and extract
only the relevant construction nodes, final geometry and placements. Save a
compact machine-readable extraction in the new output's working area so later
drawing and validation steps do not repeatedly load the scene or its full node
dump into model context.

- Preserve source files. Never save the input scene or cook export/file-write
  nodes. Evaluate upstream geometry nodes instead. Record source hashes.
- Read the saved control state first. Gang/slot changes may be made in memory
  for extraction; discard them when the process exits. Do not alter modeling
  parameters to obtain nicer dimensions.
- Check node errors, missing dependencies and actual geometry. An empty OBJ or
  failed cook is not a valid empty component.
- If procedural cooking fails because of execution restrictions, use the
  environment's normal approval mechanism. Do not repeatedly retry unchanged
  failures or modify security settings.
- Without usable Houdini, extract OBJ measurements with explicit unit provenance.
  Mark unavailable construction dimensions unknown or estimated. Screenshots
  clarify appearance, hierarchy and pose; they are not precision dimensions.
  Do not substitute an older mesh for a missing current part without disclosure.

Read the active output branches, not every alternative in the scene. For each
requested manifest variant, set gang/slot controls, evaluate its output, and
record independent assembled bounds and preferably vertices for validation.

## Recover intent without redesigning

For each controlling dimension, retain `value`, `unit`, `basis` and `source`
as defined in the contract. Capture source parameter paths. For derived values,
include the formula and inputs; for fits, include the method and residual.

Source construction geometry and finished geometry have different roles.
A 70 x 120 starting profile may produce smaller finished bounds after tapering
and bevels. Show the construction envelope and the measured result separately.
Do not enlarge geometry or relabel its actual boundary as the nominal profile.

- Prefer explicit owner decisions and verified source parameters to inference.
- A bevel's distance parameter is not automatically a CAD fillet radius.
- Preserve intentional decimals, including placement offsets. Formatting
  floating-point noise such as 27.49999999999997 as 27.5 is different from
  changing 3.28183 to 3.
- If nominalization is requested, record measured -> proposed -> approved values
  with justification. Apply only changes authorized in the conversation; resolve
  consequential conflicts while continuing independent extraction.
- Keep unknown mechanisms, travel, tolerances, material and finish unknown.
  Do not infer electrical compliance from a node or asset name.

## Build the handoff

Follow the contract's small package: `design.json`, `drawings.pdf`, and only
useful `profiles/` and part-local `meshes/`. Honor a specifically requested
image format. Keep generation scripts and intermediate data out of the main
handoff index, for example in `_work/`.

Separate a configurable asset group from a provisional manufactured component.
Reuse one component definition for repeated heads or identical modules.
Disconnected polygon islands do not, by themselves, define separate parts.

Normalize geometry to mm once. Define each local frame explicitly; keep
placement separate in rigid 4x4 column-vector matrices. Check Houdini's row-vector
matrix convention before conversion. Transpose a Houdini matrix only when it
is actually the row-vector transform being exported; do not transpose a matrix
already built in the target convention.

Supply compact recipes: section stations and transitions; radial/axial profiles;
hole axes, positions and depths; twist axis, phase, handedness and end treatment.
Use ordered source profiles for decorative or otherwise non-analytic contours.
State plane, winding, closure and sampling status. Reference meshes support
shape comparison, not automatic faceted B-rep manufacture.

Generate drawings from the same data used for JSON. Reuse the existing visual
format where practical. Lead with assembled front, side and isometric views,
then relevant component views and sections. Distinguish construction, measured,
estimated and proposed dimensions. Include datum, mm units and revision.

Dimension the axis shown in each projection: a Z length belongs on a view that
displays Z, not on the vertical Y axis of a front view. Fit all geometry inside
each viewport. Avoid decorative image generation for dimensioned engineering
references.

## Verify and deliver

- Parse JSON; resolve relative files; check IDs against the requested manifest
  subset, component references, numeric finiteness and rigid matrices.
- Re-read delivered OBJ files. Check local bounds, profile planes/closure/winding
  and transformed assembly bounds against independently evaluated source outputs.
- Check repeated-part counts and switch pose explicitly. For vertex matching,
  use spatial matching with a declared numerical threshold; lexicographic
  sorting of rounded coordinates is unstable after float32 translations.
- Record open/non-manifold edges and other detected defects without silently
  repairing them. Do not report solid volume from invalid/open geometry.
- Render and visually inspect every final drawing page for clipped geometry,
  misplaced dimension lines, overlapping labels and consistency with JSON.
- Recheck source hashes. Report verification thresholds as numerical checks,
  never as manufacturing tolerances.

For a suspected mechanical problem, state the affected component, evidence,
classification, confidence and required action. A proposed correction needs
current/proposed values and any Houdini modification. Preserve unresolved
overlaps; do not claim a collision-free sweep from a static pose.

Deliver the folder and a short summary of coverage, verification and unresolved
questions. Do not create SOLIDWORKS files, change the manifest, commit or push.
