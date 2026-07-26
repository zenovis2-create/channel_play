# Status

- Current decision: V6 implementation, deterministic verification, and external Fable final review
  pass. The remaining action is a scoped commit with staged-index verification.
- Current phase: scoped staging and commit.
- Next action: stage the explicit V6 whitelist, verify the staged scene and frozen inputs, commit.
- Current blocker: Unity MCP Editor registration and NotebookLM authentication are unavailable, but
  neither blocks the batch/player acceptance surface.
- Current proof: `runs/khufu-v6-visual-slice/`.

## Completed

- [x] Frozen nine forbidden inputs before implementation.
- [x] Added seven deterministic Standard materials and four albedo/normal texture pairs.
- [x] Added the bounded Temple Hub colonnade and reassigned V4/V5 surface materials.
- [x] Passed V6 static validation and rebuild idempotence.
- [x] Refreshed all four captures against scene SHA256
  `09c8083647f1476e72acd3c0176496e3b6a2742a66e6c5e39ee5fa7df66bb95b`.
- [x] Passed fresh V5 Gate 4 and PlayMode regression against the same scene.
- [x] Built the Windows player with 0 errors and restored `ProjectSettings.asset` byte-for-byte.
- [x] Passed visible-player performance: frame p95 8.340 ms, main thread p95 2.572 ms,
  render thread p95 2.941 ms, GPU p95 2.383 ms.
- [x] Passed all ten aggregate-validator unit and mutation tests.
- [x] Bound performance evidence to the final scene, player executable, built level, raw profile,
  player log, validator receipt, and both player screenshots.
- [x] Verified all generated texture/material `.meta` files and material-to-texture GUID references.
- [x] External Fable final review returned exactly one `FABLE_VERDICT: ship` marker.
- [x] Final aggregate validation passed.

## Unresolved

- [ ] Unity MCP server starts on port 8090, but the Unity package does not register the Editor.
- [ ] NotebookLM requires a fresh local `nlm login` before it can contribute research evidence.

## Outside V6 Scope

- Full-map final art, authored hero meshes, baked lighting, VFX, audio, and production optimization.
- Archaeological reconstruction of unknown or destroyed pyramid-temple interiors.
- Repairing third-party Sentis shader warnings emitted by `com.unity.ai.inference`.
