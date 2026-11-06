# Latoun CAD project

- Work only inside `cad/`. The application manifest and root project docs may be read for context, but must not be edited by CAD agents.
- Never create Git commits or push. The user manages Git and versioning manually.
- Preserve all input, backup and existing design files. Do not overwrite designs without confirmation; use the fresh output area provided by the user. Do not create automatic revision folders or ZIP packages.
- Before CAD construction, read `docs/model_structure.md`, `docs/assumptions.md` and `docs/skills/latoun-solidworks/SKILL.md`.
- Current geometry comes from `inputs/004/`. Preserve its remaining overlaps and unfinished mechanism interfaces. Do not invent dimensions, fits, materials or tolerances.
- Match the asset manifest with four multibody SLDPRT files and two product SLDASM files. Keep physical components as separate named bodies with native features. Use a native body copy for the second fixing head; do not create extra external component files.
- Use lowercase Latoun names without revision suffixes. The four current asset groups are `1gang_plate`, `1gang_plate_screws`, `1gang_slot1_switch` and `1gang_slot1_dimmer`.
- Native files belong in `output/solidworks`, STEP in `output/step`, STL in `output/stl`, and every generated JSON validation report in `output/validation`. References and all output remain local and ignored by Git. Do not modify `output/.backup/`.
- Save completed native work, close documents opened by automation after use, and exit SOLIDWORKS when possible. Preserve unrelated pre-existing user work. Report any unsaved recovery document or session left open.
- Do not claim success until actual files have been saved, reopened and validated. STEP checks must include imported solids; a successful save can still produce an empty file.

## Documentation

- Keep one current document per topic. Explain product structure and why decisions were made, from high level to detail. Use Git for history.
- Keep implementation procedures in the CAD skill and numerical check results in JSON. Do not duplicate dimension registers or create file-size inventories.
- The prompt in `docs/input_handoff_prompt.md` defines the preferred future input handoff. Current scripts do not automatically ingest arbitrary `design.json` files; the modeling agent must map the data to the existing construction functions.
