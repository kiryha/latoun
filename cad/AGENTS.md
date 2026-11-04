# Latoun CAD project

- CAD workspace: this `cad/` directory. Paths below are relative to it; current references are in `inputs/004` (existing plural directory). Revision 004 supersedes 002 dimensions and geometry.
- Keep CAD work under `cad/`. Keep `inputs/` and `output/` local and ignored by Git; never stage them or copy their contents elsewhere for publication.
- Historical Phase 1 documents retain the original workspace paths and observations. The root `us_mcm_nGang_plate.SLDPRT` was subsequently deleted by the user; do not restore it or treat it as validated output.
- Preserve every input file and existing design file. Do not overwrite designs without confirmation.
- Read `docs/model_structure_004.md` and `docs/assumptions_004.md` before product construction; the corresponding unsuffixed reports are historical 002 records.
- User decision on 2026-11-04: main plate maximum envelope is 70 x 120 mm; preserve other dimensions. Do not globally scale the reference geometry.
- Explicit source measurements, derived fits, estimates and unknowns must remain distinguishable. Never invent functional interfaces or tolerances.
- Use editable native SOLIDWORKS features, mm in parameters and meters at the API boundary. Prefer Python/pywin32 and a few small functions.
- Verify signatures against installed 2026 type libraries or official API documentation. Check return codes, rebuilds, body validity, saved files and reopen results before reporting success.
- Use two product assemblies with shared components; the proposed manufacturing split remains provisional.
- Revision 002 had taper contact, switch-slot interference and floating heads; these are superseded by the explicit 004 changes. Remaining 004 defects include overlapping reference stacks and absent mechanism interfaces. Do not silently repair them.
- Product outputs belong in `output/solidworks` and `output/step`; automation tests belong separately in `output/verification`.
- User authorized construction through Phase 5 on 2026-11-04. This is an early appearance/quotation model: preserve remaining 004 defects and missing interfaces; do not require manufacturing data before proceeding. Use the explicit nominal 004 geometry, including its revised reveal, slot and seated heads.
