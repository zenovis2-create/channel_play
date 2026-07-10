# Khufu V5 Phased Plan and Gates

Updated: 2026-07-10

Only one gate may be in progress. A phase cannot begin until the previous gate has an accepted
status in `STATUS.md`. Every exit test must have evidence from the tested revision.

## Gate Summary

| Gate | Phase | Entry | Exit | Required tests | Fable | Rollback boundary |
| --- | --- | --- | --- | --- | --- | --- |
| KV5-G-000 | Harness Ready | Research contract exists | Six docs validate; cold-reader check passes; Fable final verdict is `ship`; scoped harness files and final receipt are committed; `--require-committed` passes | KV5-T-001, KV5-T-002, KV5-T-014, KV5-T-015, KV5-T-016 | required final review | Remove only `docs/khufu-v5`, harness validator/tests, and this task's Fable packs |
| KV5-G-001 | Coordinate Lock | KV5-G-000 accepted | District bounds, roots, coordinates, truth tags, key positions, and rollback snapshot frozen | KV5-T-002, KV5-T-003, KV5-T-004 | plan critique only if contract changes | Revert V5 coordinate/design artifacts; V4 untouched |
| KV5-G-002 | Authored Graybox | KV5-G-001 accepted | Eight districts, six loops, three shortcuts, traversable shell, and marker validation pass | KV5-T-004, KV5-T-005, KV5-T-007, KV5-T-010 | review if risk score >= 3 | Delete V5 graybox root/generated V5 assets only |
| KV5-G-003 | Gameplay Integration | KV5-G-002 accepted | Three keys, shop, mission terminal, scanner, final exit, and operator hooks pass | KV5-T-006, KV5-T-009, KV5-T-011 | required plan/diff review if shared MVP contracts change | Restore prior MVP bindings; keep accepted graybox |
| KV5-G-004 | Traversal and Social Play | KV5-G-003 accepted | Route budgets, dead ends, shortcuts, collision, eight-proxy circulation, and scripted run pass | KV5-T-005, KV5-T-007, KV5-T-008, KV5-T-011 | blocker-analysis after repeated route failure | Revert latest district-route batch only |
| KV5-G-005 | Art and Truth Language | KV5-G-004 accepted | District materials, landmarks, scan language, truth boundary, UI fit, and required captures pass | KV5-T-002, KV5-T-012 | visual critique required | Revert art/material pass; preserve gameplay graybox |
| KV5-G-006 | Performance and Regression | KV5-G-005 accepted | Windows baseline frozen; target-player budgets pass; compile/playtest/simulation regressions pass | KV5-T-010, KV5-T-011, KV5-T-013, KV5-T-015 | review if mitigation changes architecture | Revert optimization batch; preserve last passing art revision |
| KV5-G-007 | Final Acceptance | KV5-G-006 accepted | All requirements have passing evidence; manual traversal and Fable final review say ship | KV5-T-001 through KV5-T-016 | required final review | Return to last accepted gate; no partial ship |

Missing or invalid required Fable output blocks the gate automatically.

## Phase 0: Harness and Coordinate Lock

### KV5-G-000 Harness Ready

- Validate required documents, links, identifiers, joins, and evidence content.
- Run a cold-reader audit using only `README.md` and record whether current decision, next action,
  blocker, and proof are answerable within five minutes.
- Obtain Fable final review of the harness diff and validation receipt.
- Commit only the scoped harness docs, validator/tests, accepted Fable output, and final receipt
  after user authorization; then rerun with `--require-committed`.
- Freeze ID grammar and evidence schema before implementation.

### KV5-G-001 Coordinate Lock

- Create top-down graph and side elevation with district bounds.
- Assign evidence class to archaeology-derived districts and objects.
- Freeze world origin, V4 root, V5 district roots, spawn, keys, mission terminal, shop, and exit.
- Record target-machine specification and initial performance-capture procedure.

## Phase 1: Authored Graybox

### KV5-G-002 Authored Graybox

- Build independent roots for causeway, temple, boat circuit, north court, royal circuit,
  subterranean threshold, and underworld loops.
- Preserve V4 geometry and hierarchy.
- Add route/objective/shortcut markers before decoration.
- Validate district count, graph connectivity, collision clearance, and marker bounds.

## Phase 2: Gameplay Integration

### KV5-G-003 Gameplay Integration

- Bind Sun, Crown, and Earth keys without changing the three-key MVP promise.
- Move mission terminal and shop to the Temple Hub.
- Place final extraction at Valley Gate.
- Extend Location Scanner and operator bounds to V5 districts.
- Keep simulated roster claims separate from real multiplayer claims.

## Phase 3: Traversal and Social Play

### KV5-G-004 Traversal and Social Play

- Measure all critical and optional route segments.
- Run scripted route: spawn -> three keys -> mission terminal -> exit.
- Capture collision, stuck time, dead ends, and shortcut unlock behavior.
- Rehearse eight proxies in the hub and each key route's public/private-risk pair.
- Perform manual traversal for camera comfort and wayfinding.

## Phase 4: Art and Truth Language

### KV5-G-005 Art and Truth Language

- Apply distinct district materials, acoustics, landmarks, and threshold lighting.
- Restrict cyan scan language to modern observation surfaces.
- Make the confirmed-to-fiction transition unmistakable without explanatory UI clutter.
- Capture desktop player, operator, top-down, side-elevation, and truth-boundary views.

## Phase 5: Performance and Regression

### KV5-G-006 Performance and Regression

- Record Windows player baseline on the named target machine before optimization.
- Freeze budgets through an accepted decision entry.
- Profile representative player and operator routes in a Development Player.
- Run compile, PlayMode, simulation, manual-review, and screenshot regressions.
- Apply optimizations in reversible district-scoped batches.

## Phase 6: Final Acceptance

### KV5-G-007 Final Acceptance

- Validate every requirement-to-test-to-evidence join.
- Run final automated and manual acceptance surfaces on one revision.
- Build Fable final-review pack with focused diff, receipt list, risk score, and known gaps.
- Apply all evidence-supported blocking findings and rerun affected tests.
- Report complete, unresolved, and unverified items separately.

## Change Control

A change requires a new `KV5-D-NNN` before implementation when it alters:

- requirement thresholds or evidence classes;
- V4 geometry or the truth boundary;
- district count, key flow, extraction, controller speed, or route budgets;
- target platform or performance budgets;
- gate order, required tests, or required Fable phases.

Emergency fixes remain subject to the same gate and evidence rules after the immediate block is
contained. No retroactive decision may convert a failed test into a pass.
