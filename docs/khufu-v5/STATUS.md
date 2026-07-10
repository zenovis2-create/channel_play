# Khufu V5 Live Status and Evidence

Updated: 2026-07-10
Current gate: `KV5-G-000 Harness Ready`
Gate verdict: harness accepted; commit freeze pending
Unity implementation: not started
Baseline commit: `2d6dbebdc5c572c8d59572134026165c7dfee8ba`

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with accepted evidence
- `[!]` blocked with reason and evidence where available

No phase-level bulk completion is allowed. Each `[x]` line requires its own `evidence: KV5-E-NNN`.

## Current Decision

Use Fable's accepted six-document model plus a content-aware validator. Do not begin Unity
implementation until the scoped freeze set is committed and `--require-committed` passes.

## Gate Board

- [~] `KV5-G-000` Harness Ready
- [ ] `KV5-G-001` Coordinate Lock
- [ ] `KV5-G-002` Authored Graybox
- [ ] `KV5-G-003` Gameplay Integration
- [ ] `KV5-G-004` Traversal and Social Play
- [ ] `KV5-G-005` Art and Truth Language
- [ ] `KV5-G-006` Performance and Regression
- [ ] `KV5-G-007` Final Acceptance

## Gate 0 Work Items

- [x] Create and cross-link the six harness documents; evidence: KV5-E-004
- [x] Implement content-aware harness validation; evidence: KV5-E-003
- [x] Run validator unit and integration tests; evidence: KV5-E-003
- [x] Generate revision-bound Gate 0 pre-review receipt; evidence: KV5-E-004
- [x] Complete cold-reader audit; evidence: KV5-E-006
- [x] Complete Fable final review and apply blocking findings; evidence: KV5-E-007
- [x] Generate final working-tree validation receipt; evidence: KV5-E-008
- [ ] Obtain user authorization for the scoped harness commit.
- [ ] Commit the freeze set and pass `--require-committed`.
- [ ] Freeze Gate 0 and begin Coordinate Lock.

## Blockers

- Gate 0 cannot freeze until the scoped harness files, accepted Fable output, and final receipt are
  committed. No commit was created because this request did not authorize one.

## Next Action

After user authorization, commit only the Gate 0 freeze set and run the validator with
`--require-committed`. Coordinate Lock remains closed until that command passes.

## Evidence Ledger

Ledger rows are append-only. Corrections add a new row and mark the old row superseded in Notes.

| Evidence ID | Requirements / tests | Revision | Command or procedure | Verdict | Artifact | Timestamp | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KV5-E-001 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable plan-critique wrapper, first call | failed | ../../work/fable-harness/khufu-v5-plan-critique.fable.md | 2026-07-10 | Invalid tool-call warning; never acceptable for a gate. |
| KV5-E-002 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable plan-critique wrapper, tightened retry | revise | ../../work/fable-harness/khufu-v5-plan-critique.retry.fable.md | 2026-07-10 | Valid critique; required six docs and a content-aware validator. |
| KV5-E-003 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | `python -m unittest tools.tests.test_validate_khufu_v5_harness -v` | passed | ../../runs/khufu-v5-harness-20260710-gate0/unit-tests.txt | 2026-07-10 | Nine tests cover the valid harness and fail-closed mutations at the pre-review snapshot. |
| KV5-E-004 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | `python tools/validate_khufu_v5_harness.py --root . --receipt runs/khufu-v5-harness-20260710-gate0/pre-fable-receipt.md` | passed | ../../runs/khufu-v5-harness-20260710-gate0/pre-fable-receipt.md | 2026-07-10 | Historical pre-review receipt; embedded hash matches this evidence revision. |
| KV5-E-005 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable final review, first pass | revise | ../../work/fable-harness/khufu-v5-final-review.fable.md | 2026-07-10 | Found token parsing, fail-closed test, and durable-freeze gaps. |
| KV5-E-006 | KV5-R-014 / KV5-T-016 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | Cold-reader section of Fable final review | passed | ../../work/fable-harness/khufu-v5-final-review.fable.md | 2026-07-10 | Contains `COLD_READER: passed` and correct five-field answers at the reviewed snapshot. |
| KV5-E-007 | KV5-R-012, KV5-R-014 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | Fable final-review retry after blocking fixes | accepted | ../../work/fable-harness/khufu-v5-final-review.ship.fable.md | 2026-07-10 | Final non-empty line is exactly `FABLE_VERDICT: ship`; reviewed the 7f7620 snapshot. |
| KV5-E-008 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:26e66cbbdfcfb86750bb7e3554bc39d8006daa3b88ae11c466667f5d3d9edaf3 | `python tools/validate_khufu_v5_harness.py --root . --receipt runs/khufu-v5-harness-20260710-gate0/final-working-tree-receipt.md` | passed | ../../runs/khufu-v5-harness-20260710-gate0/final-working-tree-receipt.md | 2026-07-10 | current-snapshot working-tree acceptance only; not a committed Gate 0 freeze. |

## Unresolved

- Final performance thresholds are intentionally unresolved until `KV5-G-001` records the target
  machine and `KV5-G-006` captures a Windows player baseline.
- Real multiplayer remains outside the current goal.

## Unverified

- No V5 Unity hierarchy, route, objective, screenshot, player build, or performance capture exists.
- Gate 0 freeze has not passed `--require-committed`; the harness itself has passed working-tree
  validation and Fable review.
