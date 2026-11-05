# Design assumptions

## Purpose and source of truth

The models support appearance review and early factory quotations. We preserve the design's unresolved details so the factory can assess the intended appearance before mechanism selection drives further changes.

The current reference set is `inputs/004/`. Its drawings and nominal dimension register govern the reconstruction. Dimensions belong in those references and model parameters; check results belong in the existing JSON reports under `output/`.

## Why the components are separate

The plate, rear ring and fixing heads are shared between products to keep their appearance consistent. Switch and dimmer components are separate so their mechanisms can evolve independently.

The dimmer collar remains separate from the grip because their connection is unresolved. Keeping them separate exposes the overlap for engineering review. The raised L belongs to the cap because it is a surface detail, with no specified separate attachment.

## Simplifications that affect the design

- The lever stem and grip use simple rounded shapes fitted to the supplied profiles. This keeps them practical to edit while closely matching the draft.
- The dimmer flutes use a smooth approximation of the supplied profile. They are modeled because their appearance matters to both review and quotations.
- The raised L has a simplified outline and omits its tiny edge bevel. Its graphic appearance is retained; the final edge treatment needs a manufacturing decision.

## Decisions still needed

The switch pivot and displayed lever angle are provisional. The assemblies hold a review pose; they do not demonstrate working travel.

The stem overlaps the grip, and the dimmer collar overlaps the base and grip. These source overlaps are retained because choosing a joint would require inventing a fastening or retention method.

Shaft openings, fits, retention, internal mechanisms and the electrical enclosure remain undefined. The decorative heads have no shanks or threads, and their recess has no assigned standard drive type. Materials, finishes and manufacturing tolerances also remain open.

## What to discuss with the factory

Start with mechanism selection and how each control is retained. Those decisions determine the internal geometry and which components should actually be manufactured separately.

Then review the cost and finish of the helical flutes, raised logo and small recess corners. Ask whether the proposed shapes require special tooling or extra setups, and whether coatings affect the visible gaps and fits. Any resulting appearance changes should be agreed before changing the model.
