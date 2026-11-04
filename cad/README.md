# Latoun SOLIDWORKS CAD

## Local workspace

The repository root is `D:\projects\latoun`; add that directory to GitHub
Desktop. Edit CAD documents and scripts directly under `D:\projects\latoun\cad`.
The earlier `.integration-inspection` checkout has been consolidated into this
layout. Review changes, commit to `main`, then use **Push origin** in Desktop.
Local inputs, outputs and the CAD Python environment are retained under `cad/`
and ignored by Git. Existing reports keep their historical absolute paths;
new script runs resolve paths relative to the current `cad/` directory.

Revision 004 contains native part and assembly automation, geometry validation,
AP214 STEP export and review-package tooling. The current construction report
records 12 parts, two assemblies and 14 STEP exports saved and reopened, plus
a passing native-feature smoke test. These are appearance and quotation models,
not a manufacturing release. Validation evidence and geometry remain local in
the ignored `output/` directory; this repository does not include those artifacts.

## Layout

```text
cad/
  AGENTS.md                     CAD working rules
  docs/                         Current 004 findings and historical 002 records
  scripts/verify_solidworks.py   Isolated COM native-feature smoke test
  scripts/build_parts.py         Native revision 004 parts
  scripts/build_assembly.py      Two static design-review assemblies
  scripts/sw_helpers.py          Shared SOLIDWORKS COM helpers
  scripts/profiles_004.py        Local nominal-DXF profile reader
  scripts/validate_and_export.py Geometry checks and AP214 STEP export
  scripts/package_review.py      Package local validated deliverables
  requirements.txt              Windows COM dependency
  inputs/004/                   Current local references (ignored)
  output/verification/          Local test records and test parts (ignored)
  output/solidworks/            Future native product files (ignored)
  output/step/                  Future STEP exports (ignored)
```

`inputs/` and `output/` are excluded from Git in their entirety. Obtain the
reference package separately and retain it unchanged under `inputs/004/`.
Cloning this repository does not provide references or historical run records.
Keep potentially proprietary drawings, measurements and CAD geometry local.
There is no automatic connection to the configurator's GLB asset workflow.

## Current findings

- [Revision 004 model structure](docs/model_structure_004.md): native features,
  assembly organization, reported validation and handoff.
- [Revision 004 assumptions](docs/assumptions_004.md): explicit definitions,
  cosmetic approximations and deliberately unresolved interfaces.
- [Revision 004 inventory](docs/reference_inventory_004.md): local reference files.
- [Automation status](docs/automation_status.md): passing smoke-test update and
  retained troubleshooting history.

The controlling plate envelope is **70 x 120 mm**, preserving other dimensions
without globally scaling reference geometry. Revision 004 explicitly revises
the insert reveal, switch slot and decorative-head seating. Remaining reference
stack overlaps and absent mechanism interfaces are retained. Read the current
model structure and assumptions before construction.

## Historical Phase 1 findings

- [Model structure](docs/model_structure.md): source interpretation, two proposed
  product assemblies sharing components, and a provisional manufacturing split.
- [Assumptions and dimensions](docs/assumptions.md): explicit measurements,
  derived values, user decisions and unknowns.
- [Reference inventory](docs/reference_inventory.md): files and archive contents.

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

Before another run, read [automation status](docs/automation_status.md), including
the passing-test update and the earlier session/preference recovery notes.
Preserve any open user work. Run manually in a suitable local Windows session:

```powershell
.\.venv\Scripts\python.exe scripts\verify_solidworks.py
```

The script creates an isolated 20 mm diameter by 5 mm cylinder and attempts
rebuild, body/feature/dimension checks, save and reopen. Each run writes to a new
timestamped `output/verification/` directory. A recorded intended output path
does not prove a saved part exists. A failed or interrupted run is not a pass.
Do not use `--inspect-session` against an unrelated active design; that diagnostic
operates on the active document. CAD automation has not been rerun as part of
this repository integration; the reported validation comes from the other
agent's construction records.

Reference-generation scripts under local `inputs/002/work/` require missing
original OBJ files and an external `inspect_geometry` module as well as NumPy
and Pillow. They are archival reference tooling, not SOLIDWORKS build scripts.
