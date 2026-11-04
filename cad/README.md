# Latoun SOLIDWORKS CAD

Phase 1 contains reference inspection findings, a proposed modeling structure,
and an isolated native-feature verification script. Product parts, assemblies,
and STEP exports have not been constructed or validated. The unattended native
save/reopen smoke test has not passed. This work is not a manufacturing release.

## Layout

```text
cad/
  AGENTS.md                     CAD working rules
  docs/                         Phase 1 findings and decisions
  scripts/verify_solidworks.py   Isolated COM native-feature smoke test
  requirements.txt              Windows COM dependency
  inputs/002/                   Local references (ignored)
  output/verification/          Local test records and test parts (ignored)
  output/solidworks/            Future native product files (ignored)
  output/step/                  Future STEP exports (ignored)
```

`inputs/` and `output/` are excluded from Git in their entirety. Obtain the
reference package separately and retain it unchanged under `inputs/002/`.
Cloning this repository does not provide references or historical run records.
Keep potentially proprietary drawings, measurements and CAD geometry local.
There is no automatic connection to the configurator's GLB asset workflow.

## Phase 1 findings

- [Model structure](docs/model_structure.md): source interpretation, two proposed
  product assemblies sharing components, and a provisional manufacturing split.
- [Assumptions and dimensions](docs/assumptions.md): explicit measurements,
  derived values, user decisions and unknowns.
- [Reference inventory](docs/reference_inventory.md): files and archive contents.
- [Automation status](docs/automation_status.md): verified API behavior, failed
  and interrupted checks, and the remaining save/reopen validation work.

The controlling plate envelope is **70 x 120 mm**, preserving other dimensions
without globally scaling reference geometry. Known taper contact, switch-slot
interference, floating decorative heads and absent mechanism interfaces remain
unresolved. Read the model structure and assumptions before construction.

The findings documents are preserved as historical Phase 1 records dated
2026-11-04, including their original machine paths. References to
`D:/projects/latoun` describe the original standalone workspace; current CAD
paths are relative to this directory. The previously noted root
`us_mcm_nGang_plate.SLDPRT` was subsequently deleted by the user and is not
included. Local verification records were retained during integration but are
ignored by Git as requested.

## Windows setup and verification

Phase 1 used Python 3.10.8 x64, pywin32 312 and SOLIDWORKS Design Premium 2026
SP4.1. Its CAD environment is separate from the web backend environment.
From the repository root in PowerShell:

```powershell
cd cad
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The script currently expects SOLIDWORKS at
`D:\programs\SOLIDWORKS\SOLIDWORKS` via its `INSTALL` constant and uses the
configured default part template. Check that path for the current machine.
It generates Python bindings from the installed type libraries. Dimensions
are expressed in mm for engineering documentation and meters at the API boundary.

Before another run, read [automation status](docs/automation_status.md). Prior
clients stalled in COM, and forced termination may have left **Input dimension
value** disabled. Preserve any open user work before restarting SOLIDWORKS and
check that preference. Run manually in a suitable local Windows session:

```powershell
.\.venv\Scripts\python.exe scripts\verify_solidworks.py
```

The script creates an isolated 20 mm diameter by 5 mm cylinder and attempts
rebuild, body/feature/dimension checks, save and reopen. Each run writes to a new
timestamped `output/verification/` directory. A recorded intended output path
does not prove a saved part exists. A failed or interrupted run is not a pass.
Do not use `--inspect-session` against an unrelated active design; that diagnostic
operates on the active document. The script has not been rerun for repository
integration, and reliable unattended completion remains unverified.

Reference-generation scripts under local `inputs/002/work/` require missing
original OBJ files and an external `inspect_geometry` module as well as NumPy
and Pillow. They are archival reference tooling, not SOLIDWORKS build scripts.
