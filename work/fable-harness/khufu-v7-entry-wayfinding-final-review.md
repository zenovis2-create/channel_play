You are Claude Fable 5 performing the external final gate in a Fable-to-Codex-to-Fable harness.
Findings first. Do not implement and do not praise. Keep the answer under 1000 tokens.

Goal:
Ship a bounded Khufu V7 player-entry and wayfinding slice. Remove the initial Valley Gate camera
obstruction and make the fictional route toward the Temple Hub readable without changing accepted
V5/V6 topology or implying an archaeological reconstruction.

Completion surface:
- The current Unity scene is the exact scene bound by static validation, PlayMode, Windows build,
  normal/mutation entry captures, and performance evidence.
- Fourteen forbidden V5/V6/package/settings inputs retain their frozen SHA256 values.
- V7 owns a separate root with 8 renderers / 192 vertices / 96 triangles / 0 colliders.
- The participant is in frame, at least two guide strips project into the viewport, and the center
  viewport sample resolves to a route floor rather than a pylon.
- Renaming the two exact Valley Gate pylons causes the rendered proof to fail as expected and leaves
  the mutated pylon visibly blocking the center route.
- V5 Gate 4, CharacterController PlayMode traversal, Windows build, and the V5 performance budget pass.
- A mutation-tested aggregate validator and staged-scope gate protect the final commit.

False-done conditions:
A numeric pass contradicted by the screenshot; black/corrupt cutaway output; stale scene/build evidence;
broad pylon matching; mutation that still passes; frozen-input drift; or unrelated dirty-worktree files
entering the commit.

Decision needed:
Should Codex ship this V7 slice, revise a concrete blocker, or investigate more?

What would change implementation:
A concrete blocker will be fixed and affected Unity/player evidence rerun. A ship decision unlocks the
final aggregate receipt, explicit staging, staged-index validation, and one scoped commit.

Risk score: 5/10
- +2 shared camera/cutaway contracts plus generated scene and runtime proof.
- +2 changes across more than five files with Unity YAML serialization.
- +1 Windows/D3D11-specific rendered and profiler evidence.

Implementation facts:
- `ChannelFollowCamera` keeps its old default `(0,6,-8)` and adds V7-configurable offset/look-ahead;
  execution order is 100.
- `KhufuV7EntryCameraProfile` runs at 50 and applies offset `(3,7,-12)` plus look-ahead `(-7,0,0)`.
- `ChannelCameraOccluderCutaway` runs at 200. Only exact names
  `V5_Valley_Gate_Pylon_-1` and `V5_Valley_Gate_Pylon_1` receive the new pylon handling. Exact pylons
  use restorable `Renderer.enabled=false`; generic existing candidates retain `forceRenderingOff`.
- Synthetic regression hides a generic beam and both exact pylons, leaves
  `V5_Covered_Causeway_Pylon_1` visible, then restores all original states.
- `KhufuV7EntryProofProbe` runs at 300, samples after 3 seconds, forces a refresh, captures end-of-frame,
  and records a 3x3 viewport environment grid.
- Eight guide cubes reuse `V6_Scan_Inlay`, cast/receive no shadows, and have no colliders or new materials.
- Shared changes are limited to follow camera, cutaway, and the cutaway validator. V5/V6 builders are frozen.

Rejected visual attempts:
1. Cutaway-only numeric pass was rejected because a pylon filled the center view.
2. Hiding a second pylon via `forceRenderingOff` was rejected because black rectangles appeared.
3. A route-axis camera outside the gate was rejected because the locked exit door filled the foreground.
4. A high camera inside the gate was rejected because it showed only floor.
5. Look-ahead -18 and -10 were rejected because the player was absent or clipped.
The final -7 look-ahead screenshot was directly inspected: player fully visible at lower right, two floor
guides visible, forward route readable, no black/corrupt regions.

Evidence:
- Current scene SHA256: `a17075bcf6b21a5231edf32bb0247e3c755925a97c39c25a12dba506e40cf029`.
- Static validation/idempotence/off-route mutation: passed; signature
  `9730013ededc08da590b99de5d2bd1ae91c485b25d67e6c591117d4431c2d321`.
- Fresh V5 Gate 4: 6/6 objectives, 415 clearance samples, 8/8 hub proxies.
- Fresh PlayMode: 1,758.6m, 3,533 CharacterController steps, max error 0.338m.
- Windows Development Player: succeeded, 0 errors, 185 inherited third-party warnings; changed runtime
  source hashes and scene hash recorded; PlayerSettings restored byte-for-byte.
- Normal player proof: active cutaways 2, exact pylons 1, visible candidates 0, player in frame true,
  guides in viewport 2, center `V5_Route_Segment_24_Floor`, route clear true.
- Name mutation proof: exact pylons 0, center
  `V5_Valley_Gate_Pylon_-1_MUTATED_BLOCKING_CONTROL`, route clear false, failed-as-expected.
- D3D11/Ultra 1536x1024: 3,593 samples; frame p95 8.338ms, main 2.690ms, render 3.009ms,
  GPU 2.354ms; 148.8MB allocated; 800/820 visible renderers; direct budget validation passed.
- `pytest tools/tests/test_validate_khufu_v7_entry_wayfinding.py`: 6/6 passed.
- Pre-Fable aggregate validation: passed with 14/14 frozen hashes and artifact digest
  `28dae0b2719172ad7312536149017d1f71230e55ae4dbb57a17cc95029716246`.
- Repo has many unrelated pre-existing changes; Codex will stage an explicit V7 whitelist only and rerun
  the aggregate validator with `--staged`.

Known gaps/non-goals:
- This slice does not replace production art, lighting, VFX/audio, or full-map visual polish.
- It is a fictional game map, not an authentic reconstruction of unknown pyramid interiors.
- Unity MCP registration and NotebookLM were not required for this final implementation evidence; no
  result from either is claimed.

Ask:
1. List blocking findings with a source/evidence reference.
2. List only concrete non-blocking risk reductions.
3. Assess the exact-pylon renderer-disable restoration, V7 look-ahead API scope, visual proof predicate,
   and scene/build binding.
4. End with exactly one standalone verdict line and do not repeat the verdict token elsewhere:
   FINAL_REVIEW: ship
   or use `revise` / `investigate` when warranted.
