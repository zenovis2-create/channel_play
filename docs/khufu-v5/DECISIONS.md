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

### KV5-D-006: Freeze the V5 World and District Contract

- Status: accepted
- Date: 2026-07-10
- Context: V4 and the MVP runtime use fixed names and positions, while V5 needs a 250 m-class map.
- Decision: Freeze the axes, envelope, eleven direct district roots, objective positions, evidence
  classes, and route thresholds in PLAN before builder implementation.
- Evidence: `KV5-E-010`.
- Consequence: Any coordinate or district-contract change requires a replacement decision and
  reruns the structural, traversal, and visual evidence.

### KV5-D-007: Use an Explicit Runtime Map Binding

- Status: accepted
- Date: 2026-07-10
- Context: The MVP session discovers only direct children by name and resets authored objects to
  legacy hard-coded coordinates.
- Decision: Put one runtime-safe serialized binding component on `TraitorEscape_Runtime_Map`.
  Runtime resolves and validates it first; absent bindings use the legacy fallback, while invalid
  present bindings fail loudly. Initial authored transforms become the reset source of truth.
- Evidence: `KV5-E-010` architecture review.
- Consequence: Editor builders remain outside gameplay assemblies, nested district geometry stays
  independent, and V4/MVP rollback remains possible.

### KV5-D-008: Separate Visual District Surfaces from Traversal Ownership

- Status: accepted
- Date: 2026-07-10
- Context: Actual CharacterController probes found overlapping district floors, route floors, and
  V4's continuous desert collider blocking otherwise clear authored routes.
- Decision: Route floors own required-path collision; district color floors and landmark/route
  side walls remain visual. Two isolated physical maze galleries retain collidable maze play. The
  V4 desert mesh remains unchanged visually and hierarchically, but its collider is disabled by
  the V5 integration so the fictional underworld can exist below it.
- Evidence: `runs/khufu-mega-labyrinth-v5/gate4-acceptance.md` and PlayMode failure receipts.
- Consequence: V4 geometry remains intact while V5 collision ownership is explicit and testable.

### KV5-D-009: Move Hub Terminals off the Critical Route

- Status: accepted
- Date: 2026-07-10
- Context: The PlayMode controller probe hit the shop terminal at `(58,1.2,4)` on the Hub-to-Sun
  route.
- Decision: Place mission and shop terminals at `(62,1.2,8)` and `(62,1.2,-8)` respectively.
- Evidence: `runs/khufu-mega-labyrinth-v5/playmode-probe.md`.
- Consequence: Both terminals remain in the public hub but no longer obstruct required traversal.

### KV5-D-010: Expand and Reframe the V5 Operator Camera

- Status: accepted
- Date: 2026-07-10
- Context: Actual PlayMode Game View evidence showed the 72 m, 70-degree operator start clipping
  through the pyramid and losing the 270 m by 200 m surface route. Context panels also shared the
  left HUD column and obscured one another at the available Editor proof viewport.
- Decision: For authored V5 bindings, start the operator camera at `(25,135,0)`, look vertically
  down, use a 75-degree vertical FOV, and permit height `[12,160]`. Restore 60-degree FOV on return
  to participant mode. Use left participant HUD, centre contextual panel, and right scoreboard
  columns; hide the duplicate manual panel while shop or operator UI is open.
- Evidence: `runs/khufu-mega-labyrinth-v5/captures/playmode-ui-manifest.md` and
  `runs/khufu-mega-labyrinth-v5/visual-review.md`.
- Consequence: Operator mode frames the complete surface map without changing legacy fallback
  camera behavior. Gate 6 must repeat the UI fit check in the Windows Development Player.

### KV5-D-011: Freeze the ZENOVIS Windows Player Budget

- Status: accepted
- Date: 2026-07-11
- Context: A visible-window Development Player baseline on ZENOVIS at 1536x1024 Ultra and a
  120fps cap recorded 3577 samples. P95 was 8.338 ms frame, 2.463 ms main thread, 2.829 ms render
  thread, and 2.246 ms GPU; maximum allocated memory was 149.8 MB. An earlier hidden-window run
  produced black captures and unavailable GPU data and is explicitly invalid.
- Decision: Accept the machine, procedure, and limits in
  `runs/khufu-mega-labyrinth-v5/performance-budget.json`. Required p95 limits are 9.0 ms frame and
  4.5 ms each for main, render, and GPU; allocated memory is limited to 190 MB. Geometry and raw
  capture limits are also fail-closed in the validator.
- Evidence: `runs/khufu-mega-labyrinth-v5/performance-baseline/baseline-performance.md` and
  `runs/khufu-mega-labyrinth-v5/performance-budget.json`.
- Consequence: The same Development Player must run a separate final profile and pass
  `tools/validate_khufu_v5_performance.py`. Editor or hidden-window numbers cannot pass Gate 6.
  The build-warning baseline is `185` upstream Sentis D3D11 shader compiler warnings; any increase
  or any non-Sentis warning must be investigated rather than absorbed as known noise.

### KV5-D-012: Replace V2-Only Simulation Proof with the V5 Probe

- Status: accepted
- Date: 2026-07-11
- Context: `tools/channelctl unity sim-check` and `unity agent-playtest pyramid-maze-v2`
  hard-code `Runtime_Pyramid_Maze_V2` and `MazeV2_*` markers. The accepted Khufu V5 scene removes
  that root, and the V2 route includes Djoser/Hawara names forbidden by `KV5-R-001`. Running the
  V2 agent again would test the wrong map and repeat the known missing-root failure.
- Decision: Keep `tools/channelctl unity check --batch` and the generic 15-check playtest as common
  regression surfaces. For only the V2-root and scripted-route portions of `KV5-T-011`, use the
  committed V5 Gate 4 validator and V5 PlayMode probe. Retain the failed V2 sim receipt as
  fail-closed applicability evidence; never relabel it as a pass.
- Evidence: `runs/khufu-mega-labyrinth-v5/channelctl-validation.md`,
  `runs/khufu-mega-labyrinth-v5/gate4-final.md`, and
  `runs/khufu-mega-labyrinth-v5/playmode-probe.md`.
- Consequence: V5 acceptance proves its own named keys, controller routes, terminal/shop/exit flow,
  shortcuts, and collision metrics. Legacy V2 simulation coverage remains unchanged for V2 and is
  not claimed for V5. A future `channelctl` V5 subcommand is tooling work, not a requirement for
  this map revision.

#### KV5-D-012 Assertion Map

No legacy assertion is dropped implicitly. `N/A` means the assertion belongs to the V2 sensor or
action-transport harness and is outside the Khufu V5 map goal.

| Legacy V2 assertion | V5 disposition | Exact evidence |
| --- | --- | --- |
| `School_MVP` scene opens | substituted | Generic playtest `15/15`; Gate 4 opens the committed scene |
| `Runtime_Pyramid_Maze_V2` exists | substituted with V5 identity | Static validator requires exactly one `Runtime_Khufu_Mega_Labyrinth_V5` sibling root |
| Six named `MazeV2_*` markers exist | substituted | V5 graph validator requires 11 districts, six major loops, three shortcuts, and a connected ordered critical route |
| Missing V2 maze is generated by `ChannelPlayPyramidMazeV2Builder` | N/A by design | V5 is an authored committed scene; present-invalid authored bindings fail rather than silently building a different map |
| Command artifact lists V2 route and `ChannelSimRuntime.AllowedActions` | N/A | V2 simulation transport contract is not part of `KV5-R-001` through `KV5-R-014` |
| Route receives segmentation IDs and semantic labels | N/A for sensor IDs; truth contract substituted | V5 truth-tag audit plus hashed FACT/UNKNOWN/FICTION captures |
| Temporary capsule agent spawns at first marker | substituted with stronger runtime surface | V5 PlayMode probe uses the real `MVP_Player` CharacterController at the authored spawn |
| Agent moves, looks, waits, and writes trajectory points | movement/trajectory substituted; look/wait N/A | `1758.6 m`, `3533` controller steps, maximum error `0.338 m`, and per-key route metrics |
| RGB, segmentation, and depth observations are captured | RGB substituted; segmentation/depth N/A | Eight deterministic static views and three UI captures with distinct hashes and visual review |
| Agent interacts with each V2 marker | substituted with gameplay assertions | Six physical-key orders, duplicate rejection, terminal confirmation, shop usability, early-exit rejection, and final extraction |
| Unsupported action is rejected | N/A | Legacy action-executor protocol is not used by V5 gameplay |
| Metrics, review, and final receipt are written | substituted | Gate 4, PlayMode, social-rehearsal, visual, performance, and final harness receipts |

### KV5-D-013: Bind Dirty Build Inputs Without Taking Ownership

- Status: accepted
- Date: 2026-07-11
- Context: Fable's implementation review found that the Windows Player depended on locally modified
  `ProjectSettings` and package files excluded from implementation commit `81c28f84...`. Committing
  those unrelated settings would violate worktree ownership, while ignoring them would make the
  Player/performance revision claim incomplete.
- Decision: Commit a build-input manifest containing the live scene, ProjectSettings, package,
  Unity Bee input/report, and Player-output hashes. The harness recomputes those hashes on every
  run. It also derives the exact build-time `enableFrameTimingStats: 1` ProjectSettings hash from
  the restored `0` state and requires exactly one known replacement. `--require-committed` requires
  the manifest itself to be tracked but does not stage the bound user-owned files.
- Evidence: `runs/khufu-mega-labyrinth-v5/build-input-binding.json`,
  `runs/khufu-mega-labyrinth-v5/build-input-binding.md`, and the build-binding mutation tests.
- Consequence: Any later scene, graphics, quality, player, build-scene, package, or provenance drift
  fails the final harness. The local settings stay untouched and cannot inherit the accepted
  performance claim after their bytes change.

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
| KV5-RSK-009 | Trigger-only proxy spacing is mistaken for human chokepoint contention proof. | medium | medium | level design/product | Name the proxy-collider limitation in social evidence and release notes. | Run a future human multiplayer chokepoint session before making balance claims. | UNKNOWN outside V5 scope |

## Risk Review Protocol

- Review risks at every gate entry and exit.
- A trigger changes the owning status item to `[!]` immediately.
- High-impact unmitigated risk blocks gate closure.
- New risk adds a new ID; do not rewrite prior risk history to make it appear anticipated.
- Accepting residual risk requires a decision with owner, scope, expiry/review gate, and evidence.

## Pending Decisions

- None before Gate 7 review. A new decision is required if final Fable review changes scope,
  evidence thresholds, or the accepted simulated-roster boundary.
