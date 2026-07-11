You are Claude Fable 5 acting as the plan critic in a Fable-to-Codex-to-Fable harness.
Do not implement. Findings first, under 900 tokens.

Goal:
Create a bounded Khufu V7 player-entry and wayfinding pass that removes the wall-blocked first
participant view and makes the Valley Gate -> Covered Causeway -> Temple Hub approach readable,
without changing accepted V5 topology or V6 material/geometry sources.

Completion surface:
- The rendered Windows player's first participant screenshot has an unobstructed player/route view.
- Runtime evidence records at least one occluding Valley Gate pylon cut away, with no still-visible
  cutaway candidates intersecting the camera-to-player ray.
- A deterministic V7 overlay adds a small no-collider/no-shadow floor-guide route from Valley Gate
  to Temple Hub and preserves V5/V6 signatures and frozen source hashes.
- Fresh V5 static/CharacterController regressions and the frozen Windows performance budget pass.
- Aggregate and mutation tests bind all evidence to the final scene/player hashes.

False-done conditions:
Only changing a screenshot camera, hiding all gates/doors indiscriminately, relying on colliders
that the decorative pylons do not have, stale-scene evidence, V5/V6 source drift, compile-only proof,
or claiming the route guide is archaeological reconstruction.

Decision needed:
Is this the smallest safe correction, and what exact validation or architecture change is required
before Codex edits shared camera code and adds the V7 overlay?

What would change implementation:
- If adding `pylon` to the cutaway candidate list is too broad, Codex will use a narrower marker or
  component-based candidate rule.
- If a floor-guide overlay is too much scope, Codex will ship camera-entry hardening only.
- If V6 downstream composition needs a different contract, Codex will change the V7 validator
  structure before building the scene.

Verified repo facts:
- Current accepted commit: `c7955d008bdd7fc8b64b79c9a2f23b68eb4c5375`.
- `Gameplay_PlayerSpawn_ValleyGate` is `(150, 1.2, 0)`.
- `ChannelFollowCamera` desired offset is `(0, 6, -8)` in `LateUpdate`.
- The rear Valley Gate pylon is centered at `(150, 3, -7)`, scale `(5, 6, 2)`. The desired camera
  lies on its rear Z bound and the view ray crosses it.
- The directly inspected V6 Windows screenshot is dominated by red-granite gate geometry in the
  center and lower half; the route is not readable.
- `ChannelCameraOccluderCutaway` uses renderer bounds + `forceRenderingOff`, independent of
  colliders. Its candidate list includes wall/roof/ceiling/beam/pyramid/column/pillar/lintel/tier/
  course, but not `pylon`.
- V5 decorative district pylons are deliberately built without colliders.
- Existing `ChannelPlayCameraCutawayValidator` proves hide/restore for a ceiling-beam object only.
- V6 final map metrics are 795 renderers / 23,776 vertices / 16,508 triangles / 441 colliders.
- The V6 validator assumes no downstream renderer overlay, so V7 must not claim a fresh V6
  validator pass. Instead it can freeze V6 source hashes, V6-root signature, and V6-root metrics,
  then validate V7 independently while rerunning V5 gameplay gates.

Proposed Codex plan:
1. Freeze current V5/V6 camera, scene, builder, validator, package, and quality hashes.
2. In shared `ChannelCameraOccluderCutaway`, add only `pylon` as a cutaway candidate; do not add
   generic `gate` or `door`. Extend the existing validator with pylon hide/restore coverage.
3. Add a separate V7 editor builder. It invokes the accepted V6 rebuild, creates one V7 root, reuses
   `V6_Scan_Inlay`, and adds at most 8 thin floor-guide strips along the accepted entry route.
   Budget: <=10 renderers, <=256 vertices, <=128 triangles, 0 colliders, 0 lights, 0 new materials.
4. Add a V7 validator that checks exact one-root ownership, V6 source/signature/metrics invariance,
   route-guide placement/material/shadow rules, current collider invariance, and two-run semantic
   idempotence. It supersedes rather than modifies the historical V6 validator.
5. Add a short command-line runtime entry-proof probe. In a rendered 1536x1024 D3D11 player it
   waits for the session/camera, forces cutaway refresh, records active and still-visible ray
   occluders, captures the participant view, then exits.
6. Compare the new screenshot to the frozen V6 blocked baseline with deterministic dimensions/hash/
   ROI delta, and inspect it directly. Require active cutaways >=1 and visible ray occluders ==0.
7. Run fresh V5 Gate 4 and PlayMode traversal, build a one-scene V7 Windows Development Player,
   then rerun the existing 35-second visible performance budget because cutaway scanning and scene
   renderer count changed.
8. Add aggregate/mutation tests, external Fable final review, staged-index verification, and a
   V7-only commit. Preserve unrelated dirty files.

Evidence already gathered:
- V6 Windows initial screenshot inspected directly.
- Current camera/cutaway/session/V5 builder source read.
- Official Unity 6 docs confirm `LateUpdate` as the follow-camera phase and expose world-space
  `Renderer.bounds` plus `Renderer.forceRenderingOff`, matching the current implementation.
- Unity MCP and NotebookLM remain unavailable; batch/PlayMode/player are the evidence surfaces.

Ask:
1. List blocking flaws or over-scope.
2. State the narrowest safe candidate rule for the Valley Gate pylon.
3. State the minimum tests that prove the first-view defect is fixed without V5/V6 regression.
4. End with `PLAN_VERDICT: accept` or `PLAN_VERDICT: revise` on one standalone line.
