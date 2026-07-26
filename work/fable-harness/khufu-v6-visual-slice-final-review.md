You are Claude Fable 5 performing the external final gate in a Fable-to-Codex-to-Fable harness.
Findings first. Do not implement and do not praise. Keep the answer under 1000 tokens.

Goal:
Ship a bounded visual-fidelity vertical slice for the accepted Khufu V5 mega-labyrinth. Improve
Temple Hub and dense-core readability without changing verified V5 topology or claiming an
archaeological reconstruction.

Completion surface:
- Current Unity scene contains the V6 overlay and is the exact scene bound by captures, PlayMode,
  Windows build, and performance evidence.
- Nine forbidden V5/V4/package/graphics inputs retain their pre-edit SHA256 values.
- V6 stays within 12 renderers / 800 vertices / 600 triangles / 8 materials / 0 colliders.
- Rebuild semantic signature and metrics are idempotent.
- V5 Gate 4 and CharacterController PlayMode traversal pass.
- Four fixed-view captures pass integrity and the required Hub/dense-core V5 delta thresholds.
- A rendered Windows player passes the frozen V5 performance budget.
- A mutation-tested aggregate validator and this external final review both pass.

False-done conditions:
Stale screenshots, hidden/no-graphics performance, frozen-input drift, compile-only proof, treating
fictional maze art as archaeology, a forged/ambiguous Fable verdict, or unrelated dirty-worktree
changes entering the commit.

Decision needed:
Should Codex ship this V6 slice, revise a blocking issue, or investigate more?

What would change implementation:
A concrete blocker will be fixed and all affected Unity/build/player gates rerun. A non-blocking
production-art suggestion will be recorded outside this bounded slice. A ship verdict unlocks the
aggregate final receipt and scoped commit.

Risk score: 5/10
- +2 generated scene/assets and contracts across Unity Editor, scene, build, and Python validator.
- +2 more than five files and a large Unity YAML reserialization.
- +1 Windows/D3D11-specific player verification.

Repo facts and diff summary:
- Separate editor builder: `ChannelPlayKhufuV6VisualFidelityBuilder.cs`; V5 sources are untouched.
- Builder currently calls the accepted V5 rebuild, deletes/recreates only the V6 root, generates
  four deterministic 512px albedo/normal pairs and seven Standard materials, reassigns surfaces,
  and adds a no-collider/no-shadow colonnade.
- Added metrics: 11 renderers, 520 vertices, 404 triangles, 0 colliders; 7 materials.
- Added V6 validator, capture exporter, PlayMode batch runner, and one-scene Windows build entrypoint.
- Windows build enables frame timing only during build and verifies `ProjectSettings.asset` raw
  SHA256 is exactly restored in `finally`.
- Added `tools/validate_khufu_v6_visual_slice.py` and 7 tests covering pass plus frozen-input,
  stale-scene, duplicate-capture, unrestored-settings, over-budget-performance, and Fable mutations.
- Added six `docs/khufu-v6-visual-slice` lifecycle documents.
- The Unity scene diff is generated and large: 25,709 insertions / 24,400 deletions. Rebuilding V5
  reassigns serialized objects/file IDs, while semantic V5 topology and V6 signatures remain stable.
- `git diff --check` reports only Unity-generated empty YAML scalar trailing spaces; changing scene
  bytes now would invalidate the bound evidence.
- Repo has many unrelated pre-existing changes. Codex will stage an explicit V6 whitelist only.

Evidence:
- Current scene SHA256: `09c8083647f1476e72acd3c0176496e3b6a2742a66e6c5e39ee5fa7df66bb95b`.
- V6 validation: passed; semantic signature
  `b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530`.
- Idempotence: two matching signatures and metrics, zero validation failures.
- Visual proof: 4 distinct 1536x1024 captures. Temple Hub global/ROI delta 0.0447/0.0491;
  dense core 0.0460/0.0494; required minima 0.018/0.020. Captures were directly inspected.
- Fresh V5 Gate 4: 6/6 permutations, 415 clearance samples, 8/8 hub proxies.
- Fresh PlayMode: 1,758.6 m, 3,533 CharacterController steps, max error 0.338 m.
- Windows Development Player: succeeded in 16.3s, 0 errors, 185 third-party Sentis shader warnings;
  scene/build-script/output hashes recorded and PlayerSettings restored byte-for-byte.
- Visible-player D3D11/Ultra 1536x1024: 3,594 samples; frame p95 8.340ms, main 2.572ms,
  render 2.941ms, GPU 2.383ms; 146.8MB allocated; 792 renderers; all frozen limits pass.
- First profiling attempt used 4,500 raw frames and failed only the 100MB artifact cap (867MB).
  Codex diagnosed it, retained the 35s gameplay sample, limited raw profiling to 30 warm-up frames,
  reran once, and passed with a 7.0MB raw artifact.
- `python -m unittest tools.tests.test_validate_khufu_v6_visual_slice -v`: 7/7 passed.
- Pre-Fable aggregate validation checks every above binding and fails only because the final Fable
  output file does not yet exist.
- Frozen input check: 9/9 hashes match.

Known gaps and non-goals:
- Unity MCP HTTP server ran, but the Unity package never registered an Editor instance after repeated
  attempts. Batch/PlayMode/player evidence replaces it; MCP remains explicitly unresolved.
- NotebookLM authentication expired; official Unity and Digital Giza research plus existing project
  research were used. No NotebookLM result is claimed.
- This is not full-map final art, authored hero meshes, baked lighting, VFX/audio, or archaeological
  reconstruction of unknown interiors.

Ask:
1. List blocking issues with file/function or evidence references.
2. List non-blocking improvements only when they reduce a concrete risk.
3. Explicitly assess whether semantic idempotence plus current-scene hash binding is sufficient
   despite the large Unity YAML reserialization.
4. End with exactly one standalone verdict line and do not quote or repeat any verdict token:
   FABLE_VERDICT: ship
   or use `revise` / `investigate` instead when warranted.
