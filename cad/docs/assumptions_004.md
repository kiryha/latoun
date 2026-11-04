# Latoun 004 — scope and approximations

The user explicitly approved preserving remaining defects and continuing the early design-review model without manufacturing-level engineering data. Revision 004 itself already revises the slot, insert reveal and head seating; the older 002 defects must not be reintroduced.

## Explicit definitions

Use `inputs/004/nominal_dimensions_004.md`, the nine drawing sheets and the analytic nominal DXFs as the controlling reference. Plate outer stations are Z=0, 0.25, 2.75 and 3. The insert rear is 38 x 74 R8 and its actual planar front is 34 x 70 R6. The slot width is 5, height is 22+Z, and corner radius is 0.5. These are proposed design dimensions, not production tolerances.

The source dimmer cosine profile is r=7.75+0.25*cos(40*t) mm. Its phase increases 2.25 degrees/mm with Z, producing 45 degrees over the 20 mm body and a 160 mm lead. Native B-splines interpolate 13 points per flute period; this is a smooth CAD approximation to the cosine, not a polygonal mesh conversion. The end profiles reduce mean radius by 0.2 over 0.2 mm.

## Derived/approximated cosmetic geometry

- Actuator grip: 10 x 10 rounded section with R1.6 corners, extruded over S=20..40 and intersected geometrically with a transverse R10 cylinder centered at S=30. This captures the source's curved ends with simple native surfaces. The R1.6 section differs from the supplied tessellated section by at most approximately 0.009 mm at sampled endpoints.
- Actuator stem: 4 x 10 rounded section with R0.5 corners, length 23 over S=-2..21. Sampled section residual against this analytic profile is approximately 0.019 mm. The diameter-1 transverse bore is retained solely as a reference.
- Raised L: supplied near-base graphic outline, simplified to 33 native sketch edges with a 0.015 mm simplification threshold, centered and normalized to the nominal 7 x 7 envelope. It is extruded 0.3 mm above the cap. The tiny sculpted bevel through its thickness is omitted. The threshold is an approximation setting, not a manufacturing tolerance.
- The final manufacturing split is provisional. Collar and grip remain separate so the reference overlap is visible. The logo is integral to the cap in CAD.

## Deliberately unresolved

- No shaft passage, shaft fit, switch mechanism, electrical enclosure or retention system has been added.
- The pivot at (0,0,-10) and shown 25-degree actuator pose remain placeholders. The supplied +/-25-degree clearance study is not certified mechanism travel.
- The stem/grip overlap and dimmer base/collar/grip overlaps are retained. Interference reporting must distinguish these intentional reference overlaps from unintended reconstruction errors.
- Decorative heads have no shanks or threads, and the cross recess is not assigned a standard drive type.
- Materials, finishes, tolerances, production tool radii, assembly fastening and regulatory compliance remain unspecified.
- Static review mates constrain the displayed poses. They should be replaced during mechanism engineering; named reference values alone do not create a motion study.

Manufacturing recommendations from the earlier report remain discussion points. No additional design changes have been applied solely to reduce manufacturing cost.

## Factory discussion points

- Quote the 40 helical flutes separately from the basic turned knob envelope. Confirm tool access, flute-root finish and whether explicit machining of this cosmetic profile is justified. The native sweep can be suppressed for comparison, but the delivered model retains the design.
- Review the 0.2 mm grip edge breaks, small recess corners and raised-L outline against the proposed cutters and finishing process. No cutter-radius substitutions have been applied.
- The tapered window and insert define a visual reveal, not a tolerance stack. Agree on fits, coating allowance and retention after the mechanism is selected.
- The plate, insert and bezel have front/rear features; discuss workholding and setup count with the factory before releasing a manufacturing split.
- No tight manufacturing tolerances were specified. The detailed CAD coordinates and numerical validation thresholds must not be interpreted as production tolerances.
