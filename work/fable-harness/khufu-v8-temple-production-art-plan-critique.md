You are Claude Fable 5 acting as a scarce high-cost Unity architecture and game-art reviewer.
Do not implement. Critique the plan and identify risks that would change the approach. Keep the answer under 900 tokens.

Goal:
Replace the visible V5/V6 Temple Hub graybox with a bounded, performant production-art slice derived from the
existing full-environment FBX, while preserving V5-V7 route, collision, gameplay, package, and evidence contracts.

Completion surface:
A Windows player renders a readable causeway-to-court arrival; V8 adds <=12 renderers, <=120k vertices,
<=100k triangles, no colliders/lights/cameras; V5 Gate 4, 1,758.6m CharacterController traversal, V7 gates,
normal/mutation screenshots, performance, aggregate evidence, and staged-scope validation pass.

False-done condition:
The whole 2,565-renderer FBX is inserted, the route visually clips through donor walls, graybox remains dominant,
historically unsupported rooms are presented as fact, or receipts/screenshots/build hashes refer to different states.

Decision needed:
Should Codex implement the proposed selective, material-bucketed combined-mesh donor slice, and what is the
smallest correction required to make its placement, reproducibility, route readability, and negative controls robust?

What would change implementation:
Fable can choose among (A) selective combined donor meshes at the current Temple Hub, (B) whole-FBX integration,
or (C) no FBX reuse and a new procedural kit. It can tighten donor selection, placement anchors, budgets, or tests.

Repo facts:
- Accepted scene: School_MVP, SHA256 a17075bcf6b21a5231edf32bb0247e3c755925a97c39c25a12dba506e40cf029.
- Accepted V7 map: 803 renderers, 23,968 vertices, 16,604 triangles, 441 colliders.
- FBX SHA256: 234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d.
- Unity audit: 2,583 transforms, 2,565 renderers, 379,938 vertices, 333,700 triangles, 0 colliders,
  4 lights, 6 cameras; bounds 58m x 7.691m x 68m.
- Source groups: Exterior 1,506 renderers; Interior 712; Props 331; helper/review groups 16.
- Imported front marker is local +Z; rotate +90 degrees so the causeway front points world +X from hub (62,1,0).
- Existing route approaches hub along world -X, then branches north/south-west; closed donor side walls would conflict.
- V5 hub has renderers and gameplay colliders together. Renderer.enabled can be changed without deleting colliders.
- V6 owns an 11-renderer decorative colonnade, all collider-free.
- NotebookLM research used 75 sources. Supported vocabulary is east causeway, black basalt paving/threshold,
  limestone walls, 50 red-granite square pillars, painted relief fragments, and a northwest court exit.
- The intact superstructure is uncertain; source trap/burial maze and duplicate pyramid cap are excluded from V8 claims.
- Worktree contains extensive unrelated dirty files; V8 must use an explicit staging whitelist.

Current Codex plan:
1. Freeze V5-V7/package/FBX hashes and never edit frozen owners.
2. Select only front-court, facade/threshold, entrance, open hypostyle vocabulary, and front hero props.
3. Exclude source foundation, pyramid tiers/cap, side/rear enclosing walls, trap, burial, collision, markers, anchors,
   imported cameras, and imported lights.
4. Combine selected mesh subparts deterministically by production material bucket into <=12 persistent Mesh assets,
   preserving existing asset GUIDs on rebuild.
5. Place one V8 root at (62,1,0), Y +90 degrees, with explicit threshold/court/exit anchors.
6. Disable only exact V5 hub and V6 colonnade Renderer components; retain all objects/colliders/bindings.
7. Validate source selection, metrics, material buckets, anchors, disabled-renderer whitelist, frozen hashes, and idempotence.
8. Negative controls: move V8 root +5m Z; separately re-enable one exact graybox renderer. Both must fail and restore.
9. Run V5/V7 regressions, Windows player normal/mutation captures, direct image inspection, and 35-second performance.
10. Bind final evidence hashes, request Fable final review, test staged negative/positive controls, and commit only V8 files.

Evidence already gathered:
- Unity batch audit completed with exit 0 and wrote fbx-audit.md/json.
- Existing FBX front and interior screenshots were inspected; they are cohesive but procedurally block-heavy.
- Full insertion would raise renderer components from 803 to 3,368 and is rejected.
- Research confirms the donor's deep maze cannot be labeled a factual Khufu temple reconstruction.

Known gaps:
- Exact selected renderer/triangle counts are unknown until the deterministic selector runs.
- Mesh.CombineMeshes read/write behavior for this importer has not yet been exercised.
- Final participant and fixed-review framing are not yet implemented or visually inspected.

Ask:
1. Is this plan safe and efficient?
2. What hidden failure modes matter most?
3. What minimal tests or checks should Codex run?
4. Should Codex change the plan? If yes, give the smallest corrected plan.
5. End with exactly `PLAN_CRITIQUE: proceed`, `PLAN_CRITIQUE: revise`, or `PLAN_CRITIQUE: investigate`.
