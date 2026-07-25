# Khufu V11 Royal Chamber Circuit Test Plan

## Static Gates

| Gate | Evidence |
| --- | --- |
| Contract parse | JSON classification and performance budget parse; all spec IDs are classified. |
| Baseline binding | Exact V10 limestone/red-granite source paths and Great Step blocker name resolve. |
| Open-boundary transition | V11 variants are bound, source assets are unchanged, and the blocker is disabled. |
| Root ownership | Identity transform, exact child buckets, tags, and no forbidden components. |
| Structural pairs | Every structural/collider spec has matching transform and bounds. |
| Geometry identity | Entry, antechamber, chamber, sarcophagus, shaft recesses, and five display levels exist. |
| Clearance | Sampled route capsule reaches the King's Chamber without V11/V10 blockers. |
| Enclosure | Player-view samples retain walls/ceiling around the route and chamber. |
| Performance | Root and map metrics satisfy `performance-budget.json`. |
| Idempotence | Second rebuild preserves scene and generated-asset signatures. |

## Negative Controls

1. Rebind one transitioned V10 renderer to its original closed mesh; validation must reject it.
2. Offset one structural proxy; pair validation must reject it.
3. Enable the Great Step blocker; route validation must reject it.
4. Add an external map collider on the route; clearance validation must reject it.
5. Remove one stacked display level; semantic validation must reject it.

## Required Captures

1. `great_step_open_axis.png`
2. `antechamber_portcullis_detail.png`
3. `kings_chamber_wide.png`
4. `sarcophagus_and_shaft_boundary.png`
5. `relieving_stack_cutaway.png`
6. `pyramid_royal_circuit_integration.png`

Each capture must be fresh, nonblank, hashed, and manually checked for clipping, opaque legacy
walls, floating boxes, leaks through the pyramid shell, text overlays, and incoherent overlap.

## Release Gate

Release requires all static gates, five negative controls, post-capture idempotence, clean-index
Unity import, focused Python tests, six captures, manual QA, V4/V5/V8/V9/V10 regression evidence,
an actual Windows CharacterController round trip, a blocker-enabled player control, strict staged
inventory validation, and a reviewer verdict.
