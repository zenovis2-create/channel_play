# Test Plan

| ID | Surface | Pass condition |
| --- | --- | --- |
| V9-T-001 | Frozen inputs | V5-V8 source, package, FBX, and V8 baseline hashes match. |
| V9-T-002 | Ownership | Exactly one V9 root and exact visual/collision child groups exist. |
| V9-T-003 | Renderer whitelist | Only exact Valley Gate, Covered Causeway, and duplicated route renderers are disabled. |
| V9-T-004 | Inherited floor | Exactly two forward V5 floor colliders remain enabled and align to V9 floor bounds. |
| V9-T-005 | Structural pairing | Every V9 structural visual has one BoxCollider proxy with matching bounds. |
| V9-T-006 | Decorative safety | Inlays and relief accents have no collider or trigger. |
| V9-T-007 | Clearance | Capsule samples pass the complete spawn-to-hub corridor at 1.8m by 2.2m. |
| V9-T-008 | Static budget | Renderer, mesh, collider, light, camera, rigidbody, and map budgets pass. |
| V9-T-009 | Idempotence | Two rebuilds preserve root signature, mesh GUIDs, topology, and hashes. |
| V9-T-010 | Pair mutation | Offsetting one collision proxy is rejected, then restored without saving. |
| V9-T-011 | Graybox mutation | Re-enabling one superseded renderer is rejected, then restored without saving. |
| V9-T-012 | Regression | V5 Gate 4, inherited PlayMode traversal, V7 entry, and V8 root signatures pass. |
| V9-T-013 | Windows player | Participant traverses Valley Gate -> causeway -> V8 hub in the built player. |
| V9-T-014 | Visual mutation | Deliberate proxy/graybox mutation is visibly distinct and rejected. |
| V9-T-015 | Performance | D3D11 player profile passes inherited timing/memory and V9 geometry limits. |
| V9-T-016 | Scene scope | Canonical baseline comparison allows only V9 documents and exact renderer disables. |
| V9-T-017 | Aggregate | Docs, bindings, receipts, local Fable decision, and staged whitelist pass. |
| V9-T-018 | Error metric control | A 0.75m independent waypoint perturbation reports nonzero error and trips the 0.4m threshold. |
| V9-T-019 | Inverse collision | Causeway envelope contains 0 orphaned solid colliders and no superseded renderer-owned collision. |
| V9-T-020 | Capture integrity | Every PNG fully decodes, passes CRC/pixel checks, and runtime proof captures are freshly created. |
| V9-T-021 | Player payload | All files returned by `BuildReport.GetFiles()` are hashed in the receipt and each binding. |
| V9-T-022 | Index equivalence | Every required staged artifact exists in the index and equals its validated worktree file. |

Direct traversal and direct image inspection are mandatory manual-quality gates.
