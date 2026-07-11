# Test Plan

| ID | Surface | Pass condition |
| --- | --- | --- |
| V8-T-001 | Source audit | FBX hash and measured hierarchy/mesh/material metrics match the frozen audit. |
| V8-T-002 | Static budget | V8 is <=12 renderers, <=120k vertices, <=100k triangles, 0 colliders/lights/cameras. |
| V8-T-003 | Selection boundary | No Collision, GameplayMarkers, LightingAnchors, cameras, lights, pyramid cap, trap, or burial-maze donor is selected. |
| V8-T-004 | Placement | Causeway threshold, open court, hub center, and pyramid-side exit anchors align to the existing east-west route. |
| V8-T-005 | Graybox replacement | Exact V5/V6 hub renderer set is disabled; all original colliders and gameplay bindings remain present and enabled. |
| V8-T-006 | Materials | Limestone, basalt, red granite, shadow, and relief/paint buckets are present with non-null production materials. |
| V8-T-007 | Idempotence | Two rebuilds preserve mesh GUIDs, topology signatures, metrics, source hashes, and scene signatures. |
| V8-T-008 | Placement mutation | Moving the V8 root +5m Z is rejected, then restored without saving. |
| V8-T-009 | Graybox mutation | Re-enabling an owned V5 hub renderer is rejected, then restored without saving. |
| V8-T-010 | V5/V7 regression | V5 Gate 4, V5 PlayMode traversal, and V7 static gates pass unchanged. |
| V8-T-011 | Windows player | Build succeeds and normal participant/fixed-review captures show a readable causeway-to-court arrival. |
| V8-T-012 | Visual mutation | A deliberate facade/graybox mutation visibly differs and the image proof rejects it. |
| V8-T-013 | Performance | 35-second player profile passes the inherited frame/main/render/GPU and visible-renderer budgets. |
| V8-T-014 | Aggregate | Frozen inputs, all bindings, docs, Fable ship decision, and staged whitelist pass. |
| V8-T-015 | Scene scope | Canonical HEAD/staged YAML proves all existing document bodies unchanged except the V8 parent reference and exact V5=5/V6=11 renderer disables; every added document is V8-owned. |

Direct image inspection is a required human-quality gate in addition to automated image metrics.
