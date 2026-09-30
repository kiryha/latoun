# Latoun Asset Manifest Editor — Coding Agent Brief

> **Update (v0.2) — manifest shape.** The manifest now has two root keys:
> `properties` (shared data) and `parts` (the entry map). The GLB folder is
> stored **once** as `properties.glb_folder` (a relative public URL prefix,
> e.g. `/assets/wall_plates/`), and each entry's `file` holds only the **bare
> file name** (e.g. `1gang_plate.glb`). The backend joins
> `glb_folder + file` into the full public URL when resolving render state, so
> anything downstream (viewport/assembly) still sees a full URL. The
> `frontend/public` filesystem base is **not** stored in the manifest — it is a
> backend constant (`settings.repository_root / "frontend" / "public"`) derived
> at runtime, so the repo stays portable (no absolute machine paths anywhere).
> Legacy manifests that stored a full path in `file` migrate automatically:
> `file` is reduced to its basename on load. Older inline examples below that
> show a full path inside `file` predate v0.2; read them as `glb_folder` +
> basename.
>
> Current shape:
>
> ```json
> {
>   "properties": { "glb_folder": "/assets/wall_plates/" },
>   "parts": {
>     "plate.1gang": {
>       "category": "plate",
>       "gang_count": 1,
>       "file": "1gang_plate.glb",
>       "is_active": true
>     }
>   }
> }
> ```

## 1. Objective

Add a new **Geometry** tab to the Latoun configurator for managing the wall-plate GLB asset manifest without editing JSON manually in an IDE.

Current tabs:

```text
Assembly | Materials | Assignments
```

New tab order:

```text
Assembly | Geometry | Materials | Assignments
```

The Geometry tab is an internal/admin tool.

The application currently operates entirely in admin mode, so user accounts, authentication, and permission checks are outside the scope of this task. The Geometry tab should be structured so it can later be hidden from public users.

The tool must:

- Read the wall-plate asset manifest.
- Display all manifest entries.
- Add new entries.
- Edit existing entries.
- Duplicate entries.
- Delete manifest entries without deleting GLB files.
- Enable or disable manifest entries.
- Generate entries for gang and slot combinations.
- Preview one GLB asset at a time.
- Display semantic material names found in the selected GLB.
- Optionally allow selecting a mesh in the viewport to inspect its properties.
- Track multiple unsaved changes.
- Write the complete JSON file only when the user clicks **Save Manifest**.
- Preserve a clear separation between manifest editing and GLB file management.

The Geometry tool must not upload, move, rename, replace, or delete GLB files.

---

## 2. Read the Existing Repository First

Before implementation:

1. Read the project README.
2. Inspect the existing tab and navigation implementation.
3. Inspect the current Assembly tab.
4. Inspect the existing Three.js viewport and GLB loader.
5. Inspect the current asset-manifest reader.
6. Inspect the current asset resolver used by Assembly.
7. Inspect the FastAPI backend structure.
8. Inspect the SQLAlchemy setup.
9. Inspect the existing `module_types` database model and API.
10. Search the repository for references to:

```text
/config/asset_manifest.json
/assets/glb/
schema_version
coordinate_space
category
slot_module
plate_screws
```

11. Follow the repository's established conventions for:

```text
React
TypeScript
FastAPI
Pydantic
SQLAlchemy
Three.js
API routing
error handling
testing
styling
```

Do not redesign unrelated systems.

---

## 3. New File Locations

Move the manifest reference from:

```text
/config/asset_manifest.json
```

to:

```text
/config/wall_plates/asset_manifest.json
```

The GLB asset root becomes:

```text
/public/assets/wall_plates/
```

All GLB files will be stored directly in that folder.

Do not create subfolders such as:

```text
plates/
screws/
modules/
hardware/
```

Example physical files:

```text
/public/assets/wall_plates/1gang_plate.glb
/public/assets/wall_plates/1gang_plate_screws.glb
/public/assets/wall_plates/1gang_slot1_switch.glb
/public/assets/wall_plates/1gang_slot1_dimmer.glb
/public/assets/wall_plates/2gang_slot1_switch.glb
/public/assets/wall_plates/2gang_slot2_switch.glb
```

Manifest paths must use public URL paths:

```text
/assets/wall_plates/1gang_plate.glb
/assets/wall_plates/1gang_slot1_switch.glb
```

The user will move the existing GLB files manually.

The coding agent must:

- update the application to use the new paths;
- update the existing manifest entries;
- update code references to the old manifest location;
- update code references to `/assets/glb/`.

Do not move GLB files as part of this task.

---

## 4. Current Manifest

The current manifest is:

```json
{
  "schema_version": 2,
  "assets": {
    "plate.1gang": {
      "category": "plate",
      "file": "/assets/glb/1gang_plate.glb",
      "coordinate_space": "assembly_origin"
    },
    "hardware.1gang.plate_screws": {
      "category": "hardware",
      "file": "/assets/glb/1gang_plate_screws.glb",
      "coordinate_space": "assembly_origin"
    },
    "module.1gang.slot1.dimmer": {
      "category": "slot_module",
      "module_type": "dimmer",
      "slot_position": 1,
      "file": "/assets/glb/1gang_slot1_dimmer.glb",
      "coordinate_space": "assembly_origin"
    },
    "module.1gang.slot1.switch": {
      "category": "slot_module",
      "module_type": "switch",
      "slot_position": 1,
      "file": "/assets/glb/1gang_slot1_switch.glb",
      "coordinate_space": "assembly_origin"
    }
  }
}
```

The Geometry editor must support migration of this structure.

---

## 5. Manifest Scope

This manifest belongs specifically to the wall-plate product family.

It is not intended to become a universal manifest for every future Latoun product.

Future product families may have separate manifests, for example:

```text
/config/wall_plates/asset_manifest.json
/config/door_hardware/asset_manifest.json
/config/table_lamps/asset_manifest.json
```

Do not attempt to design a universal asset database in this task.

The Geometry tab may initially be fixed to:

```text
wall_plates
```

However, avoid naming components and services so narrowly that they cannot later accept another product-family manifest.

Good internal names:

```text
GeometryTab
AssetManifestEditor
AssetManifestService
ManifestEntryEditor
GeometryPreview
```

Avoid unnecessary global abstractions.

---

## 6. Keep JSON as the Source of Truth

The JSON file remains the authoritative source for geometry asset records.

Do not create an asset-manifest database table.

The data flow is:

```text
Geometry tab
    ↓
load JSON manifest through backend
    ↓
edit an in-memory working copy
    ↓
validate working copy
    ↓
Save Manifest
    ↓
backend atomically rewrites JSON file
    ↓
Assembly uses updated manifest
```

The manifest must remain committed to the repository and reviewable in Git.

---

## 7. Schema Version

The current manifest includes:

```json
"schema_version": 2
```

The product owner does not want to maintain explicit JSON schema versioning.

Remove:

```json
"schema_version": 2
```

from the new manifest unless existing application compatibility makes immediate removal unsafe.

Preferred final root structure:

```json
{
  "assets": {
  }
}
```

The backend must still validate the expected structure even without a version field.

Do not introduce a replacement version field such as:

```text
version
manifest_version
format_version
schema
```

---

## 8. Remove `coordinate_space`

Remove this field from all manifest entries:

```json
"coordinate_space": "assembly_origin"
```

The wall-plate asset contract is already defined:

- every GLB is authored in assembly coordinates;
- every GLB is loaded with identity transforms;
- the filename and manifest entry determine which gang and slot it belongs to.

Do not expose `coordinate_space` in the Geometry editor.

Do not write it to new manifest entries.

Remove code that depends on it if it is no longer required.

---

## 9. Asset Identity and Manifest Keys

The JSON object key remains the unique asset identifier.

Examples:

```text
plate.1gang
hardware.1gang.plate_screws
module.1gang.slot1.switch
module.1gang.slot1.dimmer
module.2gang.slot2.outlet
```

The Geometry editor must display and allow editing of the manifest key.

The key must be:

- non-empty;
- unique;
- stable;
- human-readable;
- suitable for lookup by application code.

The editor may suggest or auto-generate keys, but the user must be able to review and edit the result before saving.

Recommended key patterns:

### Plate

```text
plate.{gang}gang
```

Examples:

```text
plate.1gang
plate.2gang
plate.3gang
plate.4gang
```

### Plate screws

```text
hardware.{gang}gang.plate_screws
```

Examples:

```text
hardware.1gang.plate_screws
hardware.4gang.plate_screws
```

### Slot module

```text
module.{gang}gang.slot{slot}.{module-type-code}
```

Examples:

```text
module.1gang.slot1.switch
module.2gang.slot1.dimmer
module.2gang.slot2.usb_c_outlet
module.4gang.slot4.outlet
```

Slot numbers are unpadded because supported assemblies have only a small,
bounded number of slots. Legacy `slot01`–`slot04` keys remain readable; new
entries use `slot1`–`slot4`.

Do not make the application depend solely on parsing the key. The entry fields remain authoritative for asset resolution.

---

## 10. Asset Categories

There is currently no database table for asset categories.

Keep a small fixed list of manifest asset categories in the application:

```text
plate
hardware
slot_module
```

These values correspond to the current manifest structure.

Display names:

```text
Plate
Hardware
Slot Module
```

For the current wall-plate product, `hardware` is used for the plate screw asset.

Do not create a `category` database table in this task.

Do not treat the product family `wall_plates` as a category.

The relationship is:

```text
product family: wall_plates

asset categories:
- plate
- hardware
- slot_module
```

> **Terminology note (field renamed).** The manifest field that records this
> category was originally named `asset_type`. It is now named `category` to
> avoid colliding with the notion of a product "asset" / product family. The
> backend accepts the legacy `asset_type` key on load for backward
> compatibility and rewrites it as `category` on the next save. There is no
> product-family "asset" table, and there is no `asset_types` table — the
> application assumes a single product (`wall_plates`).

> **Two independent axes — do not conflate them.** `category`
> (`plate` / `hardware` / `slot_module`) describes *what kind of part* an entry
> is. `module_type` (`switch` / `dimmer` / `outlet` / `usb_c_outlet`, from the
> database) only sub-types a `slot_module`. A **plate is a category, not a
> module type** — never add `plate` to the `module_types` table, because module
> types are slot devices and a plate is the substrate that holds the slots.

---

## 11. Recommended Manifest Entry Shapes

### Plate

```json
"plate.1gang": {
  "category": "plate",
  "gang_count": 1,
  "file": "/assets/wall_plates/1gang_plate.glb",
  "is_active": true
}
```

### Plate screws

```json
"hardware.1gang.plate_screws": {
  "category": "hardware",
  "hardware_type": "plate_screws",
  "gang_count": 1,
  "file": "/assets/wall_plates/1gang_plate_screws.glb",
  "is_active": true
}
```

### Slot module

```json
"module.1gang.slot1.switch": {
  "category": "slot_module",
  "gang_count": 1,
  "module_type": "switch",
  "slot_position": 1,
  "file": "/assets/wall_plates/1gang_slot1_switch.glb",
  "is_active": true
}
```

Use numeric:

```text
gang_count
slot_position
```

Do not derive all structured data from filenames.

---

## 12. Gang Count

Add an explicit `gang_count` field to every manifest entry.

Supported values:

```text
1
2
3
4
```

The old entries encode gang count only in their keys and filenames. Migrate them to include an explicit numeric field.

Examples:

```json
"gang_count": 1
```

```json
"gang_count": 4
```

The Geometry editor must provide a dropdown or segmented selector for:

```text
1 Gang
2 Gang
3 Gang
4 Gang
```

---

## 13. Active State

Add:

```json
"is_active": true
```

to manifest entries.

The Geometry editor must allow an entry to be enabled or disabled.

Inactive entries:

- remain in the JSON file;
- remain editable;
- appear in the Geometry tab;
- must not be returned by the normal Assembly asset resolver;
- must be clearly marked in the manifest table;
- may still be previewed in the Geometry tab.

Default for newly created entries:

```json
"is_active": true
```

For backward compatibility, if `is_active` is missing while loading an older entry, treat it as:

```text
true
```

The next save should normalize the entry and write the field explicitly.

---

## 14. Module Types Must Come From the Database

The Geometry editor must not hard-code module type strings.

Load module types from the existing SQLite `module_types` table.

> `module_types` holds only slot devices. Do not add `plate` (or `hardware`)
> as a module type: those are `category` values, a separate axis from
> `module_type`.

Current records include:

| code | display name |
|---|---|
| `switch` | Switch |
| `dimmer` | Dimmer |
| `outlet` | Outlet |
| `usb_c_outlet` | USB-C Outlet |

Relevant existing fields:

```text
module_type_id
code
display_name
is_active
is_customer_visible
sort_order
```

The Geometry tab should retrieve module types through an existing API if one is available.

If no suitable API exists, add a read-only endpoint.

Suggested response:

```json
[
  {
    "module_type_id": 1,
    "code": "switch",
    "display_name": "Switch",
    "is_active": true,
    "is_customer_visible": true,
    "sort_order": 10
  },
  {
    "module_type_id": 2,
    "code": "dimmer",
    "display_name": "Dimmer",
    "is_active": true,
    "is_customer_visible": true,
    "sort_order": 20
  }
]
```

Sort by:

```text
sort_order
```

The manifest stores the module type's stable `code`, not its database ID:

```json
"module_type": "switch"
```

The UI dropdown displays:

```text
Switch
Dimmer
Outlet
USB-C Outlet
```

Do not allow arbitrary free-text module type values.

Inactive module types may be displayed for existing manifest records, but they should be clearly marked as inactive.

New slot-module entries should normally use active module types.

---

## 15. Geometry Tab Layout

Recommended layout:

```text
GEOMETRY

Toolbar
Filters
Manifest entries
Entry editor
3D preview
Validation panel
Save controls
```

A practical desktop arrangement:

```text
┌─────────────────────────────────────────────────────────────┐
│ Geometry Manifest                        Save Manifest       │
│ Unsaved changes: 4                       Discard Changes     │
├─────────────────────────────────────────────────────────────┤
│ Filters / Search                                             │
├──────────────────────────────┬──────────────────────────────┤
│ Manifest entries             │ Selected entry editor        │
│                              │                              │
│                              ├──────────────────────────────┤
│                              │ 3D preview                   │
│                              │                              │
├──────────────────────────────┴──────────────────────────────┤
│ Validation and warnings                                     │
└─────────────────────────────────────────────────────────────┘
```

Reuse the application's existing visual language.

---

## 16. Manifest Entries Table

Display all manifest entries in a table.

Recommended columns:

| Column | Purpose |
|---|---|
| Active | Enabled or disabled state |
| Manifest Key | Unique JSON object key |
| Category | Plate, Hardware, or Slot Module |
| Gang | 1–4 |
| Slot | Slot number for module assets |
| Module Type | Database-backed module type |
| Hardware Type | For hardware assets |
| File | Public GLB path |
| Status | Valid, warning, missing file, duplicate |
| Actions | Edit, duplicate, delete |

The table should support:

- row selection;
- sorting;
- text search;
- filters;
- clear indication of unsaved modifications;
- clear indication of newly added entries;
- clear indication of entries marked for deletion.

Recommended filters:

```text
Category
Gang Count
Module Type
Active / Inactive
Validation Status
Search
```

Search should match at least:

```text
manifest key
file path
module type code
module type display name
```

---

## 17. Entry Editor

Selecting a row opens the entry editor.

Common fields:

```text
Manifest Key
Category
Gang Count
GLB File Path
Active
```

Conditional fields depend on `category`.

### Plate fields

```text
Manifest Key
Category = Plate
Gang Count
GLB File Path
Active
```

Do not show:

```text
Slot Position
Module Type
Hardware Type
```

### Hardware fields

```text
Manifest Key
Category = Hardware
Hardware Type
Gang Count
GLB File Path
Active
```

For the first implementation, the supported hardware type is:

```text
plate_screws
```

Display name:

```text
Plate Screws
```

This can be a fixed dropdown rather than free text.

### Slot-module fields

```text
Manifest Key
Category = Slot Module
Gang Count
Slot Position
Module Type
GLB File Path
Active
```

Module Type must be selected from the database-backed dropdown.

---

## 18. Slot Position Rules

For a slot module:

```text
slot_position >= 1
slot_position <= gang_count
```

Allowed values should update based on the selected gang count.

Examples:

```text
1-gang → slot 1
2-gang → slots 1–2
3-gang → slots 1–3
4-gang → slots 1–4
```

Slots are numbered left-to-right.

If the user reduces gang count and the current slot is no longer valid, the UI must require correction before saving.

Do not silently change a selected slot unless the behavior is clearly communicated.

---

## 19. GLB File Path Editing

Store complete public asset paths:

```text
/assets/wall_plates/example.glb
```

Do not store only the filename.

The path field should be editable text, but provide useful assistance.

Recommended behavior:

- default prefix:

```text
/assets/wall_plates/
```

- default extension:

```text
.glb
```

- warn if the path does not start with:

```text
/assets/wall_plates/
```

- warn if the path does not end with:

```text
.glb
```

- warn if the file cannot be loaded;
- do not prevent saving solely because a GLB does not exist yet.

Some entries will intentionally be created before their GLB files are authored.

Distinguish:

```text
invalid manifest data
```

from:

```text
valid manifest entry with missing GLB file
```

A missing GLB is a warning, not necessarily a blocking validation error.

---

## 20. Add Entry

Provide:

```text
Add Entry
```

The user chooses a category:

```text
Plate
Hardware
Slot Module
```

Create a draft entry with sensible defaults.

### New plate default

```json
{
  "category": "plate",
  "gang_count": 1,
  "file": "/assets/wall_plates/",
  "is_active": true
}
```

### New hardware default

```json
{
  "category": "hardware",
  "hardware_type": "plate_screws",
  "gang_count": 1,
  "file": "/assets/wall_plates/",
  "is_active": true
}
```

### New slot-module default

```json
{
  "category": "slot_module",
  "gang_count": 1,
  "module_type": "switch",
  "slot_position": 1,
  "file": "/assets/wall_plates/",
  "is_active": true
}
```

Use the first active module type ordered by `sort_order` as the default if appropriate.

New entries remain client-side until **Save Manifest** is clicked.

---

## 21. Edit Entry

Editing a field updates the in-memory working manifest.

Do not immediately write to disk.

Clearly mark edited rows.

The user should be able to move between rows without losing unsaved changes.

Changing `category` must:

- update visible fields;
- remove fields that are not valid for the new type;
- create required defaults for newly relevant fields;
- trigger validation;
- never leave stale incompatible fields in the saved output.

Example:

Changing:

```text
slot_module → plate
```

must remove:

```text
module_type
slot_position
```

from the saved entry.

---

## 22. Duplicate Entry

Provide:

```text
Duplicate
```

Duplicating creates a new client-side entry based on the selected record.

The duplicate must not retain the exact same manifest key.

Suggested behavior:

```text
module.2gang.slot1.switch
```

becomes a temporary key such as:

```text
module.2gang.slot1.switch.copy
```

or opens immediately with the key field requiring correction.

The duplicate should preserve:

```text
category
gang_count
slot_position
module_type
hardware_type
file
is_active
```

The user must resolve duplicate lookup identity before saving.

---

## 23. Delete Entry

Provide:

```text
Delete Entry
```

Deleting means:

- remove the entry from the JSON manifest on the next save;
- do not delete the GLB file;
- do not move the GLB file;
- do not rename the GLB file.

Before marking an entry for deletion, show a confirmation such as:

```text
Remove this entry from the asset manifest?

The GLB file will not be deleted.
```

The deletion remains part of the unsaved working changes until **Save Manifest**.

Allow the user to undo the deletion before saving.

---

## 24. Enable and Disable

Allow toggling:

```text
is_active
```

directly from either:

- the table; or
- the entry editor.

An inactive entry remains in the manifest.

The Assembly resolver must ignore inactive entries.

The Geometry preview may still load an inactive entry.

---

## 25. Bulk Generation Tool

The user needs to populate the manifest to production scale for:

- all gang counts;
- all valid slot positions;
- all module types from the database;
- plates;
- plate screw sets.

Add a tool such as:

```text
Generate Wall-Plate Entries
```

This tool generates missing manifest entries without overwriting existing entries.

### Required plate entries

```text
plate.1gang
plate.2gang
plate.3gang
plate.4gang
```

### Required hardware entries

```text
hardware.1gang.plate_screws
hardware.2gang.plate_screws
hardware.3gang.plate_screws
hardware.4gang.plate_screws
```

### Required slot-module entries

For every gang count:

```text
gang_count = 1, 2, 3, 4
```

For every valid slot:

```text
slot_position = 1 through gang_count
```

For every selected module type from the database:

```text
switch
dimmer
outlet
usb_c_outlet
```

Example for 2-gang:

```text
module.2gang.slot1.switch
module.2gang.slot1.dimmer
module.2gang.slot1.outlet
module.2gang.slot1.usb_c_outlet

module.2gang.slot2.switch
module.2gang.slot2.dimmer
module.2gang.slot2.outlet
module.2gang.slot2.usb_c_outlet
```

Using the four current module types, the complete generated set is:

```text
4 plate entries
4 plate-screw entries
40 slot-module entries
48 total entries
```

The slot-module count is:

```text
(1 + 2 + 3 + 4) slots × 4 module types = 40
```

---

## 26. Bulk Generation Dialog

The generation tool should show a confirmation/configuration dialog.

Recommended options:

```text
Generate plates
Generate plate screws
Generate slot modules
Module types to include
Gang counts to include
Activate generated entries
```

Default:

```text
all gang counts
all active module types
all categories selected
generated entries active
```

Show a preview before applying:

```text
New entries to create: 42
Existing entries preserved: 6
Conflicts requiring review: 0
```

The tool must:

- create only missing entries;
- not overwrite existing entries;
- not reset existing file paths;
- not reset active states;
- not remove custom entries;
- treat generated entries as unsaved changes until Save Manifest.

---

## 27. Generated Filenames

Generate predictable default filenames.

### Plate

```text
{gang}gang_plate.glb
```

Example:

```text
/assets/wall_plates/3gang_plate.glb
```

### Plate screws

```text
{gang}gang_plate_screws.glb
```

Example:

```text
/assets/wall_plates/4gang_plate_screws.glb
```

### Slot modules

```text
{gang}gang_slot{slot}_{module-type-code}.glb
```

Examples:

```text
/assets/wall_plates/1gang_slot1_switch.glb
/assets/wall_plates/2gang_slot2_dimmer.glb
/assets/wall_plates/3gang_slot1_outlet.glb
/assets/wall_plates/4gang_slot4_usb_c_outlet.glb
```

Use unpadded slots:

```text
slot1
slot2
slot3
slot4
```

Do not replace underscores in database module codes unless there is an established repository naming convention requiring it.

---

## 28. Resolver Identity and Duplicate Validation

The manifest must not contain two active entries that resolve to the same assembly requirement.

### Plate resolver identity

```text
category = plate
gang_count
```

Only one active plate entry may exist for each gang count.

### Hardware resolver identity

```text
category = hardware
hardware_type
gang_count
```

Only one active plate-screw entry may exist for each gang count.

### Slot-module resolver identity

```text
category = slot_module
gang_count
slot_position
module_type
```

Only one active entry may exist for each combination.

Example conflict:

```text
2-gang
slot 1
switch
```

must not resolve to two active GLB paths.

Inactive duplicates may be allowed, but they should still produce a warning because reactivating one could create a conflict.

The application resolver must use structured entry fields, not rely only on key or filename conventions.

---

## 29. 3D Preview

Selecting a manifest entry should attempt to load its GLB into a preview viewport.

The preview is for inspection only.

It must not:

- modify geometry;
- edit transforms;
- edit GLB materials;
- save GLB changes;
- upload or replace GLB files.

Recommended preview controls:

```text
Orbit
Pan
Zoom
Frame asset
Reset camera
Toggle grid
Toggle axes
```

Reuse the current Three.js renderer, camera, controls, loaders, lighting, and environment where practical.

Do not unnecessarily create a second rendering framework.

---

## 30. Preview Scene Behavior

Load only the selected GLB.

Do not assemble it automatically with other wall-plate parts in the first version.

An isolated preview is useful for checking:

- orientation;
- scale;
- pivot;
- geometry;
- object hierarchy;
- semantic material names.

When the selected manifest row changes:

1. dispose of the previous preview asset;
2. load the newly selected path;
3. frame the new asset;
4. show load status;
5. report errors without crashing the Geometry tab.

Handle resource cleanup correctly:

```text
geometries
materials created for preview
textures
object references
event listeners
```

Do not dispose of shared application materials or resources incorrectly.

---

## 31. Preview Load States

Display clear states:

```text
No entry selected
Loading GLB
GLB loaded
GLB file not found
GLB parse error
Invalid path
```

A failed preview must not invalidate the entire manifest editor.

Example warning:

```text
Could not load:
/assets/wall_plates/3gang_slot2_outlet.glb

The manifest entry may still be saved because geometry can be added later.
```

---

## 32. Semantic Material Inspection

The preview must inspect semantic material names exported in the GLB.

The current runtime semantic binding is derived from:

```typescript
normalizeSemanticBindingName(mesh.material.name)
```

Display a list containing at least:

```text
Object / Mesh Name
Semantic Material Name
```

Example:

| Mesh | Semantic Material |
|---|---|
| `plate_body` | `primary_metal` |
| `screw_01` | `hardware_metal` |
| `switch_core` | `electrical_core` |

For multi-material meshes, display all material names.

Do not resolve these names into finish materials in this panel unless reusing the existing rendering system requires it.

The purpose of this inspector is to verify which semantic bindings are present in the GLB.

---

## 33. Optional Mesh Selection

Implement mesh selection if it can be added cleanly without destabilizing the viewport.

Preferred behavior:

1. The user clicks a mesh in the preview.
2. The selected mesh is highlighted.
3. A properties panel displays:

```text
Object name
Mesh name
Material index
Semantic material name
Geometry vertex count
Geometry triangle count
Parent object path
```

The critical property is:

```text
Semantic Material Name
```

This corresponds to the leaf name of the Houdini material referenced by
`shop_materialpath`. For example, an exported glTF material name of
`/mat/primary_metal` is displayed and resolved as `primary_metal`.

Do not imply that `shop_materialpath` survives in the GLB as a raw Houdini attribute unless the current export pipeline explicitly preserves it.

In this application, inspect the resulting GLB semantic name through:

```typescript
normalizeSemanticBindingName(mesh.material.name)
```

Mesh picking is desirable but secondary to:

- manifest editing;
- validation;
- saving;
- basic GLB preview;
- semantic material listing.

If mesh picking is deferred, document it clearly in the implementation notes.

---

## 34. Preview Metadata

After a GLB loads, display useful read-only metadata:

```text
File path
Load status
Object count
Mesh count
Semantic material names
Bounding-box dimensions
Scene hierarchy
```

Nice-to-have values:

```text
Vertex count
Triangle count
Animation count
Texture count
File size, if available from the backend
```

Do not make optional metadata a blocker for the core task.

---

## 35. Unsaved Working Copy

When the Geometry tab loads:

```text
saved manifest
    ↓
deep-copy
    ↓
working manifest
```

All changes operate on the working copy.

Track:

```text
added entries
edited entries
duplicated entries
deleted entries
active-state changes
bulk-generated entries
```

The tab should show a clear dirty state:

```text
Unsaved changes
```

Optionally show a count:

```text
12 unsaved changes
```

Do not send a write request for every field edit.

---

## 36. Save Manifest

Provide a primary action:

```text
Save Manifest
```

Save behavior:

1. Validate the complete working manifest.
2. Block saving if there are structural errors.
3. Allow saving with non-blocking missing-file warnings after confirmation.
4. Send the complete manifest to the backend.
5. Backend validates it independently.
6. Backend writes it atomically.
7. Backend returns the normalized saved manifest.
8. Frontend replaces its baseline and working copy with the saved response.
9. Dirty state is cleared.
10. Assembly must use the newly saved manifest.

Do not trust frontend validation alone.

---

## 37. Atomic File Writing

The backend must not write directly over the existing file in a way that could leave malformed or partially written JSON.

Recommended process:

1. Serialize validated JSON.
2. Write to a temporary file in the same directory.
3. Flush and close it.
4. Replace the existing manifest atomically.
5. Return success only after replacement completes.

Optionally create one temporary safety backup during the write operation, but do not create a custom manifest-versioning system.

Do not generate files such as:

```text
asset_manifest_v1.json
asset_manifest_v2.json
asset_manifest_2026_07_23.json
```

Git provides history.

---

## 38. JSON Formatting

Write deterministic, human-readable JSON.

Recommended:

```text
UTF-8
2-space indentation
trailing newline
stable field order
```

Preferred field order:

### Plate

```text
category
gang_count
file
is_active
```

### Hardware

```text
category
hardware_type
gang_count
file
is_active
```

### Slot module

```text
category
gang_count
module_type
slot_position
file
is_active
```

Sort manifest entries deterministically.

Recommended order:

1. plates by gang count;
2. hardware by gang count;
3. slot modules by gang count;
4. slot modules by slot position;
5. slot modules by module type sort order;
6. custom or unknown entries afterward.

Do not reorder entries randomly on every save.

---

## 39. Discard Changes

Provide:

```text
Discard Changes
```

This resets the working copy to the last successfully loaded or saved manifest.

Show confirmation when unsaved changes exist:

```text
Discard all unsaved manifest changes?
```

Discarding changes must not modify the JSON file.

---

## 40. Navigation With Unsaved Changes

If the user attempts to:

- switch to another tab;
- refresh the browser;
- close the page;
- navigate away;

while unsaved changes exist, warn them where supported.

At minimum, use a browser unload warning.

If the current tab system supports route blocking, integrate with it.

Do not silently lose unsaved edits.

---

## 41. Backend API

Use REST endpoints consistent with the existing project.

Suggested routes:

```text
GET /api/wall-plates/asset-manifest
PUT /api/wall-plates/asset-manifest
```

Optional validation and file-check routes:

```text
POST /api/wall-plates/asset-manifest/validate
GET /api/wall-plates/asset-file-status
```

Avoid creating one API endpoint per manifest entry because saving is intentionally batch-based.

### GET response

```json
{
  "assets": {
    "plate.1gang": {
      "category": "plate",
      "gang_count": 1,
      "file": "/assets/wall_plates/1gang_plate.glb",
      "is_active": true
    }
  }
}
```

### PUT request

Send the complete manifest:

```json
{
  "assets": {
  }
}
```

### PUT response

Return:

```json
{
  "manifest": {
    "assets": {
    }
  },
  "warnings": [],
  "saved": true
}
```

Follow existing API response conventions if they differ.

---

## 42. Backend Path Safety

The backend must write only to the configured manifest path:

```text
/config/wall_plates/asset_manifest.json
```

Do not accept arbitrary filesystem destinations from the frontend.

The frontend must not send a server file path.

The endpoint is specifically scoped to the wall-plate manifest.

GLB paths stored inside the manifest are public URL paths, not arbitrary local filesystem paths.

Reject dangerous or malformed values containing patterns such as:

```text
../
..\ 
file://
absolute operating-system paths
```

Do not allow the editor to become a general filesystem editor.

---

## 43. Manifest Models

Create typed frontend and backend models.

Suggested TypeScript:

```typescript
type AssetCategory = "plate" | "hardware" | "slot_module";

type GangCount = 1 | 2 | 3 | 4;

interface AssetManifest {
  assets: Record<string, AssetManifestEntry>;
}

interface AssetManifestEntryBase {
  category: AssetCategory;
  gang_count: GangCount;
  file: string;
  is_active: boolean;
}

interface PlateManifestEntry extends AssetManifestEntryBase {
  category: "plate";
}

interface HardwareManifestEntry extends AssetManifestEntryBase {
  category: "hardware";
  hardware_type: "plate_screws";
}

interface SlotModuleManifestEntry extends AssetManifestEntryBase {
  category: "slot_module";
  module_type: string;
  slot_position: number;
}

type AssetManifestEntry =
  | PlateManifestEntry
  | HardwareManifestEntry
  | SlotModuleManifestEntry;
```

The `module_type` value must be validated against database records.

Suggested frontend editing model:

```typescript
interface EditableManifestEntry {
  manifestKey: string;
  originalManifestKey?: string;
  value: AssetManifestEntry;
  editState: "unchanged" | "added" | "modified" | "deleted";
}
```

Use the project's existing naming conventions if different.

---

## 44. Backend Validation

The backend must validate the full manifest before writing it.

### Root validation

```text
root must be an object
assets must exist
assets must be an object
```

### Key validation

```text
manifest key is not empty
manifest key is unique
manifest key contains no unsupported control characters
```

### Common entry validation

```text
category is recognized
gang_count is 1, 2, 3, or 4
file is non-empty
file is a bare name (no "/" or "\" folder separators)  # folder lives in properties.glb_folder
file ends with .glb
is_active is boolean
```

### Plate validation

```text
category = plate
hardware_type must not exist
module_type must not exist
slot_position must not exist
```

### Hardware validation

```text
category = hardware
hardware_type = plate_screws
module_type must not exist
slot_position must not exist
```

### Slot-module validation

```text
category = slot_module
module_type is required
module_type exists in module_types table
slot_position is required
slot_position is an integer
slot_position >= 1
slot_position <= gang_count
hardware_type must not exist
```

### Resolver uniqueness

Block duplicate active resolver identities.

---

## 45. Errors Versus Warnings

Separate blocking errors from non-blocking warnings.

### Blocking errors

Examples:

```text
Manifest key is empty.
Gang count must be between 1 and 4.
Slot 3 is invalid for a 2-gang asset.
Module type "toggle" does not exist in the database.
Two active entries resolve to 2-gang slot 1 Switch.
File must be a bare name (no folders); the folder is set once in properties.glb_folder.
```

### Non-blocking warnings

Examples:

```text
GLB file is not currently available.
Manifest key does not follow the recommended naming convention.
Filename does not match the generated naming convention.
An inactive entry duplicates another resolver identity.
Module type is inactive.
The GLB contains no semantic material names.
```

Display errors and warnings separately.

Do not block manifest creation merely because future GLB files are not present.

---

## 46. Manifest Migration

This task must migrate the current manifest data.

### Old manifest location

```text
/config/asset_manifest.json
```

### New manifest location

```text
/config/wall_plates/asset_manifest.json
```

### Old GLB URLs

```text
/assets/glb/
```

### New GLB URLs

```text
/assets/wall_plates/
```

### Remove

```text
schema_version
coordinate_space
```

### Add

```text
gang_count
is_active
```

### Preserve

```text
manifest keys
category
module_type
slot_position
file basename
```

Example migrated manifest:

```json
{
  "properties": {
    "glb_folder": "/assets/wall_plates/"
  },
  "parts": {
    "plate.1gang": {
      "category": "plate",
      "gang_count": 1,
      "file": "1gang_plate.glb",
      "is_active": true
    },
    "hardware.1gang.plate_screws": {
      "category": "hardware",
      "hardware_type": "plate_screws",
      "gang_count": 1,
      "file": "1gang_plate_screws.glb",
      "is_active": true
    },
    "module.1gang.slot1.dimmer": {
      "category": "slot_module",
      "gang_count": 1,
      "module_type": "dimmer",
      "slot_position": 1,
      "file": "1gang_slot1_dimmer.glb",
      "is_active": true
    },
    "module.1gang.slot1.switch": {
      "category": "slot_module",
      "gang_count": 1,
      "module_type": "switch",
      "slot_position": 1,
      "file": "1gang_slot1_switch.glb",
      "is_active": true
    }
  }
}
```

Do not create placeholder files for GLBs that do not exist.

---

## 47. Assembly Integration

Update the Assembly tab to read from the new manifest location and schema.

The Assembly resolver must support:

### Plate lookup

```text
category = plate
gang_count = selected gang count
is_active = true
```

### Plate-screw lookup

```text
category = hardware
hardware_type = plate_screws
gang_count = selected gang count
is_active = true
```

### Slot-module lookup

```text
category = slot_module
gang_count = selected gang count
slot_position = selected slot
module_type = selected module code
is_active = true
```

The Assembly tab must no longer depend on:

```text
coordinate_space
old manifest path
/assets/glb/
```

After the Geometry tab saves the manifest, Assembly should use the updated data.

It is acceptable to reload the manifest when:

- the Assembly tab becomes active;
- the manifest save completes;
- the user explicitly refreshes assets.

Avoid requiring a full application restart.

---

## 48. Suggested Frontend Components

Recommended component structure:

```text
GeometryTab
AssetManifestToolbar
AssetManifestFilters
AssetManifestTable
AssetManifestRow
ManifestEntryEditor
ManifestEntryForm
BulkManifestGeneratorDialog
GeometryPreviewViewport
GeometryPreviewToolbar
SemanticMaterialInspector
MeshPropertiesPanel
ManifestValidationPanel
UnsavedChangesIndicator
```

Avoid implementing the entire tool as one oversized component.

---

## 49. Suggested Frontend Services and Hooks

Recommended:

```text
assetManifestApi
assetManifestValidation
assetManifestNormalization
assetManifestGenerator
assetManifestSelectors
geometryPreviewService
useAssetManifestEditor
useGeometryPreview
useModuleTypes
```

### `assetManifestApi`

Responsibilities:

```text
load manifest
save complete manifest
handle backend errors
```

### `assetManifestValidation`

Responsibilities:

```text
validate entry shape
validate complete manifest
detect resolver conflicts
separate errors and warnings
```

### `assetManifestGenerator`

Responsibilities:

```text
generate keys
generate file paths
generate missing production entries
preserve existing records
```

### `useAssetManifestEditor`

Responsibilities:

```text
baseline manifest
working manifest
selected entry
add
edit
duplicate
delete
undo delete
discard
dirty tracking
save
```

---

## 50. UI Behavior for Invalid Existing Data

The editor must be able to load and display a manifest containing an invalid or outdated entry.

Do not make the entire Geometry tab unusable because one entry is malformed.

Preferred behavior:

- load all parseable entries;
- mark invalid rows clearly;
- show their raw values where possible;
- allow the user to correct them;
- block saving until structural errors are resolved.

If the JSON itself cannot be parsed, show:

```text
The asset manifest contains invalid JSON.
```

Include backend-provided diagnostic information where safe.

Do not overwrite an unreadable manifest automatically.

---

## 51. Concurrency Protection

Even though the application currently has one admin user, avoid silently overwriting a manifest changed externally after it was loaded.

Recommended lightweight approach:

- backend returns a content hash or last-modified token with GET;
- frontend returns that token with PUT;
- backend rejects the save if the file changed since loading.

Example response:

```json
{
  "manifest": {
    "assets": {}
  },
  "revision": "sha256-content-hash"
}
```

Example save request:

```json
{
  "manifest": {
    "assets": {}
  },
  "expected_revision": "sha256-content-hash"
}
```

Conflict response:

```text
The manifest changed on disk after it was loaded. Reload it before saving.
```

This is not manifest versioning. It is protection against accidental overwrite.

Implement this if it fits cleanly with the existing backend.

---

## 52. Loading and Error Handling

The Geometry tab must handle:

```text
manifest loading
module-type loading
preview loading
manifest saving
```

separately.

One failure should not unnecessarily hide unrelated functionality.

Examples:

- If module types fail to load, existing entries can still be displayed, but slot-module editing should show an error.
- If preview loading fails, manifest editing should still work.
- If manifest saving fails, preserve all unsaved frontend changes.
- If the manifest cannot load, disable editing and provide a retry action.

---

## 53. Accessibility

Use accessible controls.

Requirements:

- all table actions keyboard accessible;
- form controls have labels;
- validation messages connect to relevant fields;
- selected rows are distinguishable without color alone;
- toggles expose their state;
- confirmation dialogs trap focus correctly;
- viewport is not the only way to inspect semantic materials.

The semantic material list must remain available as text.

---

## 54. Responsive Behavior

The application is primarily an admin desktop tool, but the Geometry tab should degrade reasonably on narrower windows.

Suggested behavior:

- table may scroll horizontally;
- editor and preview may stack vertically;
- toolbar actions may wrap;
- long file paths may use ellipsis with full value available in editor or tooltip.

Do not compromise desktop usability to optimize for small mobile screens.

---

## 55. Tests — Manifest Parsing and Migration

Add tests for:

```text
old manifest can be migrated
schema_version is removed
coordinate_space is removed
old /assets/glb/ paths become /assets/wall_plates/
gang_count is derived correctly for old entries
is_active defaults to true
hardware_type plate_screws is added where appropriate
manifest keys are preserved
```

---

## 56. Tests — Validation

Add tests for:

```text
valid plate entry
valid hardware entry
valid slot-module entry
invalid category
invalid gang count
invalid slot number
slot greater than gang count
missing module type
unknown module type
inactive module type warning
missing file path
path outside /assets/wall_plates/
non-GLB extension
duplicate manifest key
duplicate active plate resolver
duplicate active hardware resolver
duplicate active slot-module resolver
inactive duplicate warning
```

---

## 57. Tests — Editing Workflow

Add tests for:

```text
load manifest
select entry
edit entry
add entry
duplicate entry
mark entry deleted
undo deletion
toggle active state
multiple edits remain unsaved
discard restores baseline
save sends complete manifest
successful save clears dirty state
failed save preserves dirty state
navigation warning appears with unsaved changes
```

---

## 58. Tests — Bulk Generation

Add tests for:

```text
generates four plate entries
generates four plate-screw entries
generates correct slots for each gang count
uses module types loaded from database
generates 40 slot-module entries for four current module types
generates 48 total entries from an empty manifest
does not overwrite existing entries
does not reset existing file paths
does not reset is_active
generates unpadded slot filenames
uses module type code in filename
uses /assets/wall_plates/ prefix
```

---

## 59. Tests — Backend Saving

Add tests for:

```text
GET reads the new manifest location
PUT validates the complete manifest
PUT rejects malformed data
PUT rejects resolver conflicts
PUT writes formatted JSON
PUT writes atomically
PUT does not modify GLB files
PUT does not accept arbitrary output paths
PUT returns normalized manifest
revision conflict prevents overwrite
```

---

## 60. Tests — Geometry Preview

Add tests where practical for:

```text
selected entry loads its GLB
changing selection unloads previous GLB
missing file shows warning
parse failure shows error
semantic material names are collected
multi-material meshes report all names
preview failure does not break editor
inactive assets can still be previewed
```

Use lightweight unit tests for hierarchy traversal and semantic material extraction where full WebGL testing is impractical.

---

## 61. Manual Acceptance Scenarios

### Scenario A — Load Existing Manifest

1. Open the application.
2. Confirm tab order:

```text
Assembly | Geometry | Materials | Assignments
```

3. Open Geometry.
4. Confirm the four migrated entries appear.
5. Confirm paths use:

```text
/assets/wall_plates/
```

6. Confirm `coordinate_space` is absent.
7. Confirm entries are active.

Expected result:

```text
Existing entries are editable and valid.
```

### Scenario B — Add a 2-Gang Plate

Create:

```text
Key: plate.2gang
Type: Plate
Gang: 2
File: /assets/wall_plates/2gang_plate.glb
Active: Yes
```

Expected result:

```text
Entry appears as an unsaved addition.
No disk write occurs until Save Manifest.
```

### Scenario C — Add a Slot Module

Create:

```text
Key: module.3gang.slot2.outlet
Type: Slot Module
Gang: 3
Slot: 2
Module Type: Outlet
File: /assets/wall_plates/3gang_slot2_outlet.glb
```

Expected result:

```text
Outlet is selected from the database-backed dropdown.
```

### Scenario D — Invalid Slot

Set:

```text
Gang: 2
Slot: 3
```

Expected result:

```text
Blocking validation error.
Manifest cannot be saved.
```

### Scenario E — Missing Future GLB

Create a valid entry whose file does not exist yet.

Expected result:

```text
Entry is structurally valid.
Missing GLB warning is shown.
Preview reports file not found.
Manifest may still be saved after warning confirmation.
```

### Scenario F — Duplicate Resolver Identity

Create two active entries for:

```text
2-gang
slot 1
switch
```

Expected result:

```text
Resolver conflict is shown.
Save is blocked.
```

### Scenario G — Disable Duplicate

Disable one conflicting entry.

Expected result:

```text
Blocking conflict is resolved.
Inactive duplicate may remain as a warning.
```

### Scenario H — Bulk Generation

Run:

```text
Generate Wall-Plate Entries
```

with all gangs and current module types.

Expected result:

```text
All missing plate, screw, and slot-module entries are created.
Existing entries are preserved.
Generated entries remain unsaved until Save Manifest.
```

### Scenario I — Preview Semantic Materials

Select an existing GLB.

Expected result:

```text
GLB loads in isolated viewport.
Mesh names and semantic material names are listed.
```

### Scenario J — Delete Manifest Entry

Delete an entry and save.

Expected result:

```text
Entry is removed from JSON.
Its GLB file remains untouched.
```

### Scenario K — Assembly Integration

Save a new valid manifest entry and open Assembly.

Expected result:

```text
Assembly resolves geometry using the updated manifest without an application restart.
```

---

## 62. Non-Goals

Do not implement:

```text
GLB upload
GLB replacement
GLB deletion
GLB renaming
GLB movement
GLB geometry editing
GLB transform editing
GLB material editing
database-backed asset manifest
universal cross-product asset schema
product-family creation UI
user accounts
authentication
role management
public/admin permission enforcement
manifest history UI
manifest version files
Git commits from the application
cloud object storage
CDN publishing
automatic GLB generation
automatic movement of existing GLB files
per-object semantic material editing
```

The user will manage GLB files using another application.

---

## 63. Acceptance Criteria

The task is complete when:

1. The tab order is:

```text
Assembly | Geometry | Materials | Assignments
```

2. Geometry loads:

```text
/config/wall_plates/asset_manifest.json
```

3. Assembly uses the same new manifest location.
4. GLB paths use:

```text
/assets/wall_plates/
```

5. No GLB subfolders are required.
6. Existing manifest entries are migrated.
7. `schema_version` is removed.
8. `coordinate_space` is removed.
9. Every entry has an explicit `gang_count`.
10. Every entry has an explicit `is_active`.
11. The user can add manifest entries.
12. The user can edit manifest entries.
13. The user can duplicate manifest entries.
14. The user can remove manifest entries.
15. Deleting an entry never deletes its GLB.
16. The user can enable and disable entries.
17. Slot-module types are loaded from the database.
18. Module types are selected from a dropdown.
19. Arbitrary module type strings cannot be entered.
20. The user can generate missing entries for all gangs and slots.
21. Bulk generation preserves existing entries.
22. Multiple changes remain unsaved until Save Manifest.
23. Save Manifest validates the entire manifest.
24. The backend validates independently.
25. The JSON write is atomic.
26. The JSON is formatted deterministically.
27. The user can discard unsaved changes.
28. Navigation warns about unsaved changes.
29. Resolver duplicate conflicts are detected.
30. Missing GLB files produce warnings rather than crashes.
31. Selecting an entry previews its GLB where available.
32. Semantic material names are displayed as text.
33. Preview failure does not prevent manifest editing.
34. Inactive entries are ignored by Assembly.
35. Geometry can still preview inactive entries.
36. The Geometry tool does not manipulate GLB files.
37. Assembly can consume a newly saved manifest without restarting the application.
38. Tests cover migration, editing, generation, validation, saving, and resolution.

---

## 64. Guiding Principles

```text
The JSON manifest remains the source of truth.

The Geometry tab edits manifest records, not GLB files.

All wall-plate GLBs live directly in /public/assets/wall_plates/.

The public GLB URL root is /assets/wall_plates/.

Manifest entries describe how an assembly requirement resolves to a GLB path.

Structured fields are authoritative; filenames and keys are conventions.

Module types come from the database.

Every module type may occupy every valid slot.

One active manifest entry must resolve each assembly requirement.

Missing future geometry is allowed and must be clearly reported.

Multiple edits are saved as one complete manifest update.

The backend must validate and write the JSON safely.

The current tool is wall-plate-specific without prematurely defining every future Latoun product.

The application is currently admin-only, but Geometry should later be easy to hide from public users.
```
