# Loop: Khufu V5 Gate Execution

## Goal

Advance exactly one Khufu V5 gate at a time and produce a playable, visually inspected Unity map
without false completion, archaeology drift, or uncontrolled retries.

## Trigger

- Type: manual GOAL continuation or gate-resume message.
- Input schema: current gate ID, accepted commit, requirement/test IDs, and evidence ledger state.
- Preconditions: previous gate accepted; scoped files committed or explicitly fingerprinted;
  Unity editor path available; no unresolved blocking finding.

## State

- Durable state: `docs/khufu-v5/STATUS.md`, Git commits, and `runs/khufu-v5-*` receipts.
- Transient state: active Unity editor process, MCP connection, temporary RenderTextures.
- Idempotency key: `khufu-v5:<gate-id>:<commit-sha>:<attempt>`.
- Completion marker: accepted evidence row linked from the gate's `[x]` status line.
- Replay inputs: builder method, scene path, route-marker order, controller speeds, capture cameras.

## Tools

| Tool | Purpose | Success signal | Failure signal | Timeout | Retryable? |
| --- | --- | --- | --- | --- | --- |
| `apply_patch` | Scoped source/doc edits | Patch applied to named files | Patch error or conflicting current content | 30 s | replan once |
| Unity batch/MCP | Compile, build, validate, play, capture | Explicit `CHANNEL_PLAY_KHUFU_V5 ... passed` marker | compile error, missing marker, nonzero exit, timeout | 10 min | once after diagnosis |
| Harness validator | Join status/tests/evidence | `HARNESS_VERDICT: passed` | any ERROR line or nonzero exit | 2 min | only after content fix |
| Image inspection | Verify visual matching surface | readable nonblank required views | blank, clipped, overlapping, misleading structure | 5 min | up to 3 authored iterations |
| Git | Revision and rollback anchor | scoped commit and clean scoped status | identity, conflicts, unrelated staged files | 2 min | once after diagnosis |
| Local Fable review | Evidence-first gate review | `ship` or no blocking findings | revise/investigate or vague approval | 5 min | one tightened retry |

## Safety Gates

| Gate | Blocks when | Recovery |
| --- | --- | --- |
| Schema | Required IDs, markers, or verdict tokens are missing | Reject output and repair schema |
| Scope | Edit touches unrelated dirty files or V4 outside accepted boundary | Stop and narrow patch/restore task files only |
| Permission | Commit, install, or destructive action lacks authorization | Ask or remain at current gate |
| Budget | More than 3 implementation iterations or 2 identical failures | Stop, summarize, blocker-analysis |
| Risk | Archaeology class is unclear or fiction reads as fact | Quarantine district and revisit truth contract |
| Visual | No screenshot/playtest inspection exists | Keep gate open |
| Runtime | Compile passes but route/objective/operator behavior is untested | Keep gate open |

## Observe-Decide Rules

- Done when: every required test for the active gate has current revision-bound evidence and no
  blocking reviewer finding remains.
- Retry when: the failure is diagnosed, changed input can plausibly fix it, and retry budget remains.
- Replan when: exact failure repeats twice, route metrics conflict with layout, or a shared runtime
  contract must change.
- Escalate when: external Fable judgment would change architecture or a destructive action needs
  user approval.
- Quarantine when: a district violates evidence classes, corrupts V4, or cannot be rolled back
  independently.
- Fail when: budget expires, Unity cannot run, or matching-surface proof cannot be produced.

## Telemetry

- Required logs: gate, attempt, command/tool, latency, exit/verdict, exact error, next decision.
- Required artifacts: compile receipt, validator receipt, route metrics, screenshots, playtest log.
- Required user/operator report: completed, unresolved, unverified, and next gate.
- Required metrics: district/loop/shortcut count, route length, traversal result, error count,
  screenshot dimensions/nonblank pixels, player-build frame timing when Gate 6 begins.
- Trace fields: `loop.name`, `run_id`, `gate`, `attempt`, `commit`, `tool`, `status`, `evidence.ref`.

## Budgets and Stop Conditions

- Maximum attempts per gate implementation: 3.
- Maximum identical failure attempts: 2.
- Maximum active gate count: 1.
- Maximum external strong-review calls per gate: 1 plus one tightened retry.
- Stop immediately on unrelated file overwrite, V4 contract regression, or false historical claim.

## Verification

- Unit checks: validator methods and route/graph metrics.
- Integration checks: Unity compile, V5 build/validate method, runtime object binding.
- Dry run: validation against scene without PlayMode mutation where possible.
- Live canary: PlayMode scripted route and operator capture on the current Windows workspace.
- Scorecard: loop contract score must be >=80 before implementation and >=90 before final hardening.
