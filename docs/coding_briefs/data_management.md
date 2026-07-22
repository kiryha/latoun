# Geometry Data Management

## 1. Purpose

The Latoun configurator separates product data, geometry assets, material definitions, and resolved render state.

The geometry system should remain simple. Latoun products are small compared with automotive assets, so some geometry duplication is acceptable when it removes runtime assembly complexity.

The core separation is:

```text
Product database
    Describes what the product is.

Asset manifest
    Registers which render assets exist and where they are stored.

GLB files
    Contain geometry and semantic material-binding information.

Material library
    Defines how physical materials look in Three.js.

Render state
    Describes which assets and materials are needed for one configuration.
```

The manufacturing BOM structure and render asset structure do not need to match one-to-one.

---

## 2. Source and Export Formats

### 2.1 Houdini

Houdini is the source of truth for geometry.

Houdini is responsible for:

- Modeling the parts
- Positioning parts in final assembly coordinates
- Applying clean mesh names
- Applying semantic placeholder materials
- Baking transforms
- Exporting GLB files

### 2.2 GLB

Use `.glb` rather than separate `.gltf`, `.bin`, and texture files.

GLB is preferred because it is:

- A single file
- Easy to load with Three.js
- Easy to move and register
- Suitable for browser-based rendering

The current geometry assets are:

```text
1gang_plate.glb
1gang_plate_screws.glb
1gang_slot01_dimmer.glb
1gang_slot01_switch.glb
```


---

## 3. Geometry Assembly Strategy

All exported geometry should already be positioned in final assembly coordinates.

The configurator should load every asset at the scene origin:

```text
position = 0, 0, 0
rotation = 0, 0, 0
scale = 1, 1, 1
```

Example assembly:

```text
1-gang assembly
=
1gang_plate.glb
+ 1gang_plate_screws.glb
+ one selected module:
    1gang_slot01_dimmer.glb
    or
    1gang_slot01_switch.glb
```

Three.js should not calculate slot positions or module transformations during the first implementation.

This follows the automotive-style workflow:

```text
Final positioning happens in Houdini.
Transforms are baked.
Runtime assets are loaded at the origin.
```

---

## 4. Geometry Duplication

It is acceptable to export slot-specific geometry instead of reusing one geometry file with runtime transformations.

For example:

```text
2gang_slot01_switch.glb
2gang_slot02_switch.glb

4gang_slot01_switch.glb
4gang_slot02_switch.glb
4gang_slot03_switch.glb
4gang_slot04_switch.glb
```

This duplicates some geometry, but it removes the need for:

- Slot transform tables
- Pivot management
- Placement matrices
- Runtime assembly math
- Additional database relationships
- Alignment debugging

Latoun products are small enough that the extra file size is less important than a simple and reliable pipeline.

A reusable asset and anchor-based placement system can be added later if geometry duplication becomes a real problem.

---

## 5. Coordinate System

Define one coordinate convention and keep it consistent across all assets.

Recommended convention:

```text
Origin:
Center of the complete wall plate front face

+X:
Right

+Y:
Up

+Z:
Toward the user, away from the wall

Wall plane:
Z = 0

Actuators:
Extend in the +Z direction

Electrical bodies:
Extend in the -Z direction
```

All GLB assets belonging to the same assembly must use this coordinate space.

The frontend camera can look toward the origin from positive Z.

---

## 6. Units

Recommended unit policy:

```text
Houdini modeling:
Millimeters

Database dimensions:
Millimeters

GLB export:
Meters

Three.js scene:
Meters
```

Example:

```text
Houdini plate height:
120 mm

GLB / Three.js plate height:
0.12 m
```

Engineering and manufacturing dimensions remain easy to read in millimeters, while GLB and Three.js use meter-based scale.

---

## 7. Transform Policy

Before exporting from Houdini:

- Bake object transforms into geometry
- Use the global Latoun assembly origin
- Reset root translation
- Reset root rotation
- Reset root scale
- Remove temporary export transforms
- Confirm final assembly alignment

Expected exported root transform:

```text
translation = 0, 0, 0
rotation = 0, 0, 0
scale = 1, 1, 1
```

The Three.js loader should not contain per-file correction transforms.

If an asset is misaligned, fix it in Houdini and export it again.

---

## 8. Naming Conventions

### 8.1 Current Short Names

Short names are acceptable during the first iteration:

```text
1gang_plate.glb
1gang_plate_screws.glb
1gang_slot01_dimmer.glb
1gang_slot01_switch.glb
```

These names are enough while the project supports only one market and one collection.

### 8.2 Future Full Convention

A future full filename convention can include:

```text
latoun_[market]_[collection]_[gang]_[asset_type]_[slot]_[module_type].glb
```

Examples:

```text
latoun_us_mcm_1gang_plate.glb
latoun_us_mcm_1gang_plate_screws.glb
latoun_us_mcm_1gang_slot01_dimmer.glb
latoun_us_mcm_1gang_slot01_switch.glb
```

Long and explicit filenames are preferable to abbreviated or ambiguous names.

### 8.3 Naming Rules

Use:

- Lowercase
- Underscores
- Stable terminology
- Two-digit slot numbers
- Semantic names
- No manual version suffixes

Good:

```text
1gang_slot01_dimmer.glb
```

Bad:

```text
part_final.glb
switch_new.glb
switch_v7.glb
mesh_export_latest.glb
```

---

## 9. Internal Mesh Names

Mesh names inside GLB files should describe geometry roles.

Recommended names:

```text
geo_plate_body
geo_visible_screw_01
geo_visible_screw_02
geo_actuator_knob
geo_actuator_button
geo_actuator_collar
geo_outlet_face
geo_core_visible
geo_insulator
```

Avoid names generated by modeling applications:

```text
mesh1
box2
polySurface45
part_final
object_copy_3
```

The frontend should not normally depend on mesh names for product logic, but clean names help with inspection, debugging, and material assignment.

---

## 10. Asset Manifest

### 10.1 Definition

The asset manifest is a lightweight registry of loadable render assets.

It maps a stable semantic asset key to a physical GLB file.

Example:

```json
{
  "schema_version": 1,
  "assets": {
    "plate.1gang": {
      "asset_type": "plate",
      "file": "/assets/glb/1gang_plate.glb",
      "coordinate_space": "assembly_origin"
    },
    "hardware.1gang.plate_screws": {
      "asset_type": "hardware",
      "file": "/assets/glb/1gang_plate_screws.glb",
      "coordinate_space": "assembly_origin"
    },
    "module.1gang.slot01.dimmer": {
      "asset_type": "slot_module",
      "module_type": "dimmer",
      "slot_position": 1,
      "file": "/assets/glb/1gang_slot01_dimmer.glb",
      "coordinate_space": "assembly_origin"
    },
    "module.1gang.slot01.switch": {
      "asset_type": "slot_module",
      "module_type": "switch",
      "slot_position": 1,
      "file": "/assets/glb/1gang_slot01_switch.glb",
      "coordinate_space": "assembly_origin"
    }
  }
}
```

### 10.2 What the Manifest Contains

The manifest can record:

- Semantic asset key
- GLB path
- Asset type
- Module type
- Gang count
- Slot position
- Coordinate-space convention
- Expected material bindings
- Temporary material policy
- Optional development notes

### 10.3 What the Manifest Does Not Contain

The asset manifest should not contain:

- Product pricing
- Inventory counts
- Customer orders
- Supplier data
- Manufacturing BOM rules
- Three.js material parameters
- Product compatibility rules
- Final customer material selection

Those belong in the database, material library, or configuration services.

### 10.4 Why Use a Manifest

Without a manifest, GLB paths become hardcoded and scattered through frontend and backend code.

The manifest provides one clean mapping:

```text
Semantic asset key
    ↓
Physical GLB path
```

Example:

```text
module.1gang.slot01.switch
    ↓
/assets/glb/1gang_slot01_switch.glb
```

This also allows a filename to change without changing configuration logic.

---

## 11. Geometry Assets and BOM Components

A render asset does not have to represent exactly one physical BOM component.

Example GLB:

```text
1gang_slot01_dimmer.glb
```

It may contain:

- Knob geometry
- Collar geometry
- Visible electrical-core geometry
- Shaft-adapter geometry

The manufacturing BOM may represent these as separate parts:

```text
1x certified dimmer core
1x dimmer knob
1x collar
1x shaft adapter
```

This is valid.

The relationship is:

```text
BOM:
Optimized for manufacturing, inventory, and purchasing.

Render assets:
Optimized for loading and visual assembly.
```

Do not force a one-to-one mapping between them.

---

## 12. Geometry and Materials Must Remain Separate

GLB files should contain geometry and default placeholder materials.

The final Three.js render material is assigned after the backend resolves the configuration.

Example customer configuration:

```json
{
  "gang_count": 1,
  "module_type": "dimmer",
  "material": "brass"
}
```

The backend resolves this into:

```text
plate.1gang
hardware.1gang.plate_screws
module.1gang.slot01.dimmer
material.solid_brass.brushed
```

The frontend then:

1. Loads the GLB files.
2. Reads semantic material bindings.
3. Loads or creates the selected Three.js materials.
4. Assigns the materials to the correct geometry.
5. Renders the assembly.

The GLB filename should not encode the final material.

Good:

```text
1gang_plate.glb
```

Avoid:

```text
1gang_plate_brass.glb
1gang_plate_steel.glb
```

The same geometry should support brass, steel, and future materials.

---

## 13. Semantic Material Bindings

### 13.1 Binding Instead of Final Material

Geometry should identify a semantic material role rather than a fixed final material.

Recommended binding names:

```text
bind_plate_body
bind_visible_screws
bind_actuator_primary
bind_actuator_secondary
bind_actuator_collar
bind_core_visible
bind_outlet_face
bind_insulator
```

Avoid material-specific binding names:

```text
bind_brass
bind_steel
bind_black
```

The binding describes the geometry’s role, not its final appearance.

Example:

```text
bind_plate_body
    ↓
material.solid_brass.brushed
```

or:

```text
bind_plate_body
    ↓
material.stainless_steel.brushed
```

### 13.2 Houdini Workflow

In Houdini, assign placeholder materials with stable binding names:

```text
bind_plate_body
bind_visible_screws
bind_actuator_primary
bind_actuator_collar
bind_core_visible
```

The placeholder materials can use diagnostic colors. Their Houdini appearance is not important.

The important data is the material name.

During GLB export, these assignments become named glTF materials associated with mesh primitives.

### 13.3 Three.js Workflow

After loading the GLB, Three.js traverses the meshes and reads:

```typescript
mesh.material.name
```

Example:

```text
mesh.material.name = "bind_plate_body"
```

The resolved render state provides:

```json
{
  "material_binding_assignments": {
    "bind_plate_body": "material.solid_brass.brushed",
    "bind_visible_screws": "material.solid_brass.brushed"
  }
}
```

Three.js replaces each placeholder material with the resolved render material.

---

## 14. Temporary `replace_all` Policy

The first configurator can use a temporary simplified material policy:

```json
{
  "material_policy": "replace_all"
}
```

This means:

```text
Load the GLB.
Traverse every mesh.
Replace every existing material with the selected brass or steel material.
```

This is acceptable for initial assets when every visible part of a GLB should use the same material.

Example:

```text
1gang_plate.glb
    all geometry → brass or steel
```

The limitation is that it cannot represent mixed-material assets such as:

```text
brass knob
black plastic core
white label
steel mounting part
```

When mixed materials become necessary, replace `replace_all` with semantic material bindings.

---

## 15. Material Library

The material library stores the actual Three.js material definitions.

Example identifiers:

```text
material.solid_brass.brushed
material.stainless_steel.brushed
material.plastic.black_matte
```

A material definition may contain:

```text
display name
base color
metalness
roughness
anisotropy
anisotropy rotation
normal texture path
roughness texture path
environment intensity
texture scale
texture rotation
```

Example:

```json
{
  "code": "material.solid_brass.brushed",
  "display_name": "Brushed Brass",
  "three_material_type": "MeshPhysicalMaterial",
  "parameters": {
    "color": "#B88A44",
    "metalness": 1.0,
    "roughness": 0.28,
    "anisotropy": 0.5,
    "anisotropy_rotation": 0.0
  },
  "textures": {
    "normal": null,
    "roughness": null
  }
}
```

The division is:

```text
Geometry binding:
What region is this?

Render material:
How should this region look?
```

---

## 16. Resolved Render State

The backend resolves the product configuration into a render state.

Example:

```json
{
  "configuration": {
    "gang_count": 1,
    "module_type": "dimmer",
    "material": "brass"
  },
  "assets": [
    {
      "asset_key": "plate.1gang",
      "file": "/assets/glb/1gang_plate.glb",
      "material_binding_assignments": {
        "bind_plate_body": "material.solid_brass.brushed"
      }
    },
    {
      "asset_key": "hardware.1gang.plate_screws",
      "file": "/assets/glb/1gang_plate_screws.glb",
      "material_binding_assignments": {
        "bind_visible_screws": "material.solid_brass.brushed"
      }
    },
    {
      "asset_key": "module.1gang.slot01.dimmer",
      "file": "/assets/glb/1gang_slot01_dimmer.glb",
      "material_binding_assignments": {
        "bind_actuator_primary": "material.solid_brass.brushed",
        "bind_actuator_collar": "material.solid_brass.brushed",
        "bind_core_visible": "material.plastic.black_matte"
      }
    }
  ]
}
```

The frontend should not decide:

- Which asset corresponds to a dimmer
- Which material the user selected
- Which asset is compatible with the selected plate
- Which parts belong in the BOM

The frontend should only:

```text
Load assets.
Apply resolved materials.
Render the result.
```

---

## 17. Data Flow

```text
HOUDINI
Model geometry
Position geometry in assembly coordinates
Bake transforms
Assign semantic placeholder materials
Export GLB

        ↓

GLB FILES
Geometry
Mesh names
Default placeholder materials
Semantic material-binding names

        ↓

ASSET MANIFEST
Semantic asset keys
GLB paths
Asset metadata
Expected bindings

        ↓

PRODUCT CONFIGURATION
Gang count
Module type
Physical material
Surface treatment

        ↓

BACKEND
Validate configuration
Resolve asset keys
Read asset manifest
Resolve render material identifiers
Generate render state
Generate BOM separately

        ↓

THREE.JS
Load GLB files
Add them at origin
Read material-binding names
Apply resolved materials
Render assembly
```

---

## 18. Asset Versioning

Do not manually version generated GLB filenames.

Avoid:

```text
1gang_plate_v001.glb
1gang_plate_v002.glb
1gang_plate_final.glb
1gang_plate_final_new.glb
```

Use stable filenames:

```text
1gang_plate.glb
```

When geometry changes:

1. Update the Houdini source.
2. Export again.
3. Overwrite the GLB.
4. Commit the updated generated asset if GLBs are tracked in Git.

The recoverable source is:

```text
Houdini file
+ export logic
+ Git history
```

Production cache-busting hashes can be introduced later:

```text
1gang_plate.a83f91.glb
```

They are not needed during the local prototype stage.

---

## 19. Recommended Asset Folder Structure

```text
assets/
├── glb/
│   ├── plates/
│   │   └── 1gang_plate.glb
│   ├── hardware/
│   │   └── 1gang_plate_screws.glb
│   └── modules/
│       └── 1gang/
│           ├── 1gang_slot01_dimmer.glb
│           └── 1gang_slot01_switch.glb
├── textures/
│   ├── metals/
│   └── plastics/
├── asset_manifest.json
└── render_materials.json
```

For the first implementation, keeping all GLB files in one folder is also acceptable:

```text
frontend/public/assets/glb/
```

The structured folder hierarchy can be introduced as the asset count grows.

---

## 20. Validation

The geometry pipeline should validate assets during development.

Useful validation checks:

- GLB file exists
- Asset key exists in the manifest
- Asset loads successfully
- Root transform is identity
- Expected coordinate space is correct
- Scale is reasonable
- Required material bindings exist
- No unexpected material bindings exist
- Mesh names are not empty
- No accidental hidden export geometry exists
- Module aligns correctly with the plate
- No per-asset frontend correction transform is required

Example error:

```text
Asset module.1gang.slot01.dimmer is missing required binding:
bind_actuator_primary
```

---

## 21. Current v0.1 Decisions

The first configurator will use:

```text
1-gang plate only
switch or rotary dimmer
brass or steel
separate GLB files for plate, screws, and module
all parts positioned in Houdini
all GLBs loaded at origin
asset paths registered through asset_manifest.json
material definitions stored separately from geometry
replace_all material assignment initially
semantic material bindings added when mixed materials are needed
no runtime positioning system
no geometry database
no manual GLB version suffixes
```

---

## 22. Guiding Principles

```text
Keep geometry and materials separate.

Keep product data and render data separate.

Use the database for product concepts, not low-level mesh identifiers.

Use the asset manifest as a lightweight file registry.

Use semantic asset keys instead of hardcoded paths.

Let Houdini own geometry placement.

Let the backend resolve configurations.

Let Three.js remain a simple renderer.

Prefer duplicated positioned assets over premature transform systems.

Use stable filenames and regenerate GLBs from source.

Do not force render assets to match BOM components one-to-one.
```