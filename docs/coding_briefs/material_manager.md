# Latoun Material Manager v0.1 — Coding Brief

## 1. Objective

Add an internal **Material Manager** to the Latoun configurator so materials can
be maintained from the UI instead of only via the seed script.

This is an internal prototype tool, not a customer-facing feature. Its purpose
is to make the SQLite `materials` table the live, editable source of truth for
Three.js `MeshPhysicalMaterial` render parameters, and to give immediate visual
feedback through a live 3D preview.

The tool must allow the user to:

- List all existing materials and their parameters.
- Create, rename, and delete materials.
- Adjust each material's render parameters.
- Preview the material live on a shared "hero" model under the same lighting as
  the Assembly scene.

The Material Manager lives beside the existing configurator behind a top-level
tab bar:

```text
Assembly | Materials | Assignment States | Assignments
```

Read `docs/configurator.md` first. This brief extends that system and reuses its
stack, database, and architecture.

---

# 2. Scope and User Flow

The application opens on the `Assembly` tab (the existing configurator). The new
`Materials` tab presents a master–detail manager.

The user must be able to:

1. See a list of all materials (active and inactive), each with a color swatch,
   display name, and code.
2. Select a material to load it into the editor and preview.
3. Create a new material with a unique code.
4. Rename a material's `code` and/or `display_name`.
5. Edit `base_color`, `metalness`, `roughness`, `anisotropy`,
   `anisotropy_rotation`, and the `is_active` flag.
6. See the edited material update in a live 3D preview immediately.
7. Save changes (create or update) to the SQLite database.
8. Delete a material that is not referenced by any `material_assignments` row.

Switching a material in the configurator's `Assembly` tab continues to read
these parameters live from the database.

---

# 3. Technical Stack

Same stack as the configurator (see `docs/configurator.md` §4).

```text
Frontend:  React, TypeScript, Vite, Three.js, React Three Fiber, @react-three/drei
Backend:   Python 3.11+, FastAPI, Pydantic, SQLAlchemy
Database:  SQLite
Runtime:   Local Windows PC
```

No new dependencies are introduced.

---

# 4. Architecture

The `materials` table is the single source of truth for render parameters.

```text
Material data
    SQLite materials table (authoritative, edited at runtime)

Seed script
    backend/app/seed.py — reproduces the table from scratch

Material CRUD
    FastAPI /api/materials endpoints

Rendering / preview
    React Three Fiber frontend reads resolved material data via the API
```

Rules carried over from the configurator:

- The frontend must not hardcode material parameters.
- `seed.py` is a one-time/repeatable initializer, **not** read at runtime.
- The active `data/latoun.sqlite` is git-ignored and reproducible from the seed.

Consequence: editing a material in the DB (via this tool) is reflected on the
next request; re-running `seed.py` overwrites DB values with the file values.

---

# 5. Repository Additions

Files introduced or changed for the Material Manager:

```text
backend/
├── app/
│   ├── errors.py                       # added ConflictError (HTTP 409)
│   ├── schemas.py                      # MaterialAdminOut / MaterialCreate / MaterialUpdate
│   ├── routes/
│   │   └── material_routes.py          # /api/materials CRUD (new)
│   └── services/
│       └── material_service.py         # create/update/rename/delete (new)
└── tests/
    └── test_materials.py               # CRUD + rename + guard tests (new)

frontend/
├── public/
│   └── assets/
│       ├── hdri/
│       │   └── historic_cloister_passage_1k.hdr   # environment lighting
│       └── utils/
│           └── material_hero.glb                  # shared preview model
└── src/
    ├── App.tsx                         # Assembly | Materials tab bar (new shell)
    ├── materials/
    │   ├── MaterialsManager.tsx        # master-detail UI (new)
    │   └── MaterialPreview.tsx         # live 3D preview (new)
    ├── three/
    │   └── Scene.tsx                   # exports HDRI_PATH, HDRI-only lighting
    ├── api/client.ts                   # material CRUD methods
    └── types/index.ts                  # MaterialAdmin / MaterialCreate / MaterialUpdate
```

---

# 6. Data Model

Reuses the existing `materials` table (see `docs/configurator.md` §8.1). No
schema change was required.

```text
material_id
code                    stable machine identifier (renamable; assignments use material_id)
display_name
base_color              hex string "#RRGGBB"
metalness               0.0 – 1.0
roughness               0.0 – 1.0
anisotropy              0.0 – 1.0
anisotropy_rotation     0.0 – 2π (radians)
normal_texture_path     nullable (stored; not yet applied at render time)
roughness_texture_path  nullable (stored; not yet applied at render time)
is_active               materials shown/selectable in the configurator
```

Materials are created in the frontend with `THREE.MeshPhysicalMaterial`.

---

# 7. Required API Endpoints

All under the `/api/materials` prefix. Domain errors return a JSON body
`{ "error": <name>, "message": <text> }` with the mapped HTTP status.

## List Materials

```text
GET /api/materials
```

Returns all materials (active and inactive), ordered by `code`, including
`is_active`.

## Create Material

```text
POST /api/materials
```

Body: `MaterialCreate`. Returns `201` with the created material.
Duplicate `code` returns `409`.

## Update / Rename Material

```text
PATCH /api/materials/{code}
```

Body: `MaterialUpdate` (all fields optional; partial update). The URL carries the
**current** code; the body may carry a new `code` to rename.

```text
- Unknown material            -> 404
- Renaming to an existing code -> 409
```

Assignments reference materials by foreign key (`material_id`), so a code rename needs no cascade.

## Delete Material

```text
DELETE /api/materials/{code}
```

Returns the deleted material. Refused with `409` if any `material_assignments`
row still references the material (referential-integrity guard).

---

# 8. Frontend Layout

The `Materials` tab uses a three-column master–detail layout.

```text
┌──────────────────────────────────────────────────────────────┐
│ Assembly | Materials | Assignment States | Assignments       │
├───────────────┬──────────────────────────┬───────────────────┤
│ MATERIALS +New│ Code        [__________] │                   │
│  ▪ Brass      │ Display name[__________] │                   │
│  ▪ Steel      │ Base color  [#] [______] │   Live Preview    │
│  ▪ Copper     │ Metalness   [====o=====] │   (material_hero  │
│               │ Roughness   [==o=======] │    under HDRI)    │
│               │ Anisotropy  [o=========] │                   │
│               │ Aniso. rot. [===o======] │                   │
│               │ [x] Active               │                   │
│               │ [Save Changes] [Delete]  │                   │
└───────────────┴──────────────────────────┴───────────────────┘
```

Required UI elements:

```text
material list with color swatch, name, code, inactive flag
"+ New" button
code field (sanitized live)
display name field
base color: color picker + hex text input
metalness / roughness / anisotropy / anisotropy_rotation sliders with readouts
is_active checkbox
Save (Create/Save Changes) button, enabled only when valid and dirty
Delete button (existing materials only)
live 3D preview pane
error and success banners
```

Keep the UI clean; this is an internal tool, not a customer-facing design.

---

# 9. Editing Behavior

```text
Selecting a material loads an editable draft copy.
Save is enabled only when the draft is valid and differs from the stored record.
Creating uses a blank draft with sensible defaults.
Numeric parameters use sliders bound to their valid ranges.
The color uses a native color input mirrored by an editable hex field.
```

Save routing:

```text
New material    -> POST /api/materials, then reselect by created code
Existing         -> PATCH /api/materials/{originalCode} with the full draft,
                    then reselect by the (possibly renamed) code
```

---

# 10. Code Validation and Sanitization

The `code` is constrained on both ends.

Backend (authoritative):

```text
code pattern       ^[a-z0-9_-]+$        (1–64 chars)
base_color pattern ^#[0-9a-fA-F]{6}$
metalness/roughness/anisotropy   0.0 – 1.0
anisotropy_rotation              0.0 – 2π
```

Frontend (live input sanitization for `code`):

```text
lowercase all input
convert whitespace runs to a single underscore "_"
strip any character outside [a-z0-9_-]
```

Forbidden characters can never be typed into the code field; there is no
free-text hint under the field.

---

# 11. Live Preview Requirements

The preview must match the Assembly scene's look 1:1.

```text
Model:        /assets/utils/material_hero.glb (shared hero model)
Lighting:     equirectangular HDRI only — /assets/hdri/historic_cloister_passage_1k.hdr
              (no discrete lights), via <Environment files={...} />
Tone mapping: THREE.ACESFilmicToneMapping, exposure 1.0
Framing:      <Bounds fit clip observe> auto-frames regardless of model scale
Controls:     OrbitControls, zoom enabled, pan disabled
```

Rendering rules:

```text
1. Load the hero GLB via useGLTF (drei), preloaded.
2. Clone the cached scene so the shared GLB is never mutated.
3. Build one MeshPhysicalMaterial from the edited parameters.
4. Traverse the clone and assign that material to every mesh.
5. Dispose the material when the parameters change or the view unmounts.
```

The preview updates immediately as parameters change.

---

# 12. Referential Integrity

Materials are referenced by `material_assignments` rows (finish scheme + binding → material).

```text
Delete:  refused (409) if any material_assignments row references the material.
Rename:  no cascade required; assignments reference material_id, not code.
```

---

# 13. Error Handling

The tool must surface, never swallow, these cases:

```text
backend unavailable
duplicate material code on create or rename        (409)
rename/edit of a non-existent material             (404)
delete of a referenced material                    (409)
invalid color or out-of-range parameter            (422)
preview model (material_hero.glb) fails to load
```

Errors and successes are shown as inline banners in the editor pane.

---

# 14. Tests

Backend tests (`backend/tests/test_materials.py`) must cover:

```text
list includes seeded materials
create material succeeds
create with duplicate code -> 409
create with invalid color -> 422
partial update preserves untouched fields
update of missing material -> 404
rename code updates the record and the list
rename to an existing code -> 409
delete of an unreferenced material succeeds
delete of a material referenced by material_assignments -> 409
```

Verify manually:

```text
list renders with swatches and codes
selecting a material loads editor + preview
sliders and color update the preview live
create / rename / delete round-trip through the DB
renamed material still resolves correctly in Assignments-tab previews
```

---

# 15. Non-Goals

Not in this iteration:

```text
applying normal_texture_path / roughness_texture_path at render time
texture upload or asset management
per-mesh / semantic material bindings
material categories, tags, or search
undo / redo and change history
bulk edit or import/export of materials
soft-delete / archive workflow beyond the is_active flag
authentication or per-user permissions
```

Texture fields are stored but not yet consumed by `three/materials.ts`.

---

# 16. Acceptance Criteria

The iteration is complete when:

1. A `Materials` tab sits beside `Assembly`, `Assignment States`, and `Assignments` in the app shell.
2. The material list loads from `GET /api/materials` and shows all materials.
3. A material can be created with a unique, sanitized code.
4. A material's `code` and `display_name` can be renamed.
5. Renaming does not require cascading to other tables (assignments use `material_id`).
6. All render parameters can be edited within their valid ranges.
7. The live preview applies the edited material to `material_hero.glb` under the
   shared HDRI and tone mapping, updating immediately.
8. Changes persist to SQLite and are reflected in the Assembly tab.
9. A material referenced by `material_assignments` cannot be deleted; an unreferenced one can.
10. Invalid input is rejected by the backend with a clear message.
11. No material parameters are hardcoded in React components.

The purpose is to prove that materials can be maintained live from the UI while
keeping the database authoritative and material assignments valid.
