# Running the Latoun Configurator (v0.1)

This is the local, internal prototype configurator for a single 1-gang Latoun
wall assembly. It proves that the configuration, asset, material, database, and
rendering layers work together.

## Prerequisites

Install:

- Python 3.11 or newer
- Node.js 20 LTS or newer
- Git

Confirm from a terminal:

```bat
python --version
node --version
npm --version
git --version
```

## First run

From the repository root:

```bat
setup_local.bat
```

This verifies your tooling, creates a `.venv`, installs backend and frontend
dependencies, and initializes + seeds the SQLite database at `data/latoun.sqlite`.

Then start everything:

```bat
run_local.bat
```

The configurator opens automatically at:

- App: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

## Later runs

Only run:

```bat
run_local.bat
```

## Stopping

Close the two terminal windows that opened (backend + frontend), or press
`Ctrl+C` in each.

## What you can do

1. Select **Switch** or **Rotary Dimmer**.
2. Select **Brass** or **Steel**.
3. The 3D assembly (plate + screws + selected module) updates immediately.
4. Rotate and zoom (pan is disabled).
5. Review the resolved configuration summary and the **Prototype BOM**.
6. **Save Configuration** to the local SQLite database (generates `LAT-CFG-000001`).
7. Reload any saved configuration from the list.
8. **Export JSON** for the active (saved or draft) configuration.

The default configuration is **Rotary Dimmer + Brass**.

## Architecture at a glance

```
Product data        -> SQLite (materials, module_types, configurations)
Geometry registry   -> config/asset_manifest.json (semantic key -> GLB path)
Render materials     -> SQLite materials table (MeshPhysicalMaterial params)
Geometry files       -> frontend/public/assets/glb/*.glb
Resolved render state-> FastAPI backend (services/render_state_service.py)
Rendering            -> React Three Fiber frontend
```

The frontend contains **no hardcoded GLB paths or material parameters**. It
sends a semantic configuration (`gang_count`, `module_type`, `material`) and
receives a resolved render state (material params + asset list + BOM).

## Running the backend tests

```bat
.venv\Scripts\activate
cd backend
pytest
```

## Manual configuration (optional)

Copy `.env.example` to `.env` to override database path, asset manifest path,
CORS origins, or the frontend API base URL. All values are optional.

## Troubleshooting

- **"Backend unavailable" in the UI** — the FastAPI server is not running.
  Start it with `run_local.bat`, or manually:
  `uvicorn app.main:app --port 8000 --reload` from `backend/` with the venv active.
- **"Could not load geometry"** — a GLB file is missing from
  `frontend/public/assets/glb/`. The expected files are `1gang_plate.glb`,
  `1gang_plate_screws.glb`, `1gang_slot01_dimmer.glb`, `1gang_slot01_switch.glb`.
- **Database errors** — re-run the seed: from `backend/` with the venv active,
  `python -m app.seed`. The database is fully reproducible from the seed script.
```
