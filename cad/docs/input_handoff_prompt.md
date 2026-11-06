# Prompt for the Houdini reference agent

Use the prompt below with the source Houdini scene or exported geometry and the
desired destination inside `cad/inputs/`. It produces a review package for the
owner and a structured handoff for the SOLIDWORKS modeling agent.

---

You are preparing a Latoun design handoff from artistic Houdini models to an
agent that builds editable native SOLIDWORKS geometry. Produce clear drawings
for human review and precise machine-readable data for reconstruction.

Work from the supplied source and the owner's stated design targets. Preserve
the source files. Write only to the requested directory inside `cad/inputs/`;
do not overwrite an existing handoff without authorization. Do not modify CAD
outputs, the configurator, or the asset manifest.

## Deliver a small, useful package

```text
<requested input folder>/
  design.json       Dimensions, geometry definitions, grouping and placement
  drawings.pdf      Readable review drawings
  profiles/         Only profiles that cannot be described simply in JSON
  meshes/           Part-local OBJ references where useful for shape comparison
```

Use PNG sheets if PDF creation is unavailable. Do not create extra histories,
file-size tables or duplicate dimension spreadsheets. A new filename suffix or
version folder is not required unless the owner requests it.

## Establish identity, units and coordinates first

Read the current `config/wall_plates/asset_manifest.json` without modifying it.
Use its exact asset IDs and file basenames. For example, a one-gang switch has
the `1gang_plate`, `1gang_plate_screws` and `1gang_slot1_switch` asset groups.
The plate group includes metal and silicone; the screws group uses one component
twice; the switch module includes its insert and control components.

Distinguish a configurable asset group from a possible manufactured component.
Use a stable lowercase ID for each unique component and an instance ID for each
placement. Reuse component geometry when the same screw appears twice. Mark a
suggested manufacturing split as provisional; do not infer separate components
from every disconnected polygon island.

Normalize all numeric length data and reference-mesh coordinates to millimeters.
Record the source units and conversion applied; never infer units from appearance.
Use a right-handed product frame: origin at the plate rear-face center, +X right,
+Y up and +Z toward the user. Record the conversion from the source frame.

Store component geometry in its defined local frame and placement separately.
For each instance, provide a 4x4 `local_to_product` matrix as four JSON rows,
using column vectors (`p_product = M * p_local`), with translation in the last
column in millimeters. The last row is `[0,0,0,1]`. Bake unit conversion into
local geometry; the placement matrix should contain rotation and translation,
not a second scale. Do not bake placement into the mesh and then apply it again
through the matrix. Explain any unavoidable reflection or non-rigid deformation.

## Record intention separately from measurement

For every controlling dimension include `value`, `unit`, `basis` and `source`.
Use these basis values:

- `user_specified`: an explicit owner-approved target.
- `source_parameter`: an intentional Houdini parameter or analytic definition.
- `measured`: measured from the supplied geometry; not automatically design intent.
- `derived`: calculated from other values; include the formula and inputs.
- `estimated`: a fit or interpretation; include the method and measured error when available.
- `unknown`: use `null` for the value and explain what is missing.

Example dimension entry:

```json
{"value": 70, "unit": "mm", "basis": "user_specified", "source": "Owner-approved outer plate width"}
```

Do not silently round conversion artifacts, scale the whole product, add a fit,
or choose a standard size. If a measured width differs from an approved nominal
width, record both with their roles and identify the approved value as controlling.
Proposed rounding needs to be labeled as a proposal until approved. Numerical
precision and curve-fitting thresholds are not manufacturing tolerances.

## Make geometry reconstructable without reading pixels

Prefer compact geometric definitions over meshes when the source supports them:

- Plates/inserts: ordered section stations, their planes and offsets, width,
  height, corner radii, thickness and the intended transition between stations.
- Turned parts: axis, radial/axial profile coordinates or line/arc segments,
  steps, tapers and edge breaks. State whether each size is a radius or diameter.
- Holes/cuts: centers, axes, profiles, depths or through conditions and which
  components are cut. Include hidden rear geometry and relevant sections.
- Sweeps/twists: section, path, start/end positions, twist angle, sign convention
  and phase. For flutes, supply count, analytic radial function and end treatment
  if these exist in the source.
- Repeated details: one definition and its instance transforms or pattern rule.

Do not claim an analytic circle or constant radius solely because a polygonal
profile looks circular. If fitted, label it `estimated` and report the residual.
If an analytic definition is unavailable, supply the relevant numeric sections
and state that they are sampled geometry.

For complex profiles, use DXF with real LINE/ARC/CIRCLE/polyline entities where
appropriate, or JSON containing ordered points/curve data. Include local plane,
origin, axes, units, closed/open status, winding and any sampling tolerance.
For splines, provide the degree, knots, control points, weights when rational,
and periodic/closed flags when that data is available. Otherwise label a sampled
polyline honestly; do not describe it as an exact spline.

Keep logos and decorative contours in their own profile files. Do not replace
simple analytic shapes with thousands of mesh edges or request faceted B-rep
conversion. A reference OBJ is for comparison, not the authoritative CAD recipe.

## Organize `design.json`

Use this structure, adding only fields needed by the actual geometry:

```json
{
  "units": "mm",
  "angle_units": "degrees",
  "coordinate_system": {
    "handedness": "right",
    "origin": "plate rear-face center",
    "x": "right", "y": "up", "z": "toward user"
  },
  "source": {
    "files": [],
    "original_units": null,
    "conversion_to_mm": null
  },
  "components": [],
  "assets": [],
  "checks": {},
  "issues": []
}
```

Each `components` entry must have:

- `id` and source node/object identity.
- `dimensions`: named dimension entries using the value/unit/basis/source format.
- `geometry`: the applicable definitions above, or relative paths to profiles.
  Identify whether each definition is exact source data, a measurement or a fit.
- A local-frame definition and local `bounds_mm` as `[xmin,ymin,zmin,xmax,ymax,zmax]`.
- Optional `reference_mesh` relative path and material intent, only when known.

Each `assets` entry must have its manifest `id`, `file_stem` and `instances`.
Each instance names its `component_id`, unique `instance_id` and
`local_to_product` matrix. For a shared physical component, reference the same
component ID rather than duplicating its geometry definition. Provide the
assembled bounds for each asset as a scale and placement check.

Use JSON numbers, not formatted dimension strings, commas as decimal separators,
`NaN` or infinity. Reference other files by paths relative to `design.json`.
Keep dimensions and profile coordinates consistent when both describe the same
feature. Record assumptions and unresolved contradictions in `issues`.

## Drawings for the owner

Lead with the assembled product and its asset groups. Show front, side and an
isometric view, then only the component views and sections needed to explain
shape or resolve ambiguity. Use readable labels and dimensions that matter to
design decisions; avoid displaying every raw floating-point measurement.

Use the same component IDs as JSON. Distinguish approved nominal dimensions,
measured references and proposals. Show the datum, units and provisional control
pose. Mark missing mechanism/fastening details and existing overlaps. Do not add
production tolerances, threads, certifications or manufacturing requirements
that the owner has not specified.

## Check the handoff before delivering

- Parse the JSON and verify every referenced file exists.
- Verify unique IDs, valid component references and manifest grouping.
- Check local meshes/profiles against stated dimensions and local bounds.
- Apply the supplied matrices and check the assembled bounds and orientation.
  Specifically check repeated screws and the switch lever pose.
- Check profile closure and section ordering. Record source mesh defects rather
  than silently repairing them. Report volume only for valid closed geometry.
- Confirm the drawings and JSON agree. Flag differences from the source draft
  as explicit intended changes or unresolved issues.
- If a critical dimension or unit cannot be determined, ask the owner or mark
  it unknown; do not conceal the gap with an invented precise value.

Deliver the requested folder with a short summary of unresolved questions and
any intentional differences from the original model. Do not create SOLIDWORKS
files yourself in this reference-preparation task.
