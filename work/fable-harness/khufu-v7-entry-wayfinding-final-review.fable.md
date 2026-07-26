## Blocking findings

1. **Staged-scope gate has no negative-test evidence.** The completion surface requires a "mutation-tested … staged-scope gate," but evidence only says Codex *will* run the aggregate validator with `--staged` after this verdict. No result shows the gate failing when an out-of-scope file is staged. Since "unrelated dirty-worktree files entering the commit" is an explicit false-done condition and the worktree is heavily dirty, this is the one unprotected surface. Required Codex-side check, inside the ship path before the commit: stage the V7 whitelist plus one deliberately out-of-scope dirty file (e.g., `tools/studio/app/app.js`), confirm `--staged` validation fails, unstage it, confirm it passes, then commit. This is executable within the unlocked ship flow, so it conditions the commit rather than forcing a revise loop.

No other blockers: numeric claims are corroborated by the inspected screenshot, the mutation control fails for the stated reason (center sample resolves to the renamed blocking pylon, route-clear false), frozen inputs are 14/14, and Gate 4 / PlayMode / build / perf are fresh and within budget.

## Non-blocking risk reductions

- **Dual hide mechanisms** (`Renderer.enabled=false` for exact pylons vs. `forceRenderingOff` for generic candidates) means two restore paths. Add one assertion in the synthetic regression that, post-restore, *both* `enabled` and `forceRenderingOff` match the pre-test snapshot for every touched renderer, not just visibility.
- **Mutation-run scene hygiene:** the name-mutation capture necessarily ran on a modified scene. Confirm the aggregate receipt records that the post-mutation scene hash returned to `a17075bc…` (the frozen-hash pass suggests it did; make it explicit in the receipt).
- **Single-frame proof at t=3s** is timing-sensitive. Cheap hardening: sample two frames ~0.5s apart and require both to satisfy the predicate. Not required for this slice.

## Requested assessments

- **Exact-pylon renderer-disable restoration:** Correct design. Exact-name matching (`V5_Valley_Gate_Pylon_-1` / `_1`) avoids the forbidden broad-pylon match; the causeway-pylon control proves scoping. `enabled=false` avoids the black-rectangle artifact seen with `forceRenderingOff` (rejected attempt 2). Restoration is exercised by the synthetic regression; see the dual-path assertion above.
- **V7 look-ahead API scope:** Acceptable. `ChannelFollowCamera` retains default `(0,6,-8)`, so scenes without a `KhufuV7EntryCameraProfile` are behaviorally unchanged; execution order 50→100→200→300 gives a deterministic profile→camera→cutaway→probe pipeline with no same-frame race.
- **Visual proof predicate:** Sound. It is conjunctive (player in frame ∧ ≥2 guides ∧ center = route floor ∧ route clear), grounded in a 3x3 environment grid rather than pixel color alone, and mutation-tested with a failure mode that matches the intended semantics — the predicate fails *because the route is blocked*, not incidentally. The rejected-attempt history shows the predicate was actually discriminating, not tuned to pass.
- **Scene/build binding:** Adequate. One scene hash spans static validation, PlayMode, build, captures, and perf; the aggregate validator re-verified 14/14 frozen inputs afterward, and PlayerSettings were restored byte-for-byte. Ensure the final aggregate receipt embeds the scene hash alongside the capture artifact digest `28dae0b2…` so the binding is auditable from the receipt alone.

FINAL_REVIEW: ship
