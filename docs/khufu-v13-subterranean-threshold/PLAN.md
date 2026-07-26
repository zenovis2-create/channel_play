# Khufu V13 Subterranean Threshold Plan

## Player Flow

`V10 branch -> junction transition -> descending bedrock passage -> subterranean landing ->
horizontal approach -> chamber doorway -> chamber center -> same-route return`.

The transition begins at `(-2.5, 3.8, -19.2)`, not the obsolete V4 branch at
`(-2.5, 1.2, -18.3)`. The main descent targets `(0, -3.8, -5.6)` at approximately 29 degrees,
below the current controller's 45-degree slope limit. The level approach ends near
`(0, -3.8, -1.6)`.

## Geometry

- Build three enclosed passage shells with 2.50 m clear width and 2.40 m clear height.
- Center the chamber near `(0, -3.8, 1.5)` so it stays inside the inherited bedrock slot between
  `x=-3` and `x=3`.
- Bound the chamber at approximately `5.0 x 6.2 x 3.4` m with floor, ceiling, north wall,
  east/west walls, two south doorway jambs, and a lintel.
- Use five combined renderer buckets: `Bedrock_Structure`, `Passage_Detail`,
  `Subterranean_Shadow`, `Evidence_Limit_Accent`, and `Subterranean_Route_Inlay`.

## Ownership

Disable components only on the exact 13 records in `segment-classification.json`. Twelve targets
have one renderer/collider pair; `V4_Subterranean_Unfinished_Pit` is renderer-only. Preserve every
target GameObject active and preserve all local transforms. Do not restore or claim
`V4_Glow_Descending`, `V4_Glow_Subterranean`, `V4_Route_Subterranean_Approach`, or
`V4_Route_Subterranean_Chamber`; those disabled states belong to V10. Preserve
`V4_Light_Subterranean` enabled as an inherited dependency.

## Verification

Run the read-only Unity audit and Python prewrite gate before the first scene write. Then build
deterministically, validate exact transitions, clearance, enclosure, pit backing, idempotence,
negative controls, rollback, original V4-V12 gates, six captures, and the built-player round trip.

## Operational Rule

After V13 exists, predecessor builders run only with V13 detached and the required predecessor
bindings restored. Rebuild V13 immediately afterward; partial predecessor/V13 contexts fail closed.
