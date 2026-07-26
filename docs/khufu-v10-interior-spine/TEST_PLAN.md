# Khufu V10 Interior Spine Test Plan

| ID | Surface | Pass condition |
| --- | --- | --- |
| V10-T-001 | Research | Every numeric claim joins to a named primary/institutional source or is marked adaptation. |
| V10-T-002 | Audit | V4 markers, candidate renderers/colliders, V5 overlaps, exact transition allowlist, and empty Crown dependency intersection are recorded without scene save. |
| V10-T-003 | Compile | Original and clean-index Unity batch imports exit 0 with no compile error. |
| V10-T-004 | Root | Exactly one V10 root exists with FACT and HYBRID evidence markers. |
| V10-T-005 | Geometry | Seven corbels per side, 27 bench slots per side, two Great Step slots, plugs, branch threshold, service mouth, and bounded enclosure-ray coverage pass. |
| V10-T-006 | Pairing | Every structural visual/proxy pair passes transform and bounds tolerances. |
| V10-T-007 | Inverse collision | Every enabled solid collider in the V10 envelope is owned; orphan count is zero. |
| V10-T-008 | Clearance | The full normal route passes `1.8m x 2.2m` static samples and fixed anchors. |
| V10-T-009 | Idempotence | Two rebuilds produce identical scene and generated-mesh hashes. |
| V10-T-010 | Visual mutation | Re-enabling a superseded renderer fails exact overlap validation. |
| V10-T-011 | Collider mutation | Moving one named proxy fails pair and traversal validation. |
| V10-T-012 | Metric mutation | Independent `0.75m` observation error trips a `0.40m` threshold. |
| V10-T-013 | Legacy | V4 validation, V5 Gate 4, and V5 PlayMode pass on the integrated scene; frozen V8/V9 receipts remain passed and their current root metrics/signatures match exactly. |
| V10-T-014 | Windows traversal | Normal route reaches all anchors and returns; collider control stops at the named blocker. |
| V10-T-015 | Images | Required editor/runtime PNGs are fresh, fully decodable, nonblank, and directly inspected. |
| V10-T-016 | Performance | Pinned Windows D3D11 procedure passes `performance-budget.json`. |
| V10-T-017 | Reviews | Review-work, three-hypothesis debugging audit, external Fable, and Local Fable receipts pass. |
| V10-T-018 | Commit | Exact staged allowlist is dependency-closed and byte-bound; scoped commit and exact post-commit aggregate pass. |

The enclosure gate uses 24 fixed Grand Gallery route samples and 24 upper-hemisphere directions per
sample. At least `75%` of rays must hit V10 structure within `4.5m`, and every sample must have hits
on both lateral sides and above. Thresholds are frozen before implementation.

V8 and V9 validators freeze full-map totals from their own release surfaces (`813/441` and
`818/464`). An additive V10 scene cannot satisfy those historical totals. V10 therefore preserves
their passed receipts and recomputes the frozen V8/V9 root metrics and signatures in the integrated
scene. This is the bounded integration replacement; the historical validators are not weakened or
edited.

## Required Views

- north entrance and approach;
- ascending passage girdle/plug boundary;
- Gallery Foot and Queen branch boundary;
- Grand Gallery long axis;
- corbel, bench-slot, and groove detail;
- Great Step ownership boundary;
- HYBRID service-return distinction;
- pyramid cutaway integration;
- deliberate collider/overlap mutation;
- Windows normal and negative traversal frames.
