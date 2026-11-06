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
    stl/          Manifest group meshes for Houdini
    validation/   Internal JSON check results
  scripts/        Tools that build, check and export the models
  AGENTS.md       Instructions and technical notes for agents
```

References and generated CAD files are kept locally and excluded from Git. A repository clone provides the documentation and scripts; obtain the references and models separately.

Generated output contains the current native models, matching STEP files, manifest group meshes for Houdini and separate JSON check results. Versioning is managed manually; the automation saves its work and closes its documents and SOLIDWORKS session when possible.

## Working with agents

For the agent preparing Houdini references, use [the input handoff prompt](docs/input_handoff_prompt.md). It requests drawings for review and structured geometry data for modeling.

For the CAD agent, use [the SOLIDWORKS skill](docs/skills/latoun-solidworks/SKILL.md). In a new chat, ask it to read that file and `cad/AGENTS.md`, then give it the input folder and the specific change. The skill is stored in this repository; it does not require a separate plugin installation.
