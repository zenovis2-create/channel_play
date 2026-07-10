# Pyramid Reference-matched V4 Design Contract

Date: 2026-07-10
Scene: `Assets/_Project/Scenes/School_MVP.unity`
Generated root: `TraitorEscape_Runtime_Map/Runtime_Pyramid_Reference_Matched_V4`
Golden reference: `asset_pipeline/references/pyramid_true_form_v3/pyramid_reference_target_user_20260710.png`
Golden reference size: `1536x1024`
Golden reference SHA256: `D7D7E4E6E4B8439546AD5BA927992B636F9B545066135823ACEF97F2441BD446`

## Correction

V3 passed geometric bookkeeping but did not match the generated reference. It depicted a
sparse hollow perimeter shell, a broad rectangular front opening, and freestanding ramps.
Those properties made the implementation structurally and visually different from the
reference. V4 supersedes V3 as the active scene implementation.

## Archaeological Facts

- Khufu's pyramid is a dense masonry mass, not a hollow shell. Its roughly dressed core
  blocks were covered by a smooth Tura-limestone casing.
- The exterior contract remains a 56 m square base, 35.636 m height, and 51.843-degree
  face slope (`7/11` height/base).
- The Descending Passage continues through core masonry into bedrock; the Subterranean
  Chamber is excavated below the base.
- The Grand Gallery rises at about 26 degrees and has seven inward-stepping corbel courses.
- The granite King's Chamber is embedded in the core with five relieving chambers and a
  gabled load-diversion structure above it.
- The King's Chamber floor level is about `82/280` of pyramid height; at V4 scale this is
  `10.43 m`. The Queen's Chamber floor level is about `41/280`, or `5.21 m` at V4 scale.

Research anchors:

- Harvard/Digital Giza 3D: https://www.3ds.com/newsroom/press-releases/dassault-systemes-recreates-giza-necropolis-its-3dexperience-platform
- AERA archaeological survey: https://aeraweb.org/projects/gpmp/
- JAEA casing study: https://web.ujaen.es/investiga/egiptologia/journalarchitecture/downloads/JAEA1_Lightbody.pdf
- Harvard Grand Gallery paper: https://gizamedia.rc.fas.harvard.edu/documents/miatello_pjaee_7-6_2010.pdf
- Egyptian Ministry monument record: https://egymonuments.gov.eg/en/monuments/the-great-pyramid/

## Cutaway Convention

The cutaway is a visualization device, not a literal historical opening. It must retain
enough casing to reconstruct the complete pyramid mentally while filling every sliced
surface with dark stone poche or dense blockwork. Empty blue background may never be
visible through the pyramid mass around a passage.

## Golden-reference Composition

- Output is exactly `1536x1024`.
- Camera is a low, near-north three-quarter architectural view, not a high aerial view.
- The complete square-base/apex silhouette remains readable.
- North cutaway base width: `34 m`.
- North cutaway top width: `0.9 m` at `Y=28.7 m`.
- Top/base cutaway width ratio: `0.026` (must remain below `0.30`).
- North casing remains as left panel, right panel, and upper triangular cap.
- East casing remains a complete smooth triangular face.
- The left half of the cutaway shows dense exposed core masonry.
- The right/central half shows passages and chambers embedded against a filled cut plane.
- A `7.5 m` deep split bedrock foundation exposes the descending route and subterranean
  chamber. Its front portal is a gameplay access device, not a historical claim.

## V4 Geometry

- Dense cut-face core: at least `160` individually visible blocks across `42` staggered
  courses; the tightly packed exposed face and filled backing establish mass.
- Section poche: one continuous dark unlit tapered plane behind all internal architecture.
- Entrance: north face above base and east/west offset kept modest.
- Descending passage: enclosed stone conduit that crosses below `Y=0`.
- Ascending passage: enclosed conduit that joins the Grand Gallery foot.
- Queen's Chamber: compact gabled chamber on the horizontal branch.
- Grand Gallery: stair/ramp floor, exactly seven corbel bands per side, and a narrow
  central trench; it must not read as one oversized freestanding ramp.
- King's Chamber: compact red-granite room with antechamber/portcullis.
- Relieving system: exactly five short chambers directly over the King's Chamber, bounded
  laterally so they do not read as floating shelves.
- Cyan route lighting remains thin and subordinate to stone architecture.

## Visual Acceptance Tests

1. Render and golden reference share the same resolution and low three-quarter framing.
2. The cutaway is visibly tapered; top/base width ratio is <= `0.30`.
3. Smooth casing occupies both sides of the cutaway and one complete side face.
4. At least `160` exposed core blocks are visible; no sparse perimeter bars are accepted.
5. A continuous dark cut plane surrounds the internal voids, preventing a hollow-shell read.
6. The foundation is split and the below-grade route/chamber are visible in the hero view.
7. Internal architecture occupies less than half the opening width at each level and reads
   as carved/embedded, not as a bridge floating in an empty atrium.
8. Seven Grand Gallery corbels per side and five bounded relieving chambers are visible.
9. The hero render is inspected next to the golden reference before completion is allowed.
10. Numeric validation, visual comparison, compilation, and Play Mode must all pass.

## Honest Limits

The generated reference exaggerates the amount of masonry removed and simplifies the
true plan for readability. V4 matches that cutaway language without claiming the exposed
opening, cyan route lighting, or lower gameplay portal existed historically. The final
Unity result is a validated structural blockout, not a photorealistic art match.
