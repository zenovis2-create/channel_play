# Loop: Khufu V9 Causeway Fidelity

## Goal

Produce and prove one collision-faithful production-art corridor from Valley Gate to the V8 Temple Hub.

## Trigger

- Type: manual Codex engineering run
- Input schema: accepted V8 scene plus frozen V5-V8 sources and V9 docs
- Preconditions: V8 aggregate passes; Unity 6000.0.76f1 and Windows D3D11 player path are available

## State

- Durable state: V9 docs, generated meshes, scene root, receipts, bindings, captures, and commit
- Transient state: Unity batch logs, temporary mutation state, player process, profiler session
- Idempotency key: V8 scene hash plus V9 builder hash
- Completion marker: `V9_AGGREGATE_VERDICT: passed`
- Replay inputs: frozen commit, source hashes, Unity version, builder entrypoint, proof labels

## Tools

| Tool | Purpose | Success signal | Failure signal | Timeout | Retryable? |
| --- | --- | --- | --- | --- | --- |
| Unity batch | audit, rebuild, validate, build | explicit `result=passed` marker | nonzero exit or failed marker | 15 min | once after diagnosis |
| Python aggregate | bind evidence and scope | `V9_AGGREGATE_VERDICT: passed` | listed deterministic errors | 2 min | after repair |
| Windows player | traversal and proof | normal proof receipt and screenshot | timeout, blocked route, missing frame | 3 min | once after diagnosis |
| Profiler probe | target performance | budget validator passed | missing/raw-small/over-budget | 3 min | once after diagnosis |
| Local Fable review | final risk gate | `LOCAL_FABLE_DECISION: ship` | blocking finding | 5 min | after required fixes |

## Safety Gates

| Gate | Blocks when | Recovery |
| --- | --- | --- |
| Scope | a changed path is outside the V9 whitelist | unstage and isolate |
| Frozen input | V5-V8/package/source hash drifts | stop and inspect ownership |
| Collision | pairing or clearance fails | repair V9 proxy or visual only |
| Budget | renderer/geometry/frame limit fails | simplify or combine V9 art |
| Evidence | receipt is stale, blank, or unbound | regenerate matching surface |

## Observe-Decide Rules

- Done when: every V9 test passes on one scene/build binding and the commit is scoped.
- Retry when: a transient process or capture fails once with a diagnosed cause.
- Replan when: source geometry cannot meet collision or performance budgets.
- Escalate when: a second identical blocker or ambiguous scene-scope delta remains.
- Quarantine when: frozen V5-V8 or unrelated user work would be overwritten.

## Telemetry

- Required logs: Unity audit/build/validator, player proof, profiler, aggregate
- Required artifacts: generated meshes, scene, receipts, PNGs, raw profiler, executable binding
- Required operator report: completed, unresolved, unverified, and deferred scope
- Required metrics: renderers, vertices, triangles, collider pairs, clearance samples, frame/main/render/GPU p95

## Verification

- Unit checks: Python aggregate tests and deterministic mesh/pair helpers
- Integration checks: Unity static validator, V5 Gate 4, inherited traversal
- Dry run: source/scene audit without save
- Live canary: Windows participant corridor traversal
- Scorecard: loop contract score at least 90 before final commit
