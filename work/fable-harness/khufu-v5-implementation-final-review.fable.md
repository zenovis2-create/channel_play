## Final Review — Khufu V5 (commit `81c28f84`)

### Blocking findings

None that require code changes. Two conditions are load-bearing for the `ship` path and must fail the release if they don't hold:

1. **Committed-mode binding must cover build-affecting project files.** The working tree carries uncommitted modifications to `ProjectSettings/ProjectSettings.asset` and `ProjectSettings/EditorBuildSettings.asset`, and the Windows Player performance evidence (Gate: frozen ZENOVIS budget) depends on quality/graphics/build settings from those files. If the evidence hash join binds only scene/source/Git commit hashes and not the project-settings state actually used by the Player build, the performance receipt is bound to a revision that did not produce it. Exact Codex-side check: confirm the evidence join manifest includes ProjectSettings hashes (or commit them in the Gate 7 commit) and verify `--require-committed` fails closed on any mismatch. If that verification fails, the decision reverts to `revise` — do not rationalize it as unrelated drift.

2. **`ship` is conditional on the deferred Gate 7 sequence completing as specified.** Cold-reader README audit, Gate 7 evidence commit, final receipt, and `--require-committed` pass are all post-verdict by design. That is acceptable per the stated protocol, but any failure in that sequence invalidates this verdict; no partial pass may be reported as done.

### KV5-D-012 audit

The substitution is **legitimate as scoped, with one closure requirement.** The legacy `sim-check` hard-codes `Runtime_Pyramid_Maze_V2` and `MazeV2_*` markers including names V5 explicitly forbids; its exit-1 with zero compiler errors is a contract mismatch, not a regression, and the failure is retained transparently rather than masked. However, the pack states the V5 Gate 4/PlayMode probe substitutes "only for the V2-root/scripted-route portions," which leaves the remaining sim-check assertions unaccounted. Minimum closure (documentation, foldable into Gate 7): an assertion-by-assertion map in the KV5-D-012 record showing each legacy check as either V5-substituted (with the specific Gate 4/PlayMode assertion) or explicitly N/A with rationale. Without this map, a future auditor cannot verify nothing was silently dropped alongside the V2 markers.

### Contract-by-contract audit

- **Revision binding:** Screenshots carry scene/source/Git hashes; harness passed in working-tree mode with a recorded artifact SHA256. Adequate, subject to finding 1 above.
- **V4 preservation:** Post-check metrics (217 core blocks, 8 casing panels, cut ratio 0.026, 14 corbel bands, 5 relieving chambers, zero envelope violations) exactly match the pre-V5 receipt, with a single V4 sibling root intact. The "silent V4 change" false-done condition is closed.
- **Objective correctness:** Distinct-key HashSet, duplicate non-advancement, all-three terminal confirmation, and keys-plus-confirmation extraction are asserted across six permutations in both static and PlayMode validators. Present-invalid bindings fail initialization rather than falling back — the spoofing and hollow-shell conditions are closed.
- **Traversal proof:** 3,533-step CharacterController replay (1,758.6 m, max error 0.338), per-key route distances/times, 415 clearance samples, and three shortcut lock/unlock/reset checks constitute physical-route evidence, not marker substitution.
- **Truth boundary:** FACT/UNKNOWN/FICTION classes are validator-asserted and visually checklist-confirmed; no fiction-as-fact claim appears in the evidence.
- **Visual scope:** Eleven nonblank, hash-distinct, revision-bound captures with an independent checklist; scope is honestly declared as authored blockout, not photoreal.
- **Windows performance:** Visible-window Development Player, 3,580 samples against a 3,000 minimum, all p95 metrics inside the frozen budget (frame 8.337 vs 9.0 ms is the tightest margin — note it, since a release-config regression has little headroom). The hidden-window black-screenshot attempt is correctly retained as invalid and excluded. The Editor/black-window false-done condition is closed.
- **Social rehearsal:** Reviewer-plus-replay with one player and seven trigger-collider proxies, disclosed spacing/radius metrics, and release language explicitly limited to the simulated eight-state roster. This satisfies the V5 simulated-roster contract without a human-multiplayer claim.

### Non-blocking improvements (risk-reducing only)

- **Proxy trigger colliders cannot body-block:** disclosed, but it means chokepoint contention — a core traitor-escape dynamic — is untested. Record this as a named UNKNOWN in the release notes so it isn't rediscovered as a surprise in any future human session.
- **Performance margin note:** frame p95 has ~8% headroom under a Development Player, which carries profiling overhead; a release-profile spot check would cheaply confirm the budget isn't Development-config-dependent.
- **Sentis D3D11 warnings (185):** upstream and correctly excluded, but pin the count in the baseline so a future increase is detectable rather than absorbed into "known noise."

### Decision rationale

Every enumerated false-done condition is either closed by direct evidence or explicitly out of scope with matching release language. Failed evidence is retained and labeled rather than hidden. The two open items are exactly the steps the `ship` path already specifies, plus one documentation closure (the KV5-D-012 assertion map) and one binding check (ProjectSettings coverage) that `--require-committed` verification must enforce.

FABLE_VERDICT: ship
