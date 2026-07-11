You are Claude Fable 5 doing a high-risk final Unity/game-art diff review.
Prioritize correctness, regressions, evidence integrity, deterministic asset generation, and false completion claims.
Do not praise. Findings first. Keep the answer under 1000 tokens.

Goal:
Replace the visible V5/V6 Temple Hub graybox with a bounded, performant production-art slice derived from the
existing pyramid-temple FBX while preserving V5-V7 route, collision, gameplay, camera, package, and evidence contracts.

Decision needed:
Ship, revise, or investigate more before Codex stages and commits the V8 scope.

Risk score and why:
5/10. Generated Unity Mesh assets and a large serialized scene are changed (+2); implementation spans more than
five files and includes a 16MB external FBX (+2); Windows/player-specific rendering and profiling add platform risk (+1).
No auth, persistence, package, ProjectSettings, dependency, or gameplay-system owner is changed.

Historical/product boundary:
NotebookLM deep research imported 75 sources. Supported vocabulary is the east-side causeway, black basalt
threshold/court, limestone walls, square red-granite pillars, painted relief fragments, and pyramid landmark.
Deep maze, trap, burial, helper, camera/light, round hypostyle-column, and duplicate pyramid-cap donor geometry is excluded.
The result is labeled a historically informed game-art interpretation inside a fictional mega-labyrinth, not a reconstruction.

Diff summary:
- New Unity FBX audit and selector/mesh-combine pipeline.
- New V8 builder, static validator, screenshot exporter, Windows build, and runtime participant proof.
- Ten persistent generated meshes: 9 selected material buckets plus one 20-pillar square red-granite mesh.
- School_MVP receives one `Runtime_Khufu_V8_Temple_Hub_Art` root at (56,1,0), Y+90.
- Exactly 5 V5 hub and 11 V6 colonnade renderers are disabled; objects/colliders/bindings remain.
- New GOAL/PLAN/STATUS/RULES/TEST/research/performance docs and Python aggregate validator with five focused tests.
- Source FBX binary/meta are frozen at 16,090,700 bytes and explicit SHA256 values.
- Existing V5/V6/V7/package files are hash-checked and unedited. The worktree contains unrelated dirty files that will
  be excluded through an explicit staging whitelist and negative control.

Important implementation facts:
- Full FBX audit: 2,565 renderers, 379,938 vertices, 333,700 triangles, 4 lights, 6 cameras.
- Selector contract: exactly 245 source renderers -> 9 buckets, 32,110 vertices, 26,460 triangles, zero forbidden matches.
- Final V8 root: exactly 10 renderers, 33,550 vertices, 27,180 triangles, 0 colliders/lights/cameras.
- Final map: 813 renderer components, 57,518 vertices, 43,784 triangles, 441 colliders.
- Generated assets preserve GUIDs with CopySerialized; two rebuild signatures and all 10 asset hashes match.
- Route-clearance sweep covers selected donor structures and every authored pillar. A local (0,0,2) pillar mutation fails.
- Placement +5m Z and re-enabled graybox mutations also fail and restore without saving.
- Frozen V6 and V7 root metrics/signatures are checked inside the final expanded scene.

Focused code excerpts:
```text
IsSelectedRendererName:
  rejects Collision, Gameplay_, Lighting_, Camera_, Pyramid_, Trap_, Burial_, rear/side/service rooms,
  main door shadow, podium/stairs, and round/central hypostyle columns;
  accepts only exact front court/hall/aisle plus facade/entrance/front-wall/relief/seam prefixes.

Builder:
  V7.Rebuild(); assert frozen baseline 803 renderers/441 colliders;
  combine and save 9 donor buckets; add one authored pillar mesh;
  assert V8 <= 10 renderers/40k vertices/32k triangles/0 colliders;
  disable exact V5=5 and V6=11 renderer arrays; save scene.

Route gate:
  sample world X 48..78 every 0.5m with a 0.5 x 2.2 x 1.8m corridor;
  reject structural renderer/pillar Bounds intersections; floors/aisle/seams are allowed surfaces.
```

Validation run:
- Unity source audit and Read/Write-disabled CombineMeshes spike: passed; FBX and meta unchanged byte-for-byte.
- Fable corrected plan review: `PLAN_CRITIQUE: proceed`.
- V8 static validation, camera cutaway synthetic, idempotence, placement/graybox/pillar mutations: passed.
- V5 Gate 4: 6/6 objectives, 415 clearance samples, 8/8 hub proxies, critical route 898.6m: passed.
- Final-scene PlayMode CharacterController: 1,758.6m, 3,533 steps, max error 0.338m: passed.
- Fixed D3D11 editor captures: 4 normal + 1 graybox mutation, 1536x1024; directly inspected.
- Windows Development Player: passed, 0 errors; 185 warnings are package-owned Sentis shader warnings.
- Windows participant proof: player in frame, all 10 V8 centers in frame, graybox=0: passed.
- Windows graybox mutation: 16 graybox renderers, proof failed as expected: passed.
- 35-second final player profile: 3,587 samples; frame/main/render/GPU p95 8.338/3.126/3.569/3.556ms;
  152.9MB allocated, 794 visible renderers, 57,332 vertices, 44,104 triangles: passed budget.
- Python performance validator: passed. Aggregate bindings to final scene `4f15673e...`: passed.
- Focused pytest: 5 passed.

Visual inspection:
The participant view has a clear center causeway into the basalt court, limestone entrance frame, red square pillar
rhythm, relief accents, and the existing pyramid as macro landmark. The mutation visibly restores a broad brown
graybox lintel and columns. The broader V5 map remains stylized/procedural; V8 is intentionally one production-art
vertical slice and is not claimed as a complete final-art pass.

Known gaps:
- No fresh external human playtester; navigation evidence is automated CharacterController plus direct screenshot inspection.
- The source donor is procedural and the wider map still needs later full-art, baked-lighting, VFX/audio, and LOD passes.
- An initial `Camera.Render` attempt with `-nographics` crashed in Unity shadow rendering; the documented D3D11 rendered
  path succeeded. The crash log is excluded from final acceptance and the final capture path is fixed to D3D11.
- Staged-scope negative/positive controls and scoped commit intentionally occur only after this review.

Ask:
1. List blocking issues with file/function references.
2. List non-blocking improvements only if they reduce real risk.
3. Say ship, revise, or investigate more.
4. End with exactly `FINAL_REVIEW: ship`, `FINAL_REVIEW: revise`, or `FINAL_REVIEW: investigate`.
