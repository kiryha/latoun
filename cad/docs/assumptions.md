# Latoun 002: dimensions, decisions and unresolved design details

**Historical 002 report.** Current construction uses [assumptions_004.md](assumptions_004.md) and the explicit revised 004 dimensions.

Inspection date: 2026-11-04. Units: mm unless degrees are stated.

## Classification

- **Explicit:** printed on the sheets, stated in the README, or recorded in measurement JSON. These are source-model measurements, not manufacturing tolerances.
- **Derived:** calculated from explicit values or eventually fitted to supplied numeric sections. Derived fits must include residuals and must not be relabeled as specified radii.
- **Estimated:** guessed or visually approximated geometry. No estimated critical dimensions have been adopted.
- **Unknown:** absent or not sufficiently defined to construct/validate the functional design.
- **User decision:** plate maximum envelope shall be 70 x 120; all other dimensions retained. The source envelope 69.8444768 x 119.8518052 is superseded only for the outer plate size.

## Explicit dimension register

| Geometry | Explicit value | Source / qualification |
|---|---|---|
| Plate | Source maximum 69.844 x 119.852; thickness 3 | Sheets 03/04, JSON; outer size superseded by user decision |
| Datum | Rear plate center (0,0,0), front Z=3 | README |
| Rear ring | 66 x 116 x 2; Z=-2..0 | Sheet 03; opening at Z=-1 is 62.18 x 112.18; straight wall 1.91 |
| Fixing holes | 2 x diameter 3 through; X=0, Y=+/-41.5 | Sheet 03; center separation 83 |
| Insert taper | At Z=.15, 1.5, 2.85: W/H=37.8/70.8, 36/69, 34.2/67.2 | Sheet 04; plate opening and inserts coincide at these stations |
| Insert maximum | 37.8598012 x 70.8597972 x 3 | JSON; max bounds do not describe any one end-face section |
| Switch bezel | Maximum 21.998877 x 49.998876; Z=3..7 | Sheet 05 and JSON |
| Switch slot | Working width 4.10; insert lengths 19.368, 20.972, 22.576 at Z=.001, 1.5, 2.999 | Sheet 05; ends slope with depth; mouth blends alter near-face dimensions |
| Bezel slot | At Z=5: 4.10 x 24.718; near Z=6.999: 4.289 x 27.046 | Sheet 05 |
| Switch stem | Local X/T/S envelope 4 x 10 x 23.4; S=-2..21.4 | Sheet 06 |
| Pivot | Diameter 1 through along X; center (0,0,-10); 2 from stem rear | Sheet 06; no pin/support included |
| Switch pose | 25 degrees toward -Y from +Z | Sheet 06; not a rated travel range |
| Grip | Local envelope 10 x 10 x 20; S=19.916..39.916 | Sheet 06; rounded square section and curved ends |
| Dimmer base | Max diameter envelope 23.6772672; height 4; Z=2.98164296..6.98164292 | Sheet 07 and JSON; fit axial profile to section |
| Collar | Diameter 14; height 5; Z=6.12025103..11.1202514 | Sheet 07 and JSON |
| Fluted grip | Height 20; Z=7.60046486..27.6004672 | Sheet 07 and JSON |
| Helical flutes | 40; 9-degree spacing; crest/root diameter 15.937 / 15.221 | Sheet 08; working-band geometry, not end blends |
| Twist | +2.300 degrees/mm with increasing Z, CCW in front view | Sheet 08; crest phase .500 + 9n degrees at Z=17.60047 |
| Front cap | Max diameter envelope 14.89203796; height .8; Z=27.60127..28.4012686 | Sheet 07 and JSON |
| Raised L | X=-2.93006259..3.69929592, Y=+/-3.58000048; height .3000014; Z=28.3751767..28.6751781 | Sheet 07/JSON; detailed outline in section DXFs |
| Fixing heads | Two identical hex heads; envelope 7.973454 x 6.9282055 x 3; Z=3.28183034..6.2818299 | Sheet 09/JSON; not a standard screw designation |
| Head recess | Mouth 4.168 x 4.168; floor span 4; floor arm width .8; floor Z=5.4; depth .882 | Sheet 09; shaped cross, no standard drive specified |

## Derived values and construction implications

- Symmetric outer-envelope changes: +0.0777616 mm per X side and +0.0740974 mm per Y side. These implement the user's nominal plate decision; no scaling of holes/opening/modules.
- Main insert taper per side: (37.8-34.2)/(2*(2.85-.15)) = 2/3 mm per mm of Z, about 33.690 degrees from the plate normal. Both in-plane dimensions have the same taper in the central band. End blends are excluded.
- Outer plate central-band slopes differ: X side = (69.755-65.345)/(2*2.7) = .816667; Y side = (119.772-115.668)/(2*2.7) = .76 mm/mm, using rounded sheet values. Do not impose one uniform draft angle. Fit exact sections during modeling.
- Stem lateral gap in a centered 4.10 slot: (4.10-4.00)/2 = .05 mm per side, before finish/tolerance or motion.
- At the shown pose, source section data reports stem/slot overlap .496 near insert rear and .153 at bezel mid-depth. This is not a full 3D interference or travel test.
- Stem/grip axial overlap = 21.4-19.916 = 1.484. No physical joint follows from this overlap.
- Helix lead = 360/2.3 = 156.521739 mm/revolution; total twist over 20 mm = 46 degrees; flute depth = (15.937-15.221)/2 = .358 mm. This is decorative fluting, not a screw thread.
- Head air gap = 3.28183034-3 = .28183034. Source head placement cannot clamp the plate without additional geometry.
- Base extends .01835704 mm into the insert's axial interval. Collar/base and collar/grip intervals overlap. These bounding-interval observations require solid checks before calling them actual interference volumes.
- Cap/grip axial separation = 27.60127-27.6004672 = .0008028 mm. The L extends .0260919 mm into the cap's axial interval. Do not interpret export-level microgaps as specified fits.
- Source toggle envelope Z=-13.925708..27.113050 (41.038758 overall); projection beyond plate face 24.113050. Dimmer source Z=-2..28.675178 (30.675178 overall); projection 25.675178. These omit the absent mechanisms.

## Unknowns and decisions still needed

1. **Functional scope:** the references are sufficient for a documented exterior reconstruction, but not for a functional electrical assembly. Decide whether to preserve known defects in the first reference model or approve specific corrections separately.
2. **Insert interface:** material, finish thickness, clearance/fit, assembly direction and retention. Current taper has zero modeled clearance. No clearance has been invented.
3. **Toggle mechanism:** selected switch mechanism, true travel/limits, pin size/fit/support, lever-to-mechanism connection and grip/stem retention. Existing 25-degree pose interferes with the slot; no slot extension or pivot relocation is authorized yet.
4. **Dimmer interface:** selected mechanism, shaft diameter/shape/length, through passage, axial stack, bore, torque transmission and retention. The source contains no shaft passage.
5. **Fixings:** shank/thread, seating, actual drive type and whether the .282 mm gap is intentional. No screw standard inferred.
6. **Manufacturing split:** integral versus attached rear ring, separate versus integral bezel/insert, cap attachment and materials/finishes. Proposed CAD files are provisional engineering boundaries, not a released BOM.
7. **Profile definition:** exact analytic corner/blend radii, switch-grip end surfaces, flute root form and end transitions, recess draft/radii. Numeric sections permit fitting, but do not specify original design primitives. No fit has been approved or measured yet.
8. **Acceptance:** allowable deviation from the mesh-derived sections; dimensional/geometric tolerances, finish, materials and inspection criteria. Extra decimal places in JSON do not establish machining precision.

No estimated values are currently authorized. Unspecified mechanism internals should remain absent, not represented by plausible-looking fabricated dimensions.

## DFM recommendations for later review (no design changes applied)

- Resolve taper fit after finish allowances; the current zero-clearance interface can bind or fail to seat. Check retention and assembly sequence.
- Evaluate the switch's .05 mm nominal side clearance against coating, variation, misalignment and full motion. Resolve the documented end overlap before any functional claim.
- Match internal slot/recess/flute radii to available tooling after measuring the required profile. Small cross-recess corners and .8 mm arms may require small tools, broaching or other process choices; do not assume standard Phillips tooling.
- Helical flutes may require synchronized rotary milling or suitable tooling. Preserve appearance; confirm tool access, end transitions and finishing/deburring with the supplier before choosing a process.
- The 1 mm pivot hole requires a defined pin/bearing arrangement, fit and durability assessment. Diameter alone does not establish adequacy.
- Assess thin ring/plate fixturing and finish distortion; consider machining sequence and setups for both front and rear details.
- A raised L can be machined by removing surrounding cap material, but small interior details and surface finish affect tool choice and time. A separate applied mark is an alternative only with design approval.
- No recommendation here changes the design or certifies electrical safety, load capacity, life, or production readiness.
