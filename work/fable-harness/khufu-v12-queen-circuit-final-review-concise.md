Role: Final architecture/correctness/regression reviewer. Findings first; do not implement.

Accepted plan:
Replace only the V4 Queen passage/chamber blockout with a bounded V12 limestone slice. Preserve V10 threshold architecture, V4 marker/glow/light ownership, frozen V11-open assets, restored V11 signature, exact budgets, rollback, and original V4-V11 behavior. Contracts: `docs/khufu-v12-queen-circuit/`; adopted plan: `work/fable-harness/khufu-v12-queen-circuit-adopted-plan.md`.

Implementation:
- Five combined mesh renderers create low passage, enclosed gabled chamber, east niche, two sealed narrow mouths, and route inlay. Exact V12 metrics: 5 renderers / 1,176 vertices / 588 triangles / 22 colliders; map: 834 renderers / 589 collider components.
- Ten V4 Queen blockout renderer/collider pairs stay active but disabled. V4 marker/glow remain inherited disabled states; Queen light stays enabled/disclosed.
- V12 limestone is identical to V11-open limestone; granite removes exactly the Queen ownership gate beyond V11 Great-Step omissions. V11 assets/metas are SHA-frozen.
- V12 disables only the Queen gate, `Gallery_Floor_Ramp`, and V10 Historic Service west/east/lintel collider frame. Renderers/meshes stay. Restored V11 context re-enables them and reproduces `9994b061...`.
- Builder accepts only exact V11-open/V12-open pairs, has exact scene-hash migration exceptions for discovered collider ownership, and restores scene/assets on failure.
- Core files: `Assets/_Project/Scripts/Gameplay/KhufuV12*.cs`, `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12*.cs`, and `School_MVP.unity`.

Evidence:
- Focused Python: 10 passed.
- Unity 6000.0.76f1 static: passed, signature `6f7faced...`.
- Idempotence: two rebuilds identical.
- Eight mutations rejected plus injected-failure rollback.
- Original V4/V5/V8/V9/V10/V11 gates pass; scene bytes unchanged. V10 permits exactly 19 named successor deltas; V11 restored signature exact.
- `channelctl` compile: 0 errors; playtest: 15 checks passed.
- Windows Development Player: 0 errors / 185 warnings.
- Built-player normal: 15/15 anchors, max/final error 0.050/0.030 m, 136/136 grounded, narrow mouths sealed, no Queen gate hit.
- Boundary control: 1.726 m outside, empty pre-Move overlap, 0.080 m step, exact gate `Sides` and callback on frame 1036.
- Six unique 1600x1000 captures plus manual visual review pass.
- Receipts: `runs/khufu-v12-queen-circuit/{static-validation,idempotence,negative-controls,legacy-regression,windows-build}.md`, `player-proof/v12-final-*.md`, `captures/{manifest,manual-semantic-review}.md`.

Residuals:
- Shared worktree has 1,063 dirty entries; nothing staged/committed. Exact V12 release allowlist and clean-index dependency export are not done.
- Full Python: 165 passed / 13 failed. Three bind old V5/V6 scene/build receipts; ten are Windows/POSIX portability or macOS-tool assumptions. V12-focused suite passes.
- `runs/khufu-v12-queen-circuit/` includes final receipts and intermediate failed-iteration logs that should not enter release inventory.
- 185 build warnings were not triaged individually.

Return cited blocking findings and one verdict: ship / revise minimally / do not ship.

Decision: Must clean-index/allowlist validation be completed first? Are exact scene-hash migration exceptions acceptably fail-closed? Are any other blockers present?
