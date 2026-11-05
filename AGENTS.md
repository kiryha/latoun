# Latoun repository

- Repository root: `D:/projects/latoun`. Keep the existing application folders and documentation in place.
- CAD work belongs in `cad/`. Follow `cad/AGENTS.md` for all CAD tasks and read its current model-structure and assumptions documents before construction.
- The SOLIDWORKS/CAD project is operated separately on the work VDI where the SOLIDWORKS license is available. Its agents own `cad/` and must not modify files outside `cad/`. Agents working on the configurator, product model, or repository documentation must not modify anything inside `cad/`.
- CAD references and generated files live in `cad/inputs/` and `cad/output/`; both are local and ignored by Git. Preserve all input and existing design files.
- Use GitHub Desktop with this repository root. Do not create a nested checkout or synchronize CAD files through a second workspace.
- The user manages commits and pushes manually in GitHub Desktop. Do not commit or push unless explicitly requested.
