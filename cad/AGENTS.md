# Latoun CAD project

- Never create Git commits or push anything to a remote. Leave all committing and pushing to the user.
- CAD workspace: this `cad/` directory. Paths below are relative to it; current references are in `inputs/004` (existing plural directory). Revision 004 supersedes 002 dimensions and geometry.
- Keep CAD work under `cad/`. Keep `inputs/` and `output/` local and ignored by Git; never stage them or copy their contents elsewhere for publication.
- Preserve every input file and existing design file. Do not overwrite designs without confirmation.
- Read `docs/model_structure.md` and `docs/assumptions.md` before product construction.
- User decision on 2026-11-04: main plate maximum envelope is 70 x 120 mm; preserve other dimensions. Do not globally scale the reference geometry.
- Explicit source measurements, derived fits, estimates and unknowns must remain distinguishable. Never invent functional interfaces or tolerances.
- Use editable native SOLIDWORKS features, mm in parameters and meters at the API boundary. Prefer Python/pywin32 and a few small functions.
- Verify signatures against installed 2026 type libraries or official API documentation. Check return codes, rebuilds, body validity, saved files and reopen results before reporting success.
- Use two product assemblies with shared components; the proposed manufacturing split remains provisional.
- Revision 002 had taper contact, switch-slot interference and floating heads; these are superseded by the explicit 004 changes. Remaining 004 defects include overlapping reference stacks and absent mechanism interfaces. Do not silently repair them.
- Product outputs belong directly in `output/solidworks`, `output/step` and `output/stl`. Do not create revision subfolders, verification archives, previews or review ZIPs unless requested. Keep only current models and their JSON validation reports.
- User authorized construction through Phase 5 on 2026-11-04. This is an early appearance/quotation model: preserve remaining 004 defects and missing interfaces; do not require manufacturing data before proceeding. Use the explicit nominal 004 geometry, including its revised reveal, slot and seated heads.

## Documentation rules

- Write user documentation from product context to decisions to necessary detail. Explain why; avoid narrating code or listing information obvious from files.
- Keep one current document per topic. Consolidate updates in place; use Git for history. Do not create documents for every input/output revision.
- Keep technical procedures here and numeric validation data in existing JSON reports. Do not create file-size inventories or duplicate dimension registers.
- Follow the naming convention in `docs/model_structure.md`: lowercase semantic part names, layout prefixes where needed, and `1gang_switch` / `1gang_dimmer` assemblies. No revision suffixes in filenames, component names or output folders; the owner handles versioning manually. Keep native references and STEP names consistent.

## Automation notes for agents

- Verified environment: Python 3.10 x64, pywin32 312, SOLIDWORKS 2026 SP4.1. Check the INSTALL constants and default templates before running on another machine.
- Run scripts in order only when rebuilding is required: build_parts.py, build_assembly.py, validate_and_export.py. The build requires the local 004 references. Do not rerun CAD for documentation changes.
- COM required approved desktop execution outside the restricted sandbox. Generate bindings from installed sldworks.tlb and explicitly query interfaces when automatic type lookup fails. Do not change security controls.
- Suppress the dimension-entry prompt during automated sketch creation and restore its prior value. Preserve open user documents. IBody2.Check returns 1 for a valid solid; swAddMateError_NoError is also 1. Save/open error codes use 0 for success.
- Run STEP validation in a session without pre-existing documents. Close saved native documents before importing, then close all temporary import documents, including unsaved children. Duplicate native/imported titles can leave hidden documents open and interfere with later exports. Check native solid counts before export and imported counts afterward; a successful SaveAs alone does not prove a complete STEP.
- GetBodyBox is approximate. Use directional GetExtremePoint checks for envelopes. Current validation reports live beside the native files and STEP exports. Resolve model paths from the current workspace rather than assuming report paths are portable.
- Native construction uses analytic sketches and features. Dimmer-insert section sketches remain underdefined; decorative flute and logo profiles use fixed coordinates. Do not describe every sketch as fully constrained or every detail as driven by dimensions.
- Datum: plate rear-face center, +Z toward the user. Actuator part Z is its local length axis; current placement rotates +25 degrees about X and translates Z by -10 mm. Rigid mates preserve this pose; named reference equations do not drive motion.
- Cosmetic fits: stem R0.5 (sample residual about 0.019 mm); grip R1.6 (about 0.009 mm), shaped by transverse R10 cylinder. Logo simplification threshold 0.015 mm, tiny bevel omitted. Flutes interpolate 13 points per period; sampled surface deviation was about 0.0022 mm. These are approximation/check settings, not manufacturing tolerances.
- Never overwrite existing design files without confirmation. Save completed native work and close documents opened by automation; exit SOLIDWORKS when no documents remain. Preserve unrelated pre-existing user documents. Leave unsaved failed work open only when needed for recovery, and report it. Do not leave successful runs with multiple app sessions or documents open.

- `scripts/export_houdini.py` exports each native part to binary STL for Houdini, preserving coordinates and numeric millimeters. It restores STL preferences and closes its session. Check mesh envelopes and volumes against the native reports; verify import with the installed Houdini geometry reader when available. Keep one mesh per unique part, without revision suffixes.
