# Latoun CAD project

- CAD workspace: this `cad/` directory. Paths below are relative to it; references are in `inputs/002` (existing plural directory).
- Keep CAD work under `cad/`. Keep `inputs/` and `output/` local and ignored by Git; never stage them or copy their contents elsewhere for publication.
- Historical Phase 1 documents retain the original workspace paths and observations. The root `us_mcm_nGang_plate.SLDPRT` was subsequently deleted by the user; do not restore it or treat it as validated output.
- Preserve every input file and existing design file. Do not overwrite designs without confirmation.
- Read `docs/model_structure.md` and `docs/assumptions.md` before product construction.
- User decision on 2026-11-04: main plate maximum envelope is 70 x 120 mm; preserve other dimensions. Do not globally scale the reference geometry.
- Explicit source measurements, derived fits, estimates and unknowns must remain distinguishable. Never invent functional interfaces or tolerances.
- Use editable native SOLIDWORKS features, mm in parameters and meters at the API boundary. Prefer Python/pywin32 and a few small functions.
- Verify signatures against installed 2026 type libraries or official API documentation. Check return codes, rebuilds, body validity, saved files and reopen results before reporting success.
- Use two product assemblies with shared components; the proposed manufacturing split remains provisional.
- Known reference defects include taper contact without clearance, switch-slot interference, floating decorative heads and absent mechanism interfaces. Do not silently repair them.
- Product outputs belong in `output/solidworks` and `output/step`; automation tests belong separately in `output/verification`.
- Full assembly construction is outside the initial inspection task. Present findings before beginning it.
