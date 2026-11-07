# Design assumptions

## Purpose and source of truth

The models support appearance review and early factory quotations. We preserve the design's unresolved details so the factory can assess the intended appearance before mechanism selection drives further changes.

The current reference set is `inputs/005/`. Its drawings and source construction parameters in `design.json` govern the reconstruction. Dimensions belong in those references and model parameters; check results belong in the existing JSON reports in the chosen output version's `validation/` folder.

## Why solids remain separate

The plate, silicone ring and fixing heads are shared between products to keep their appearance consistent. They are grouped into the same plate and hardware assets as the configurator. Each manifest asset is one multibody part file. Switch and dimmer components remain separate named solids within their module, so their geometry can evolve independently. Grouping does not merge their solids or decide how the factory must manufacture them.

The dimmer collar remains separate from the grip because their connection is unresolved. Keeping them separate exposes the overlap for engineering review. The raised L belongs to the cap because it is a surface detail, with no specified separate attachment.

## Reconstruction choices

- The open source stem is reconstructed as a closed solid with the supplied outer dimensions and pivot bore. This closes missing end faces; it does not define a mechanism interface.
- The dimmer flutes follow the supplied sampled section with smooth spline bevels and a native 46-degree twisted sweep. They no longer use the previous cosine approximation.
- The logo outline is simplified within 0.01 mm and extruded into the cap to form a valid solid. Its small inset and edge bevel are omitted. The source contains ununited/open logo geometry.
- Native rounded edge treatments approximate Houdini polygon bevels. Fine screw recess bevels and control edge details are simplified; these remain appearance models, not exact copies of every source polygon. The largest sampled difference in the current comparison is about 0.22 mm at the dimmer base edge. The comparison samples source vertices and does not establish a full-surface error bound.

## Decisions still needed

The switch uses the source neutral pose (0 degrees), with its provisional pivot at Z=-10 mm. The assemblies hold a review pose; they do not demonstrate working travel.

The stem overlaps the grip, and the dimmer neck overlaps the base and grip. The base slightly overlaps its insert. Screw heads retain the source 0.28183 mm separation above the plate. The plate opening and insert have zero nominal clearance. These source overlaps are retained because choosing a joint would require inventing a fastening or retention method.

Shaft openings, fits, retention, internal mechanisms and the electrical enclosure remain undefined. The decorative heads have no shanks or threads, and their recess has no assigned standard drive type. Materials, finishes and manufacturing tolerances also remain open.

## What to discuss with the factory

Start with mechanism selection and how each control is retained. Those decisions determine the internal geometry and which components should actually be manufactured separately.

Then review the cost and finish of the helical flutes, raised logo and small recess corners. Ask whether the proposed shapes require special tooling or extra setups, and whether coatings affect the visible gaps and fits. Any resulting appearance changes should be agreed before changing the model.
