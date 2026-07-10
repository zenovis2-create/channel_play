# Khufu V5 Goal and Invariants

Updated: 2026-07-10
Goal state: proposed for Gate 0 acceptance

## Intent

Build a large, readable, high-quality Unity map that combines Khufu's confirmed pyramid complex
with an explicitly fictional underworld labyrinth for the eight-participant Traitor Escape MVP.
The map must feel much larger than V4, preserve the validated V4 dense-core pyramid as its central
archaeological spine, support all three keys and extraction, and produce evidence strong enough
to distinguish completion from a convincing screenshot.

## Completion Surface

Completion requires all of the following:

- the authored map exists in Unity and compiles;
- the route graph, three keys, mission terminal, shop, shortcuts, and final exit are playable;
- measured route, collision, operator-view, screenshot, and performance evidence passes;
- archaeology-derived content remains tagged by evidence class;
- every requirement is covered by a test and a revision-bound receipt;
- required Fable plan and final reviews return accepted verdicts;
- completed, unresolved, and unverified work are reported separately.

## Scope

In scope:

- V5 map blockout and its district hierarchy;
- V4 integration without weakening its dense-core contract;
- surface complex, authentic interior spine, and fictional underworld;
- current local Traitor Escape MVP integration;
- route, visual, performance, operator, simulation, and regression proof;
- supporting validators, captures, receipts, and review artifacts.

Out of scope unless a later accepted decision adds it:

- real multiplayer transport and server authority;
- photorealistic final art for every district;
- a literal reconstruction of unknown spaces;
- target platforms other than the current Windows development target;
- rewriting unrelated game-show systems.

## Evidence Classes

Archaeology-derived requirements and objects use one class:

- `FACT`: physically documented or institutionally mapped.
- `UNKNOWN`: detected with high confidence but access, form, or purpose remains incomplete.
- `HYPOTHESIS`: scholarly reconstruction or interpretation without settled proof.
- `FICTION`: deliberate gameplay invention.
- `HYBRID`: grounded spatial relationship with gameplay-compressed geometry.
- `N/A`: not an archaeology claim.

`UNKNOWN` and `HYPOTHESIS` never become traversable fact through art direction alone.

## Measurable Requirements

| ID | Evidence class | Requirement and acceptance threshold |
| --- | --- | --- |
| KV5-R-001 | FACT/UNKNOWN/FICTION | Every archaeology-derived district root and design record has one evidence class; SP-BV, SP-NFC, Queen's Chamber shafts, Djoser, and Hawara are never presented as confirmed traversable Khufu rooms. |
| KV5-R-002 | FACT | The existing V4 pyramid keeps its 56 m base, 35.636 m height, dense section mass, known chamber spine, seven Grand Gallery corbels per side, and five bounded relieving chambers unless a later decision explicitly supersedes V4. |
| KV5-R-003 | HYBRID/FICTION | V5 provides at least eight named major districts within a target playable envelope near 250 m by 180 m and vertical range near -34 m to +36 m; deviations above 10% require a recorded decision. |
| KV5-R-004 | N/A | The route graph contains at least six major loops and three far-side-unlocked reconnecting shortcuts; no required objective depends on a permanent one-way trap. |
| KV5-R-005 | N/A | Sun, Crown, and Earth keys are collectible in any order; the mission terminal recognizes all three; the Valley Gate opens only after the required flow completes. |
| KV5-R-006 | N/A | The measured all-key critical route is 700-900 m; no unrewarded dead end costs more than 15 seconds at 4.5 m/s walk speed; hub-to-key walk time is 45-75 seconds. |
| KV5-R-007 | N/A | Eight participant proxies can circulate through the Temple Hub without persistent body blocking; each key route has a public interaction and a private-risk segment; single-exit high-risk spaces reconnect within 20 seconds. |
| KV5-R-008 | N/A | Operator mode can frame every macro district, identify all active objectives, and follow the full spawn-to-extraction route without clipping or losing the map bounds. |
| KV5-R-009 | N/A | Performance budgets are frozen from a Windows player baseline before art lock; final Windows player captures meet the accepted frame-time, memory, and visible-object budgets. Editor-only profiling cannot pass this requirement. |
| KV5-R-010 | N/A | Unity compile, EditMode/static validation, PlayMode smoke, scripted traversal, and receipt generation all exit successfully with zero unexpected error logs. |
| KV5-R-011 | FACT/UNKNOWN/FICTION | Required desktop screenshots and traversal captures show a complete pyramid silhouette, dense core, readable landmarks, non-overlapping UI, and an unmistakable truth boundary before the fictional underworld. |
| KV5-R-012 | N/A | Required Fable plan and final-review outputs exist, contain an explicit accepted verdict token, and have no `FABLE_HARNESS_ERROR` or tool-call warning. |
| KV5-R-013 | N/A | Each implementation gate has a rollback boundary, preserves unrelated worktree changes, and binds passing evidence to the tested commit. |
| KV5-R-014 | N/A | No `[x]`, passed gate, release claim, or final answer is allowed without resolvable evidence whose content and revision match the claim. |

## Non-Negotiable Invariants

### Truth

- V4 is the confirmed central spine; V5 grows around and below it.
- SP-BV and SP-NFC are observation/lore surfaces, not player rooms.
- Queen's Chamber shafts are not human traversal paths.
- Djoser and Hawara names do not appear in the Khufu V5 runtime hierarchy or player-facing UI.
- Fictional underworld content crosses a visible, documented truth boundary.

### Gameplay and Navigation

- Use authored loops, landmarks, and shortcuts, never a random grid as the critical path.
- Every objective branch reconnects without a full-map backtrack.
- No corridor longer than 30 m remains visually and acoustically unchanged.
- The current 4.5 m/s walk and 7.0 m/s sprint speeds are the timing baseline until changed by
  an accepted decision.
- Blind spots create incomplete information, not unavoidable elimination traps.

### Engineering

- Reuse existing project patterns and validators before adding dependencies.
- Do not mutate V4 while building surrounding districts until the integration gate allows it.
- Keep each district under an independent root for rebuild, culling, validation, and rollback.
- Generated receipts go under `runs/`; Fable packs and outputs go under `work/fable-harness/`.
- Never revert or overwrite unrelated dirty-worktree changes.

### Evidence

- A screenshot proves only its visible frame.
- A compile proves only compilation and the checks executed by that command.
- Editor profiling is diagnostic, not final performance proof.
- Missing, empty, stale, or mismatched evidence is failure, not uncertainty disguised as success.
- Same blocker twice triggers Fable `blocker-analysis`; it does not authorize blind retries.

## False-Done Conditions

The goal is not complete if any condition below is true:

1. The map resembles the concept image but three-key extraction is not playable.
2. One hero image looks correct but player, operator, or route surfaces fail.
3. V4 geometry or archaeology truth changed without an accepted decision.
4. A scan anomaly or external Egyptian monument is mislabeled as confirmed Khufu traversal.
5. Route distance, dead ends, shortcuts, or collision clearance are estimated rather than measured.
6. Performance is inferred from the Editor or an unspecified target machine.
7. Any required Fable output is missing, failed, warning-only, or lacks an accepted verdict.
8. Any `[x]` item lacks a matching evidence ledger row and non-empty artifact.
9. Real multiplayer is implied even though only the simulated eight-state roster was tested.
