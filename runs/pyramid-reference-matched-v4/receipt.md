# Pyramid Reference-matched V4 Final Receipt

Date: 2026-07-10
Status: `validated-structural-blockout`

## Result

V4 supersedes the V3 completion claim. It matches the golden reference's structural
reading order while keeping historical facts separate from cutaway/gameplay adaptations.

## Completed

- Active root: `Runtime_Pyramid_Reference_Matched_V4` in `School_MVP`.
- Exterior: `56.000 m` square base, `35.636 m` height, `51.843 deg` face slope.
- Tapered north cutaway: `34.0 m` base, `0.9 m` top at `Y=28.7 m`, ratio `0.026`.
- Dense exposed core: `217` blocks across `42` courses.
- Continuous dark section poche behind the internal architecture.
- Queen's Chamber floor scaled from about `41/280` of pyramid height (`5.21 m`).
- King's Chamber floor scaled from about `82/280` of pyramid height (`10.43 m`).
- Grand Gallery with seven corbels per side, central trench, landing, and antechamber.
- Exactly five bounded relieving chambers and a gabled load-diversion roof.
- `7.5 m` deep split bedrock, subterranean chamber, and visible lower cutaway.
- Exact-size golden-comparison renders at `1536x1024`.

## Automated Validation

- Status: `passed`.
- Casing panels/faces: `8`.
- Route markers: `8`.
- Corbel bands: `14`.
- Relieving chambers: `5`.
- Foundation sections: `3`.
- Queen's floor actual/target: `5.200 / 5.218 m`.
- King's floor actual/target: `10.500 / 10.436 m`.
- Interior envelope violations: `0`.
- Detailed receipt: `runs/pyramid-reference-matched-v4/validation-receipt.md`.

## Image Evidence

- Golden reference SHA256: `D7D7E4E6E4B8439546AD5BA927992B636F9B545066135823ACEF97F2441BD446`.
- Hero SHA256: `B1889987AD6001B9B01CD427905C747A3ACDF4ECE716A97641C822962AF3458B`.
- Front SHA256: `DDF2DF93A04FD52CFE5042369FF47AD7137CFDD1F2E23E7693B87173582D4975`.
- X-ray SHA256: `5F204FD9170134857A4F0FEE1500C58C052C5AC0F9A35AC07C833340570E456A`.
- All checked images are `1536x1024`, nonblank, and have broad sampled luminance ranges.
- Screenshot receipt: `runs/pyramid-reference-matched-v4/screenshot-receipt.md`.

## Runtime Verification

- Unity scripts compiled with zero compiler errors.
- An 8-second Play Mode run produced zero scene/gameplay errors.
- Play Mode exited cleanly.
- Active scene: `Assets/_Project/Scenes/School_MVP.unity`, saved and not dirty.
- Remaining unrelated warning: Unity AI Assistant account API accessibility timeout.

## Historical Versus Adapted

- Historical: dense limestone mass and casing, one bedrock chamber and two masonry
  chambers, descending/ascending passages, corbelled Grand Gallery, King's Chamber,
  five relieving chambers, and upper gable.
- Adapted: open cutaway, cyan route overlay, enlarged traversable clearances, and lower
  gameplay access portal.

## Not Completed

- Photorealistic material, erosion, bespoke block, desert, and lighting art matching.
- Manual input-driven traversal through every branch.
- Production navigation bake and final collision polish.

The hero render is structurally comparable to the generated concept, but it is deliberately
reported as a Unity blockout rather than a pixel-identical or production-art match.
