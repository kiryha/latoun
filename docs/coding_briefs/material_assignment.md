# Latoun Semantic Material Assignment — Coding Brief

## 1. Objective

Implement a production-oriented semantic material assignment system for the Latoun internal configurator.

The current configurator applies one selected material to all loaded assembly geometry through:

```json
{
  "material_policy": "replace_all"
}
```

This must be replaced with a semantic binding workflow.

Each geometry region inside a GLB file will contain a semantic material name exported from Houdini. The application will resolve that semantic name into a Three.js render material using database assignments.

The core mapping is:

```text
finish scheme + binding name → render material
```

Example:

```text
brass + primary_metal → brass_brushed
brass + hardware_metal → brass_brushed
init + electrical_core → black_plastic_matte
```

The implementation must include:

- Database tables for finish schemes and semantic material assignments
- A new internal `Assignments` tab (finish-scheme bindings + assembly preview)
- An admin Assignment States system (persisted viewport assemblies for Assignments preview)
- Backend CRUD endpoints
- Assignment resolution logic
- Semantic material application in Three.js
- Validation and visible error handling
- Migration from the current `replace_all` system

Read the repository `README.md` and existing geometry-management documentation before implementation.

---

## 2. Current Application

The current internal application contains:

```text
Assembly
Materials
Assignments
```

The `Assembly` tab allows the user to:

- Select plate gang count (1–4)
- Select one device per slot:
  - Switch
  - Dimmer
  - Outlet
  - USB-C Outlet
- Select a customer-visible finish scheme for the complete assembly
- Preview the assembled product live (placeholders for missing GLBs)
- Export the active assembly as JSON (admin)
- Save Current State into Assignment States (admin; geometry-only name)
- View a prototype BOM

Public Assembly editing uses current UI state only — it does not load an
`assignment_state_id` while configuring.

Error / warning / success messages overlay at the bottom of the 3D viewport.

The `Materials` tab allows internal users to:

- Create render materials
- Modify render-material parameters
- Delete render materials
- Enable or disable materials
- Preview materials on test geometry

Assignment States are admin viewport presets (CRUD via API; pickable in the
Assignments preview toolbar; created from Assembly Save Current State):

- Gang count (1–4; only 1-gang GLBs exist today for most combinations)
- One module type per slot
- Optional default finish scheme for Assignments preview
- Codes `LAT-ASG-######`
- Display names are geometry-only (no finish suffix)

The `Assignments` tab is an internal administration tool for finish-scheme material bindings and live assembly preview:

- Edit finish schemes and semantic material assignments
- Pick an Assignment State for geometry
- Choose a finish scheme independently for materials
- Select **None** to show the material hero preview instead of an assembly
- Surface error / success / missing-assignment banners at the bottom of the preview viewport

Existing render-material properties include:

```text
code
display name
base color
metalness
roughness
anisotropy
anisotropy rotation
active status
```

Current geometry assets:

```text
1gang_plate.glb
1gang_plate_screws.glb
1gang_slot1_dimmer.glb
1gang_slot1_switch.glb
```

All geometry is exported from Houdini in final assembly coordinates and loaded at the origin.

---

## 3. Target Architecture

Use the following separation:

```text
GLB geometry
    Stores semantic material names.

Materials table
    Stores actual Three.js render-material definitions.

Finish schemes table
    Stores customer-visible finish choices.

Material assignments table
    Maps finish scheme + semantic binding to render material.

Backend resolver
    Combines init assignments with the selected finish scheme.

Frontend renderer
    Reads semantic names from imported GLB materials and applies resolved render materials.
```

The asset manifest must remain a geometry file registry only.

Do not store material assignments or expected semantic bindings in the asset manifest.

---

## 4. Terminology

Use these terms consistently.

### Render Material

An actual material definition used to create a Three.js material.

Examples:

```text
brass_brushed
stainless_steel_brushed
black_steel_brushed
black_plastic_matte
white_ceramic
```

### Semantic Binding

A role-based material name stored on geometry.

Examples:

```text
primary_metal
hardware_metal
actuator_metal
electrical_core
insulator
label
```

Semantic bindings must not contain a final physical material name.

Good:

```text
primary_metal
hardware_metal
```

Bad:

```text
brass_plate
black_plastic
steel_screw
```

### Finish Scheme

A customer-visible product finish selection that changes multiple render materials in the background.

Examples:

```text
brass
steel
black
copper
```

User-facing label:

```text
Finish
```

Internal entity name:

```text
finish_scheme
```

### Init Scheme

A hidden internal finish scheme containing static material assignments.

Example:

```text
init + electrical_core → black_plastic_matte
init + insulator → black_plastic_matte
```

The `init` scheme must not appear as a selectable finish in the Assembly tab.

---

## 5. Material Assignment Rule

The authoritative mapping is:

```text
finish_scheme + binding_name → render_material
```

Example assignment rows:

| Finish scheme | Binding name | Render material |
|---|---|---|
| `init` | `electrical_core` | `black_plastic_matte` |
| `init` | `insulator` | `black_plastic_matte` |
| `init` | `label` | `white_print` |
| `brass` | `primary_metal` | `brass_brushed` |
| `brass` | `hardware_metal` | `brass_brushed` |
| `brass` | `actuator_metal` | `brass_brushed` |
| `steel` | `primary_metal` | `stainless_steel_brushed` |
| `steel` | `hardware_metal` | `stainless_steel_brushed` |
| `steel` | `actuator_metal` | `stainless_steel_brushed` |
| `black` | `primary_metal` | `black_steel_brushed` |
| `black` | `hardware_metal` | `black_steel_brushed` |
| `black` | `actuator_metal` | `black_steel_brushed` |

---

## 6. Strict Option A Policy

All geometry material names must be treated as semantic bindings.

Do not support direct material names stored on geometry.

Do not use this fallback:

```text
No assignment found
→ assume the semantic name is a render-material code
```

Instead:

```text
No assignment found
→ report a missing assignment
→ apply a visible error material
```

This strict behavior prevents silent material errors.

---

## 7. GLB and Houdini Contract

In Houdini, geometry regions will receive semantic material names through `shop_materialpath` or the equivalent GLB-export material-assignment workflow.

Examples:

```text
primary_metal
hardware_metal
actuator_metal
electrical_core
insulator
label
```

The exported GLB must preserve these values as glTF material names.

After loading a GLB, Three.js should be able to read:

```typescript
mesh.material.name
```

Example:

```text
mesh.material.name === "primary_metal"
```

The semantic value is stored in the GLB itself. It must not be repeated in the asset manifest.

---

## 8. Asset Manifest Changes

Remove material-related properties from asset entries.

Current:

```json
{
  "category": "plate",
  "file": "/assets/glb/1gang_plate.glb",
  "coordinate_space": "assembly_origin",
  "material_policy": "replace_all"
}
```

Target:

```json
{
  "category": "plate",
  "file": "/assets/glb/1gang_plate.glb",
  "coordinate_space": "assembly_origin"
}
```

The manifest should contain only asset-registration information, such as:

```text
asset key
category
file path
coordinate space
module type
slot position
gang count
```

It must not contain:

```text
material policy
binding names
expected bindings
render-material assignments
finish-scheme definitions
```

---

## 9. Database Schema

Retain the existing `materials` table.

Add:

```text
finish_schemes
material_assignments
```

### 9.1 `finish_schemes`

Fields:

```text
finish_scheme_id
code
display_name
description
is_active
is_customer_visible
sort_order
created_at
updated_at
```

Constraints:

```text
code must be unique
code must not be empty
display_name must not be empty
```

Seed values:

```json
[
  {
    "code": "init",
    "display_name": "Initialization",
    "description": "Static material assignments shared by all assemblies.",
    "is_active": true,
    "is_customer_visible": false,
    "sort_order": 0
  },
  {
    "code": "brass",
    "display_name": "Brass",
    "description": "Brass product finish scheme.",
    "is_active": true,
    "is_customer_visible": true,
    "sort_order": 10
  },
  {
    "code": "steel",
    "display_name": "Steel",
    "description": "Stainless-steel product finish scheme.",
    "is_active": true,
    "is_customer_visible": true,
    "sort_order": 20
  },
  {
    "code": "black",
    "display_name": "Black",
    "description": "Blackened-metal product finish scheme.",
    "is_active": false,
    "is_customer_visible": true,
    "sort_order": 30
  }
]
```

### 9.2 `material_assignments`

Fields:

```text
material_assignment_id
finish_scheme_id
binding_name
material_id
created_at
updated_at
```

Foreign keys:

```text
finish_scheme_id → finish_schemes.finish_scheme_id
material_id → materials.material_id
```

Required uniqueness constraint:

```text
UNIQUE(finish_scheme_id, binding_name)
```

Required indexes:

```text
finish_scheme_id
binding_name
material_id
```

Deletion behavior:

```text
Deleting a finish scheme should delete its assignments.

Deleting a render material must be blocked if assignments reference it,
unless the user explicitly reassigns or removes those assignments first.
```

Do not use unstructured JSON for the assignment table.

---

## 10. Suggested SQLAlchemy Models

Use the existing project conventions. The structure should be equivalent to:

```python
class FinishScheme(Base):
    __tablename__ = "finish_schemes"

    finish_scheme_id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_customer_visible = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class MaterialAssignment(Base):
    __tablename__ = "material_assignments"

    material_assignment_id = Column(Integer, primary_key=True)

    finish_scheme_id = Column(
        Integer,
        ForeignKey(
            "finish_schemes.finish_scheme_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    binding_name = Column(String, nullable=False)

    material_id = Column(
        Integer,
        ForeignKey("materials.material_id"),
        nullable=False,
    )

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "finish_scheme_id",
            "binding_name",
            name="uq_finish_scheme_binding_name",
        ),
        Index(
            "ix_material_assignments_finish_scheme_id",
            "finish_scheme_id",
        ),
        Index(
            "ix_material_assignments_binding_name",
            "binding_name",
        ),
        Index(
            "ix_material_assignments_material_id",
            "material_id",
        ),
    )
```

Use full descriptive variable names. Do not use one-letter variable names.

---

## 11. API Endpoints

Add CRUD endpoints for finish schemes and assignments.

### 11.1 Finish Schemes

```text
GET    /api/finish-schemes
POST   /api/finish-schemes
GET    /api/finish-schemes/{finish_scheme_id}
PUT    /api/finish-schemes/{finish_scheme_id}
DELETE /api/finish-schemes/{finish_scheme_id}
```

List endpoint should support filtering:

```text
?is_active=true
?is_customer_visible=true
```

### 11.2 Material Assignments

```text
GET    /api/finish-schemes/{finish_scheme_id}/assignments
POST   /api/finish-schemes/{finish_scheme_id}/assignments
PUT    /api/material-assignments/{material_assignment_id}
DELETE /api/material-assignments/{material_assignment_id}
```

Optional bulk save endpoint:

```text
PUT /api/finish-schemes/{finish_scheme_id}/assignments
```

Example bulk request:

```json
{
  "assignments": [
    {
      "binding_name": "primary_metal",
      "material_code": "brass_brushed"
    },
    {
      "binding_name": "hardware_metal",
      "material_code": "brass_brushed"
    },
    {
      "binding_name": "actuator_metal",
      "material_code": "brass_brushed"
    }
  ]
}
```

Bulk save behavior:

- Create new rows
- Update existing rows for matching binding names
- Remove rows omitted from the submitted complete assignment set
- Execute in one database transaction
- Return the saved normalized assignment list

---

## 12. Resolved Assignment Endpoint

Add or update a backend endpoint that returns flattened assignments for a selected customer finish scheme.

Suggested endpoint:

```text
GET /api/finish-schemes/{finish_scheme_code}/resolved-assignments
```

Example response:

```json
{
  "finish_scheme": {
    "code": "brass",
    "display_name": "Brass"
  },
  "active_sources": [
    "init",
    "brass"
  ],
  "material_assignments": {
    "primary_metal": "brass_brushed",
    "hardware_metal": "brass_brushed",
    "actuator_metal": "brass_brushed",
    "electrical_core": "black_plastic_matte",
    "insulator": "black_plastic_matte",
    "label": "white_print"
  },
  "materials": {
    "brass_brushed": {
      "code": "brass_brushed",
      "display_name": "Brushed Brass",
      "base_color": "#B88A44",
      "metalness": 1.0,
      "roughness": 0.45,
      "anisotropy": 0.0,
      "anisotropy_rotation": 0.5,
      "normal_texture_path": null,
      "roughness_texture_path": null
    },
    "black_plastic_matte": {
      "code": "black_plastic_matte",
      "display_name": "Matte Black Plastic",
      "base_color": "#080808",
      "metalness": 0.0,
      "roughness": 0.72,
      "anisotropy": 0.0,
      "anisotropy_rotation": 0.0,
      "normal_texture_path": null,
      "roughness_texture_path": null
    },
    "white_print": {
      "code": "white_print",
      "display_name": "White Print",
      "base_color": "#F2F2F2",
      "metalness": 0.0,
      "roughness": 0.55,
      "anisotropy": 0.0,
      "anisotropy_rotation": 0.0,
      "normal_texture_path": null,
      "roughness_texture_path": null
    }
  }
}
```

The frontend should receive all material definitions needed for the active assembly in the resolved response.

Avoid one API request per material.

---

## 13. Assignment Resolution Logic

For a selected customer-visible scheme:

```text
1. Load all assignments from init.
2. Load all assignments from the selected finish scheme.
3. Copy init assignments into the resolved mapping.
4. Overlay selected finish-scheme assignments.
5. Selected finish-scheme assignments override init assignments with the same binding name.
6. Return one flattened mapping.
```

Example:

```text
init:
electrical_core → black_plastic_matte
primary_metal   → default_steel

brass:
primary_metal   → brass_brushed
```

Resolved:

```text
electrical_core → black_plastic_matte
primary_metal   → brass_brushed
```

Do not depend on database row insertion order.

The precedence must be explicit:

```text
init < selected finish scheme
```

---

## 14. New `Assignments` Tab

The application has three top-level tabs:

```text
Assembly | Materials | Assignments
```

The `Assignments` tab is an internal administration tool for finish-scheme material bindings and live preview.

Assignment States persist viewport assemblies used by the Assignments tab for geometry (created via Assembly Save Current State or the API). See `docs/coding_briefs/configurator.md` §8.3.

The future customer-facing configurator should not expose the Assignments tab (and should hide Assembly admin actions via `VITE_ADMIN_MODE=false`).

Error / success / missing-assignment banners overlay at the bottom of the Assignments preview viewport.

### 14.1 Layout

Recommended desktop layout:

```text
┌───────────────────────────────────────────────────────────────┐
│ Assembly | Materials | Assignments                            │
├───────────────────┬──────────────────────────┬────────────────┤
│ Finish Schemes    │ Scheme Properties        │ Preview        │
│                   │                          │ (alerts bottom)│
│ Init              │ Code                     │ Current        │
│ Brass             │ Display Name             │ assembly or    │
│ Steel             │ Description              │ test object    │
│ Black             │ Active                   │                │
│                   │ Customer Visible         │                │
│ + New             │                          │                │
│                   │ Semantic Assignments     │                │
│                   │ Binding → Render Material│                │
└───────────────────┴──────────────────────────┴────────────────┘
```

The exact layout may follow the visual language of the existing Materials tab.

### 14.2 Finish Scheme List

Display:

```text
display name
code
active state
customer-visible state
```

Provide:

```text
New Finish Scheme
Delete Finish Scheme
```

The `init` scheme should be visually marked as:

```text
Internal
Static assignments
Not customer visible
```

Prevent accidental deletion of `init`, or require a strong confirmation.

### 14.3 Scheme Properties

Editable fields:

```text
code
display name
description
active
customer visible
sort order
```

The finish scheme code should be treated as a stable identifier.

Changing the code should either:

- Be blocked after creation, or
- Require explicit confirmation because assignment states may reference it as `default_finish_scheme_id`

Prefer making `code` read-only after creation for this iteration.

### 14.4 Assignment Table

Display rows:

| Semantic binding | Render material | Actions |
|---|---|---|
| `primary_metal` | `Brushed Brass` | Remove |
| `hardware_metal` | `Brushed Brass` | Remove |
| `actuator_metal` | `Brushed Brass` | Remove |

Required controls:

```text
Add Assignment
Remove Assignment
Change Render Material
Save Changes
```

The semantic binding should be entered as a plain string for v0.1.

The render material must be selected from active materials in the existing material database.

Do not duplicate material parameters in the assignment UI.

### 14.5 Binding Name Validation

Normalize binding names before saving:

```text
trim leading and trailing whitespace
convert to lowercase
replace spaces with underscores
reject empty names
```

Allowed pattern:

```regex
^[a-z][a-z0-9_]*$
```

Examples accepted:

```text
primary_metal
hardware_metal
electrical_core
usb_insert
```

Examples rejected:

```text
Primary Metal
primary-metal
 primary_metal
123_binding
```

Show a clear validation message before saving.

---

## 15. Optional Binding Discovery

Implement binding discovery if it is reasonably achievable with the current frontend architecture.

When GLB assets are loaded, collect unique imported material names:

```typescript
mesh.material.name
```

Display them in the Assignments tab under:

```text
Bindings Found in Loaded Assembly
```

Example:

```text
primary_metal
hardware_metal
actuator_metal
electrical_core
```

For each discovered binding, show status for the selected scheme:

```text
Resolved by current scheme
Resolved by init
Missing
```

Example:

| Binding | Resolution | Material |
|---|---|---|
| `primary_metal` | Current scheme | `brass_brushed` |
| `electrical_core` | Init | `black_plastic_matte` |
| `label` | Missing | — |

This feature is useful but secondary to the core CRUD and rendering implementation.

Do not write discovered bindings automatically to the database without user action.

---

## 16. Assembly Tab Changes

Replace the current user-facing `Material` selector with a `Finish` selector.

Current:

```text
MATERIAL
[Brass] [Copper] [Steel]
```

Target:

```text
FINISH
[Brass] [Steel] [Black]
```

The buttons must come from:

```text
finish_schemes
where is_active = true
and is_customer_visible = true
```

Do not build finish buttons from the `materials` table.

A finish scheme can resolve multiple render materials.

The Assembly tab resolves multi-slot assemblies via `POST /api/render/resolve`
from current UI state. Admin **Save Current State** persists geometry into
Assignment States. Finish schemes still resolve materials through
`material_assignments`. Missing geometry returns `missing_assets` without
failing the request.

---

## 17. Backend Render-State Changes

The render resolver returns semantic assignments rather than one global material.

Ad-hoc Assembly resolve:

```text
POST /api/render/resolve
```

Saved Assignment State resolve:

```text
GET /api/assignment-states/{id}/render-state?finish_scheme=
```

Example response:

```json
{
  "is_valid": true,
  "assembly": {
    "gang_count": 1,
    "modules": [
      { "slot_number": 1, "module_type": "dimmer" }
    ],
    "finish_scheme": "brass",
    "assignment_state_code": "LAT-ASG-000001",
    "assignment_state_display_name": "1-Gang Dimmer"
  },
  "active_sources": ["init", "brass"],
  "assets": [
    {
      "asset_key": "plate.1gang",
      "file": "/assets/glb/1gang_plate.glb"
    },
    {
      "asset_key": "hardware.1gang.plate_screws",
      "file": "/assets/glb/1gang_plate_screws.glb"
    },
    {
      "asset_key": "module.1gang.slot1.dimmer",
      "file": "/assets/glb/1gang_slot1_dimmer.glb"
    }
  ],
  "material_assignments": {
    "primary_metal": "brass_brushed",
    "hardware_metal": "brass_brushed",
    "actuator_metal": "brass_brushed",
    "electrical_core": "black_plastic_matte"
  },
  "materials": {
    "brass_brushed": {
      "code": "brass_brushed",
      "display_name": "Brushed Brass",
      "base_color": "#B88A44",
      "metalness": 1.0,
      "roughness": 0.45,
      "anisotropy": 0.0,
      "anisotropy_rotation": 0.5
    },
    "black_plastic_matte": {
      "code": "black_plastic_matte",
      "display_name": "Matte Black Plastic",
      "base_color": "#080808",
      "metalness": 0.0,
      "roughness": 0.72,
      "anisotropy": 0.0,
      "anisotropy_rotation": 0.0
    }
  }
}
```

The render state uses `assembly`, not `configuration`. The asset list no longer needs a material policy.

---

## 18. Three.js Semantic Material Application

Remove the production dependency on `replace_all`.

For every loaded mesh:

1. Read the imported material name.
2. Treat that name as a semantic binding.
3. Look up the binding in `material_assignments`.
4. Find the referenced render material in `materials`.
5. Apply the generated Three.js material.
6. Report missing bindings visibly.

Support meshes with:

- One material
- An array of materials

Suggested implementation structure:

```typescript
function applySemanticMaterials(
  assetRoot: THREE.Object3D,
  materialAssignments: Record<string, string>,
  renderMaterialsByCode: Map<string, THREE.Material>
): MaterialApplicationResult {
  const missingBindings = new Set<string>();

  assetRoot.traverse((sceneObject: THREE.Object3D) => {
    if (!(sceneObject instanceof THREE.Mesh)) {
      return;
    }

    const originalMaterials = Array.isArray(sceneObject.material)
      ? sceneObject.material
      : [sceneObject.material];

    const resolvedMaterials = originalMaterials.map(
      (originalMaterial: THREE.Material): THREE.Material => {
        const bindingName = originalMaterial.name.trim().toLowerCase();
        const renderMaterialCode = materialAssignments[bindingName];

        if (!renderMaterialCode) {
          missingBindings.add(bindingName);
          return createMissingBindingMaterial(bindingName);
        }

        const resolvedMaterial =
          renderMaterialsByCode.get(renderMaterialCode);

        if (!resolvedMaterial) {
          missingBindings.add(bindingName);
          return createMissingBindingMaterial(bindingName);
        }

        return resolvedMaterial;
      }
    );

    sceneObject.material = Array.isArray(sceneObject.material)
      ? resolvedMaterials
      : resolvedMaterials[0];
  });

  return {
    missingBindings: Array.from(missingBindings).sort(),
  };
}
```

Follow the existing project architecture rather than putting all logic into one component.

Create a dedicated service or utility for semantic material application.

---

## 19. Missing Assignment Material

Create a clear fallback material for errors.

Recommended appearance:

```text
bright magenta
non-metallic
medium roughness
```

Example:

```typescript
function createMissingBindingMaterial(
  bindingName: string
): THREE.MeshStandardMaterial {
  const missingBindingMaterial = new THREE.MeshStandardMaterial({
    color: 0xff00ff,
    metalness: 0.0,
    roughness: 0.5,
  });

  missingBindingMaterial.name = `missing_binding:${bindingName}`;

  return missingBindingMaterial;
}
```

When a binding is missing:

- Render the affected geometry in magenta
- Show a visible warning at the bottom of the 3D viewport
- Include the binding name and asset/slot context where available
- Do not silently leave the Houdini placeholder material
- Do not silently apply the first selected finish material

Example warning:

```text
Missing material assignments
brass + electrical_core — plate
```

The assembly may still render, but its validation status must show a material-assignment error.

Missing geometry (unregistered GLB keys) is a separate warning class and uses
neutral placeholders — not magenta.

---

## 20. Validation Service

Add material validation to assembly resolution.

For all semantic names found in currently loaded assembly assets, verify that each resolves through:

```text
selected finish scheme
or
init
```

Because the backend may not inspect GLB contents directly, support two levels:

### Frontend Runtime Validation

Required:

- Detect material names during GLB traversal
- Report missing names
- Show error material

### Backend Assignment Validation

Required:

- Verify assignment rows reference existing active materials
- Verify selected finish scheme exists and is active
- Verify `init` exists and is active

Optional later:

- Build an asset-inspection process that registers discovered semantic names for backend validation

Do not put semantic-binding lists back into the asset manifest merely to enable validation.

---

## 21. Material Deletion Rules

Update the existing Materials tab deletion behavior.

Before deleting a material:

1. Check whether `material_assignments` references it.
2. If referenced, block deletion.
3. Show the schemes and bindings that use it.

Example:

```text
Cannot delete “Brushed Brass”.

It is used by:
Brass → primary_metal
Brass → hardware_metal
Brass → actuator_metal
```

The user must reassign or delete those mappings first.

Deleting an inactive, unreferenced material is allowed.

---

## 22. Finish Scheme Deletion Rules

Before deleting a finish scheme:

- Block deletion of `init`
- Block deletion if any assignment state uses it as \default_finish_scheme_id- Delete the scheme’s assignment rows through cascade only after validation

For this iteration, prefer blocking deletion when assignment states reference the scheme as their default finish.

---

## 23. Seed Data

Seed or migrate the database with enough data to demonstrate the system.

### Render Materials

Create or reuse:

```text
brass_brushed
stainless_steel_brushed
black_plastic_matte
missing_material_binding
```

Optional:

```text
black_steel_brushed
copper_brushed
white_print
```

### Finish Schemes

```text
init
brass
steel
```

### Assignments

```text
init + electrical_core → black_plastic_matte
init + insulator → black_plastic_matte

brass + primary_metal → brass_brushed
brass + hardware_metal → brass_brushed
brass + actuator_metal → brass_brushed

steel + primary_metal → stainless_steel_brushed
steel + hardware_metal → stainless_steel_brushed
steel + actuator_metal → stainless_steel_brushed
```

Adjust the exact bindings to match semantic names exported in the current GLB files.

---

## 24. Migration Strategy

Implement the change in stages so the application remains usable.

### Stage 1 — Database and CRUD

Add:

```text
finish_schemes
material_assignments
assignment_states
assignment_state_modules
Assignments tab
```

Keep existing rendering temporarily.

### Stage 2 — Export Semantic GLBs

Update current Houdini assets so their imported material names are semantic bindings.

Suggested first bindings:

```text
1gang_plate.glb:
primary_metal

1gang_plate_screws.glb:
hardware_metal

1gang_slot1_dimmer.glb:
actuator_metal
electrical_core, if visible

1gang_slot1_switch.glb:
actuator_metal
electrical_core, if visible
```

### Stage 3 — Semantic Rendering

Switch the frontend from global `replace_all` rendering to semantic assignment.

### Stage 4 — Finish Selector Migration

Replace the Assembly material selector with finish schemes.

### Stage 5 — Remove Legacy Policy

After all current assets use semantic names and tests pass:

- Remove `material_policy` from the manifest
- Remove `replace_all` application logic
- Remove obsolete direct-material-selection fields from legacy code paths

Do not preserve unused compatibility code indefinitely.

---

## 25. UI Preview Behavior

When editing an assignment in the `Assignments` tab:

- Update the preview after saving
- The preview may use the active assembly
- The selected scheme should be applied through the same resolver used by the Assembly tab
- Do not create a separate material-resolution implementation for the admin preview

One resolver must drive:

```text
Assembly preview
Assignments preview
Assignment State render-state endpoint
exported render state
```

---

## 26. Exported Assembly JSON

Export the structured public assembly. Geometry state names omit finish:

```json
{
  "schema_version": 1,
  "gang_count": 1,
  "finish_scheme_code": "brass",
  "slots": [
    { "slot_number": 1, "module_type_code": "dimmer" }
  ],
  "state_name": "dimmer",
  "debug": {
    "assets": [
      "plate.1gang",
      "hardware.1gang.plate_screws",
      "module.1gang.slot1.dimmer"
    ],
    "missing_assets": [],
    "resolved_material_assignments": {},
    "prototype_bom": []
  }
}
```

The export is a snapshot for debugging and reproducibility. Persisted viewport
assemblies live in Assignment States (via Save Current State); the public
Assembly UI does not require an assignment state while editing.

---
## 27. Tests

### 27.1 Backend Tests

Create tests for:

```text
Create finish scheme
Update finish scheme
Delete unused finish scheme
Block deletion of init
Block deletion of finish scheme when assignment states reference it as default
Block duplicate finish-scheme code
Create assignment
Update assignment
Delete assignment
Block duplicate finish_scheme + binding_name
Block assignment to missing material
Block material deletion when assignments reference it
Resolve init assignments
Resolve selected finish-scheme assignments
Selected scheme overrides init for matching binding
Inactive finish scheme cannot be selected
Customer-visible list excludes init
```

### 27.2 Frontend Tests

Test:

```text
Assignments tab loads schemes
Selecting a scheme loads its assignments
New assignment can be added
Assignment material can be changed
Assignment can be removed
Invalid binding name is rejected
Assembly finish buttons come from finish schemes
Init is not shown in Assembly
Semantic bindings apply correct materials
Missing binding uses magenta material
Missing binding warning is visible
Meshes with material arrays resolve correctly
```

### 27.3 Manual Test Assemblies

Test at least:

```text
Dimmer + Brass
Dimmer + Steel
Switch + Brass
Switch + Steel
```

Verify:

```text
plate material changes
screw material changes
actuator material changes
static electrical-core material remains unchanged
Assignment State loads and resolves with independent finish scheme
JSON export includes finish scheme and assembly modules
```

---

## 28. Error Handling

Handle these cases explicitly:

```text
init scheme is missing
selected finish scheme is missing
selected finish scheme is inactive
assignment references deleted material
GLB material name is empty
GLB material name has no assignment
render material definition is inactive
duplicate assignment exists
database migration fails
```

Do not fail silently.

Example UI messages:

```text
Semantic material name is empty on mesh “geo_plate_body”.

No assignment exists for binding “primary_metal”
under finish scheme “Brass” or “Initialization”.

Render material “brass_brushed” does not exist.
```

---

## 29. Non-Goals

Do not implement these in this iteration:

```text
Generalized automotive code-state engine
Multiple arbitrary active finish schemes
Collection-level override states
Product-level override states
Configuration-specific material overrides
Material assignments in asset_manifest.json
Automatic GLB rewriting
Automatic database assignment creation from discovered names
Per-polygon custom metadata outside native GLB material assignments
Direct render-material names stored on geometry
Customer-facing assignment editor
Cloud deployment
User authentication
```

The flat table is intentional:

```text
finish_scheme + binding_name → render_material
```

---

## 30. Acceptance Criteria

The implementation is complete when:

1. The application has Assembly, Materials, and Assignments tabs (Assignment States are presets, not a separate top-level tab).
2. Finish schemes can be created, edited, enabled, disabled, and deleted under the defined rules.
3. Semantic assignments can be created, edited, and removed.
4. Assignments are stored in SQLite.
5. Each assignment maps one finish scheme and one binding name to one render material.
6. Duplicate assignments for the same scheme and binding are prevented.
7. The asset manifest contains no material-policy or binding data.
8. GLB material names are treated as semantic bindings.
9. The Assembly tab shows customer-visible finish schemes instead of render materials.
10. The backend combines `init` with the selected finish scheme.
11. The selected finish scheme overrides `init` for duplicate binding names.
12. Three.js applies materials per semantic binding.
13. Static geometry materials resolve through `init`.
14. Dynamic geometry materials resolve through the selected finish scheme.
15. Missing assignments render in magenta and produce visible errors.
16. Materials referenced by assignments cannot be deleted.
17. Finish scheme deletion is blocked when assignment states use it as default.
18. Assignment States persist viewport assemblies for the Assignments tab.
19. Render state uses `assembly`, resolved via `/api/render/resolve` or assignment-state render-state.
20. Existing dimmer/switch and brass/steel assemblies work.
21. No material assignment logic is duplicated in the asset manifest.
22. The existing global `replace_all` system is removed after migration.

---

## 31. Guiding Principles

```text
Geometry stores semantic names.

The database stores semantic-to-render-material assignments.

Finish schemes are customer-visible choices.

Render materials are implementation-level shader definitions.

Static assignments belong to init.

Dynamic assignments belong to customer finish schemes.

The asset manifest only locates geometry files.

The backend resolves product meaning.

The frontend applies the resolved result.

Missing assignments must be obvious.

Do not silently guess.
```