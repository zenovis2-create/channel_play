# Khufu V5 Decisions and Risks

Updated: 2026-07-10

Decision and risk records are append-only. A superseded record remains visible and links to its
replacement. Proposed decisions do not alter GOAL or PLAN until accepted.

## Decision Log

### KV5-D-001: Use Six Operational Documents

- Status: accepted
- Date: 2026-07-10
- Context: Codex proposed ten documents. Fable found that duplicated status, evidence, risks, and
  gates would drift and become a false-done vector.
- Decision: Use README, GOAL, PLAN, STATUS, TEST_PLAN, and DECISIONS. Merge rules into GOAL, gates
  into PLAN, evidence into STATUS, and risks into DECISIONS.
- Evidence: `KV5-E-002`.
- Consequence: Every live update has one owner document and fewer synchronization points.

### KV5-D-002: Preserve V4 as the Archaeological Core

- Status: accepted
- Date: 2026-07-10
- Context: V4 already has a dense-core and known-interior contract; the new map needs greater scale.
- Decision: Keep V4 as the central spine and build V5 surface and fictional bedrock districts
  around it. Do not fill the pyramid body with a room grid.
- Evidence: `docs/research/KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md`.
- Consequence: V5 requires integration tests that prove V4 did not regress.

### KV5-D-003: Enforce Archaeological Evidence Classes

- Status: accepted
- Date: 2026-07-10
- Context: The concept art and older V2 mix confirmed structures, unknown voids, and unrelated
  Egyptian monuments.
- Decision: Use FACT, UNKNOWN, HYPOTHESIS, FICTION, HYBRID, or N/A on archaeology-derived work.
- Evidence: `docs/research/KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md`.
- Consequence: SP-BV and SP-NFC remain observation surfaces; Djoser/Hawara content is excluded from
  Khufu V5 claims.

### KV5-D-004: Bind Bootstrap Evidence to an Artifact Fingerprint

- Status: accepted
- Date: 2026-07-10
- Context: The worktree contains unrelated changes and the harness files are not yet committed.
- Decision: Gate 0 may bind evidence to baseline HEAD plus a SHA-256 fingerprint of all harness
  files. Gates after Gate 0 require a commit containing the tested implementation.
- Evidence: Fable critique `KV5-E-002`; validator receipt pending.
- Consequence: Gate 0 can be honestly verified without staging or committing unrelated work.

### KV5-D-005: Delay Performance Thresholds Until Player Baseline

- Status: accepted
- Date: 2026-07-10
- Context: No named Windows target-machine baseline exists for V5.
- Decision: Freeze the procedure now, but freeze numerical frame-time and memory budgets only after
  a Windows Development Player baseline at Gate 1.
- Evidence: Official Unity profiling guidance and `KV5-R-009`.
- Consequence: Editor profiling may guide work but cannot close the performance gate.

## Risk Register

| Risk ID | Risk and trigger | Likelihood | Impact | Owner | Mitigation | Contingency | Residual risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KV5-RSK-001 | Archaeological fiction is presented as fact; trigger is an untagged or forbidden traversable object. | medium | high | design/research | Evidence classes, truth audit, static names, visual boundary. | Block gate, remove claim/route, rerun truth and visual tests. | low |
| KV5-RSK-002 | Large map becomes repetitive or disorienting; trigger is failed route time, dead-end, landmark, or cold-navigation review. | high | high | level design | Authored loops, district landmarks, acoustic identities, route budgets. | Revert latest route batch and shorten/reconnect district. | medium |
| KV5-RSK-003 | V4 regresses while V5 grows; trigger is geometry/hierarchy diff or visual mismatch. | medium | high | Unity implementation | Independent V5 roots and V4 contract test. | Remove V5 integration batch and restore last accepted root. | low |
| KV5-RSK-004 | Evidence ledger drifts from status; trigger is `[x]` without valid joined evidence. | medium | high | Codex/harness | Content-aware validator and one ledger owner. | Reopen item/gate; regenerate evidence on current revision. | low |
| KV5-RSK-005 | Dirty worktree causes accidental overwrite or false revision binding. | high | high | Codex/git | Scoped edits, focused diffs, artifact fingerprint at Gate 0, commit binding later. | Stop, identify ownership, preserve user changes, rebuild only task files. | medium |
| KV5-RSK-006 | Editor performance appears acceptable but player fails. | medium | high | performance | Target-player baseline and final player profiling. | Reopen Gate 6 and optimize by district. | low |
| KV5-RSK-007 | Simulated eight-state roster is mistaken for real multiplayer. | medium | medium | gameplay/product | Explicit scope and evidence wording. | Correct release claims and reopen affected acceptance. | low |
| KV5-RSK-008 | Fable review fails silently or returns warning-only text. | medium | high | harness | Verdict token, output-content validation, missing output blocks gate. | Retry once with tightened prompt; repeated failure uses blocker analysis. | low |

## Risk Review Protocol

- Review risks at every gate entry and exit.
- A trigger changes the owning status item to `[!]` immediately.
- High-impact unmitigated risk blocks gate closure.
- New risk adds a new ID; do not rewrite prior risk history to make it appear anticipated.
- Accepting residual risk requires a decision with owner, scope, expiry/review gate, and evidence.

## Pending Decisions

- Target-machine performance budgets after Gate 1 baseline.
- Final district bounds if the 250 m by 180 m envelope changes by more than 10%.
- Whether V5 needs additive scenes or independent roots in `School_MVP` are sufficient after
  graybox performance evidence exists.
