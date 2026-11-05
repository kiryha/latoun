# Latoun CAD

This folder contains the SOLIDWORKS models for Latoun wall plates. They translate the Houdini design drafts into editable parts and assembled products for visual review and factory quotations.

## Start here

1. [Product and file structure](docs/model_structure.md) — how parts form a product, which files to open, and how CAD relates to the configurator.
2. [Design assumptions](docs/assumptions.md) — why the model is divided this way, what was simplified, and what still needs engineering.

Open `output/solidworks/1gang_switch.SLDASM` or `output/solidworks/1gang_dimmer.SLDASM` to review a product. The models have been saved, reopened and checked in SOLIDWORKS. They are ready for design discussion; the mechanisms and manufacturing interfaces still need development.

## Folder structure

```text
cad/
  README.md       Start here
  docs/           Product structure and design decisions
  inputs/         Supplied design references
  output/
    solidworks/   Editable parts and assemblies
    step/         Geometry for factory exchange
  scripts/        Tools that build, check and export the models
  AGENTS.md       Instructions and technical notes for agents
```

References and generated CAD files are kept locally and excluded from Git. A repository clone provides the documentation and scripts; obtain the references and models separately.

Generated output contains the current native models, matching STEP files and JSON check results. Versioning is managed manually; the automation saves its work and closes its documents and SOLIDWORKS session when possible.
