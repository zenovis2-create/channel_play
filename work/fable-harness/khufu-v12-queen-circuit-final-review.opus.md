I verified the claims read-only against the contracts, builder source, and receipts. Every number in the summary matched (`static-validation.md`, `negative-controls.md`, both `player-proof/*.md`). Note: `Write`/`ExitPlanMode` aren't available in this context, so this review is delivered inline rather than as a plan file.

## 1. Blocking findings

**B1 — Declared release gate is unrun and untooled.** `docs/khufu-v12-queen-circuit/GOAL.md` V12-R-010 and `TEST_PLAN.md` rows "Clean index" and "Release" make clean-index import, exact allowlist, staged convergence, commit, and post-commit inventory fail-closed completion criteria. None ran. V10/V11 each shipped with `tools/validate_khufu_v1X_release.py`, `tools/tests/test_validate_khufu_v1X_release.py`, `docs/khufu-v11-royal-circuit/staging-allowlist.txt`, and `runs/khufu-v11-royal-circuit/clean-index-import-final.log`. V12 has only `tools/validate_khufu_v12_prewrite.py`. This blocks *release*, not the slice.

**B2 — Contract/code parity gap on migration inputs.** `RULES.md` (18 rules) never documents the three accepted exact-scene-hash migration states pinned at `ChannelPlayKhufuV12QueenCircuitBuilder.cs:48-53` and consumed at `:347-364`. The builder accepts input contexts the contract does not describe.

No blocking finding in geometry, ownership, rollback, or evidence. Receipts are internally consistent: `static-validation.md` (root 5/1176/588/22, map 834/67070/48560/589, `6f7faced...`, V11 restored `9994b061...`), nine negative/rollback rejections, 15/15 anchors at 0.050 m with 136/136 grounded and both mouths sealed, control at 1.726 m with empty overlap and same-frame hit on `V10_PROXY_Queen_Branch_Threshold_Queen_Ownership_Gate` (frame 1036/1036).

## 2. Is clean-index/allowlist required?

Yes — required, not optional. It is contractually declared (above) and is the only control that makes the 1,063-entry dirty worktree safe to commit against. Without it there is no defense against a sweeping `git add -A`, and no way to decide which `runs/khufu-v12-queen-circuit/` diagnostic logs (`*-v2..v5`, `captures-d3d11`, `legacy-v10-dump`) belong in the release. Mirror the V11 pair; do not invent a new mechanism.

## 3. Are exact scene-hash migrations acceptably fail-closed?

Yes. Each branch conjoins a V12-open mesh pair, a specific proxy-state fingerprint, and SHA256 equality against a pinned literal; any drift falls through to the `InvalidOperationException` at `:364`. Entry path does not weaken output: `ValidateAppliedTransitions` (`:375-393`) re-asserts every proxy disabled and the V4 blockout component-disabled regardless of route, and failure runs `snapshot.Restore()` (`:213`), which byte-restores scene plus generated/material trees and *verifies* the restore (`:867-869`). Two residuals, neither disqualifying: the three constants are unreachable once the scene sits at `eec9cc9c...`, so they are now inert accepted-input surface; and each future migration constant widens that surface, so the pattern needs a documented retirement rule.

## 4. Verdict: **revise minimally**

The engineering slice is approvable as built. Before shipping:

1. Author `docs/khufu-v12-queen-circuit/staging-allowlist.txt` + `tools/validate_khufu_v12_release.py` (+ test) mirroring V11; run clean-index import and post-commit inventory.
2. Add a RULES.md rule enumerating the three migration hashes, their fail-closed semantics, and their inert status post-`eec9cc9c...`.
3. Record the 13 Python failure IDs in the receipt so they cannot mask later regressions. 185 warnings: accept, no action.
4. Receipts pin paths under `C:/Users/User/Documents/channel play`; re-verify scene and Assembly-CSharp hashes in this checkout at staging time.

