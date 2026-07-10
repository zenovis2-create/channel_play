# Khufu V5 Test Plan and Traceability Matrix

Updated: 2026-07-10

Tests prove only their named surface. Passing one surface never substitutes for another. All final
implementation evidence must come from the same accepted commit unless a test explicitly records
an approved exception.

## Test Matrix

| Test ID | Requirements | Surface | Pass condition | Required evidence |
| --- | --- | --- | --- | --- |
| KV5-T-001 | KV5-R-010, KV5-R-014 | Harness validator | Required docs and links exist; IDs are unique; every requirement is covered; every `[x]` joins to accepted non-empty evidence; required Fable output has an accepted token. | Validator receipt with `HARNESS_VERDICT: passed`. |
| KV5-T-002 | KV5-R-001, KV5-R-011 | Truth-tag static audit plus human visual audit | Every archaeology-derived district/object has one class; forbidden traversal claims are absent; truth boundary is visible in required captures. | Static receipt plus annotated screenshot review. |
| KV5-T-003 | KV5-R-002, KV5-R-013 | V4 contract validator and focused diff | V4 dimensions, dense mass, seven corbels, five relieving chambers, and root contract remain unchanged or have an accepted superseding decision. | V4 validator receipt, focused diff, hierarchy snapshot. |
| KV5-T-004 | KV5-R-003, KV5-R-004 | V5 hierarchy/graph validator | At least eight district roots, six major loops, and three shortcuts exist within accepted bounds; graph is connected. | Machine-readable graph and validation receipt. |
| KV5-T-005 | KV5-R-004, KV5-R-006 | Route metric validator | All-key route is 700-900 m; hub-to-key times and dead-end/shortcut thresholds pass at recorded controller speeds. | Segment table, route receipt, controller-speed revision. |
| KV5-T-006 | KV5-R-005 | PlayMode objective flow | Keys collect in any order; terminal recognizes three; shop remains usable; Valley Gate rejects early use and opens after completion. | PlayMode receipt plus event log. |
| KV5-T-007 | KV5-R-006, KV5-R-007 | Scripted and manual traversal | Required routes are reachable; no stuck/collision failure; one-way recovery and eight-proxy hub circulation thresholds pass. | Trajectory, collisions, stuck metrics, manual review. |
| KV5-T-008 | KV5-R-007 | Human social-deduction rehearsal | Each key route exposes one public interaction and one private-risk segment without unavoidable isolation; observations are recorded by two reviewers or one reviewer plus replay evidence. | Review form, replay/captures, issue list. |
| KV5-T-009 | KV5-R-008 | Operator PlayMode and screenshots | Operator camera reaches all macro districts, shows objective states, and frames the full route without clipping or UI overlap. | Operator traversal receipt and required screenshots. |
| KV5-T-010 | KV5-R-010 | Unity batch compile/EditMode checks | Unity exits 0; compile errors and unexpected error logs are zero; static validators pass. | `tools/channelctl unity check` receipt and logs. |
| KV5-T-011 | KV5-R-005, KV5-R-006, KV5-R-010 | Unity PlayMode/simulation smoke | Runtime map spawns; player moves; key/terminal/shop/exit flow and scripted agent route complete; receipt verdict is pass. | Playtest, sim-check, agent-playtest receipts. |
| KV5-T-012 | KV5-R-001, KV5-R-011 | Screenshot and manual visual review | Desktop player, operator, top-down, side elevation, landmarks, dense core, UI fit, and truth boundary meet the visual checklist at named resolutions. | PNG set, capture manifest, signed review. |
| KV5-T-013 | KV5-R-009 | Windows Development Player profiling | Named target machine, scene, route, sample window, budgets, and profiler data are recorded; accepted budgets pass. | Player build receipt, profiler capture, budget decision ID. |
| KV5-T-014 | KV5-R-012, KV5-R-014 | Fable harness review | Required output is non-empty plain text, contains `FABLE_VERDICT: ship`, and contains no harness error or tool-call warning. | Fable output and wrapper call ledger. |
| KV5-T-015 | KV5-R-013 | Regression and rollback audit | Unrelated dirty changes are untouched; gate rollback is executable; focused diff contains only intended files; affected prior tests still pass. | Git status/diff summary, rollback procedure, regression receipts. |
| KV5-T-016 | KV5-R-014 | Cold-reader audit | From README alone, a fresh reviewer identifies current decision, phase, next action, blocker, and proof within five minutes with no incorrect answer. | Timestamped question/answer receipt and reviewer identity/type. |

## Gate 0 Validator Scope

The documentation validator must fail on at least these mutations:

1. A required document is missing or empty.
2. A local Markdown link is broken.
3. A requirement or test definition ID is duplicated.
4. A requirement has no test-matrix coverage.
5. A completed status item has no evidence reference.
6. Referenced evidence is missing, empty, failed, stale by declared revision, or lacks a pass token.
7. A required Fable artifact contains `FABLE_HARNESS_ERROR` or `system-warning`, has more than one
   verdict line, places the verdict before the final non-empty line, or ends in a verdict other
   than `FABLE_VERDICT: ship`.
8. A document or validator changes after the bound receipt.
9. A receipt's embedded artifact hash differs from its evidence revision.

## Visual Review Checklist

- Pyramid silhouette reads as complete from player and operator proof cameras.
- Dense masonry surrounds passages; the core never reads as a hollow atrium.
- District landmark is visible from at least two decision points.
- Scan cyan appears only on modern observation surfaces.
- Confirmed-to-fiction transition is unmistakable.
- Text and UI do not overlap at proof resolutions.
- Key, mission, shop, and exit states are legible in OBS-ready game view.
- No screenshot substitutes for traversal or collision evidence.

## Performance Baseline Template

Record before accepting a budget:

- target machine CPU, GPU, RAM, OS, display resolution, and quality settings;
- Unity revision and tested commit;
- Development Player build command and output;
- representative player route and operator route;
- warm-up duration, capture duration, and sample count;
- median and 95th-percentile frame time;
- main-thread, render-thread, GPU, managed-memory, and total-memory observations;
- accepted thresholds in a `KV5-D-NNN` decision.

## Test Failure Rules

- Same exact failure twice stops retries and creates a Fable blocker-analysis pack.
- A flaky pass remains failed until the trigger and repeatability are understood.
- Human visual disagreement creates an issue; it is not averaged into a pass.
- Test threshold changes require a decision before rerunning.
- Partial evidence produces `investigate` or `blocked`, never `passed`.
