# Khufu V5 Implementation Final Review Pack

You are Claude Fable 5 acting as the final high-risk verifier in a Fable-to-Codex-to-Fable loop.
Do not implement and do not praise. Findings first. Review only the evidence below. Keep the answer
under 1,200 tokens.

## Goal

Ship an authored Unity 6 Khufu mega-labyrinth for the eight-state Traitor Escape MVP. Preserve the
validated V4 dense-core pyramid, add a much larger readable surface/underworld maze, support Sun,
Crown, and Earth keys in any order through mission-terminal confirmation and Valley Gate
extraction, provide bounded operator view, preserve explicit FACT/UNKNOWN/FICTION truth language,
and leave revision-bound visual, traversal, build, performance, and harness evidence.

## Completion Surface

- One committed implementation at `81c28f84d61d875a54f39d3fc74b202319103e24`.
- Unity static and PlayMode validators pass on that scene/source revision.
- Deterministic captures and independent visual checklist pass.
- Windows Development Player build and a separate visible-window final profile pass a frozen
  baseline budget.
- V4 post-check matches the pre-V5 V4 contract.
- All harness docs, evidence joins, and fail-closed unit tests pass.
- Your output contains one final decision line exactly as specified below.

## False-Done Conditions

`ship` is false if V4 changed silently; markers substitute for reachable physical routes; key
identity/order/terminal state can be spoofed; the map is a hollow screenshot shell; archaeology
fiction is presented as fact; Editor or black-window profiling substitutes for a Windows Player;
V2 evidence is mislabeled as V5; simulated proxies are called real multiplayer; evidence is stale
or uncommitted; or a required manual/external review is missing.

Decision needed:

Choose `ship`, `revise`, or `investigate`. In particular, decide whether accepted decision
`KV5-D-012` is a legitimate test-surface substitution and whether the explicitly limited
reviewer-plus-replay social rehearsal satisfies the V5 simulated-roster contract without making a
human multiplayer claim.

What would change implementation:

- `ship`: Codex runs a fresh README-only cold-reader audit, commits Gate 7 evidence, creates the
  final receipt, and verifies `--require-committed`.
- `revise`: Codex applies only concrete blockers, reruns affected Unity/build/evidence surfaces,
  and returns another final review.
- `investigate`: Codex runs the exact missing experiment before changing code.

## Risk Score: 7/10

- Cross-module Editor builder, generated scene, runtime map binding, MVP session, and validators.
- Large implementation commit: 100 files, 93,837 insertions, 452 deletions; most insertion volume
  is generated Unity YAML/material assets.
- Windows-specific build and GPU/profile evidence.
- Shared V4/legacy MVP compatibility and manually judged visual/social surfaces.

## Implementation Summary

- `ChannelPlayKhufuMegaLabyrinthV5Builder.cs`: rebuilds V4 first, adds a sibling V5 root with 11
  named districts, six loops, three far-side shortcuts, three key paths, physical maze galleries,
  underworld, landmarks, and truth boundary.
- `TraitorEscapeMapBindings.cs`: serializes spawn, terminals, exit, scanner, three key transforms,
  and operator bounds; present-invalid bindings fail runtime initialization instead of silently
  generating a fallback map.
- `KhufuObjectiveState.cs`: distinct `Sun`, `Crown`, `Earth` HashSet state; duplicates do not
  advance; mission terminal confirms only all three; extraction requires keys plus confirmation.
- `TraitorEscapeMvpSession.cs`: resolves authored transforms, resets to authored positions,
  disables operator key-assist for V5 physical acceptance, clamps V5 camera bounds, and separates
  participant/context/scoreboard UI columns.
- `ChannelPlayKhufuV5AcceptanceValidator.cs` and `ChannelPlayKhufuV5PlayModeProbe.cs`: assert
  hierarchy, graph, truth classes, route thresholds, six key permutations, terminal/shop/exit,
  shortcuts, CharacterController movement, clearance, and operator coverage.
- Screenshot exporter: eight deterministic static views with camera metadata, scene/source/Git
  hashes, luminance/duplicate checks; three PlayMode UI states reviewed separately.
- Performance probe and Python validator: raw Player profile, screenshot integrity, frozen budgets,
  and fail-closed mutation tests.

## Key Validation Evidence

1. Gate 4 static: `result=passed objective_permutations=6 clearance_samples=415 key_routes=3
   hub_proxies=8`.
2. Gate 4 PlayMode: `result=passed permutations=6 traversal_m=1758.6 steps=3533
   max_error=0.338`; critical route `898.6 m`; Sun/Crown/Earth `216.2/332.9/310.9 m` and
   `48.0/74.0/69.1 s` at 4.5 m/s; three shortcut lock/unlock/reset checks; zero Unity errors.
3. V4 post-check: 217 core blocks, 8 casing panels, cut ratio 0.026, 14 corbel bands, 5 relieving
   chambers, zero envelope violations. Values exactly match the pre-V5 receipt. Hierarchy remains
   one V4 sibling root with seven ownership children.
4. Visual: eight static plus three UI images are nonblank, hash-distinct, revision-bound; separate
   checklist passes silhouette, dense core, landmarks, underworld loops, truth labels, operator
   framing, and UI fit. Scope is authored high-quality blockout, not photoreal final art.
5. Windows build: Development Player exit success, zero errors, 138.57 MB. 185 warnings are
   upstream Sentis D3D11 shader compiler warnings; no V5 warning/error was identified.
6. Frozen ZENOVIS budget: minimum 3,000 samples; frame p95 <=9.0 ms; main/render/GPU p95 <=4.5 ms;
   allocated <=190 MB. Independent final: 3,580 samples, frame 8.337, main 2.401, render 2.794,
   GPU 2.240 ms; allocated 149.7 MB; all geometry/memory limits pass.
7. Python focused suite: 15/15. It includes performance over-budget, duplicate screenshot, error-log,
   and missing-GPU failures plus harness stale-hash, malformed Fable, missing RULES, and missing
   evidence failures.
8. Working-tree harness before this review: `HARNESS_VERDICT: passed`, 14 requirements, 16 tests,
   19 evidence rows, artifact SHA256
   `2bb114ab154aea74d70b6bc764b6a4401b860fbf84a03096bf9315f6c15101b0`.
9. `tools/channelctl unity check --batch`: Unity exit 0, compile errors 0. Generic playtest: exit 0,
   compile errors 0, 15/15 checks.

## Transparent Failed/Invalid Evidence

- A hidden-window performance attempt produced black screenshots and unavailable GPU/render data;
  it is retained as invalid and excluded from the budget/final verdict.
- Legacy `tools/channelctl unity sim-check` exited 1 with zero compiler errors because it hard-codes
  absent `Runtime_Pyramid_Maze_V2` and `MazeV2_*` markers, including Djoser/Hawara names forbidden
  in V5. `KV5-D-012` retains this failure and substitutes the V5 Gate 4/PlayMode probe only for the
  V2-root/scripted-route portions. The V2 agent command was not rerun because source accepts only
  `pyramid-maze-v2`; no V2 failure is represented as a pass.

## Social Rehearsal Scope

- Reviewer: Codex interactive Unity/visual reviewer, explicitly not described as a human player.
- Replay: committed 3,533-step CharacterController path, 415 clearance samples, top-down/player
  captures, and a live hub snapshot with one player plus seven proxies.
- Hub snapshot: 8 actors, minimum horizontal spacing 6.002 m, max hub radius 8.430 m; bot colliders
  are triggers, so the scoped proxies cannot persistently body-block.
- Every route has live-scene public/private markers and a connected return: Sun
  `(80,0.6,50)/(40,0.6,60)`, Crown `(30,3.4,-60)/(-74.3,4.4,38.3)`, Earth
  `(45,-4.6,-70)/(-85,-18.6,-55)`.
- Known limit: no human networked eight-player session. Release language is limited to the tested
  simulated eight-state roster, matching GOAL's explicit false-done rule against implying real
  multiplayer.

## Known Remaining Work

- Gate 7 docs/evidence are intentionally uncommitted until your review; unrelated worktree changes
  remain untouched.
- Fresh README-only cold-reader and final committed-mode harness receipt happen after your verdict
  so they describe the final state.
- No real multiplayer, human deception-balance study, photoreal art, or mobile/console profile is
  claimed.

Ask:

1. List only blocking findings, with the file/class/evidence surface affected and the minimum
   closure action.
2. List non-blocking improvements only if they reduce a concrete risk.
3. Audit `KV5-D-012`, revision binding, V4 preservation, objective correctness, traversal proof,
   truth boundary, visual scope, Windows performance, and the social-rehearsal scope.
4. End with exactly one final non-empty line and no other verdict token:

`FABLE_VERDICT: ship`

or

`FABLE_VERDICT: revise`

or

`FABLE_VERDICT: investigate`
