# Khufu V10 External Fable Final Review

- First final-review verdict: `revise`.
- First blocking finding: the dirty worktree did not yet have an exact staged-path manifest.
- First blocking finding: Windows traversal and performance evidence was not yet explicitly bound to the final scene and build.
- Resolution: a 163-path dependency-closed allowlist and fail-closed staged-index validator now constrain the release commit.
- Resolution: editor, Windows player, and performance bindings cover the final scene, Assembly-CSharp, evidence artifacts, and all 269 runtime files by size and SHA256.
- Re-review verdict: `ship`.
- Re-review blocking findings: none.
- Independent code/gate reviews then found omitted V10 materials, seven omitted V4 scene dependencies,
  incomplete source bindings, and an inexact post-commit check.
- Corrections: material and legacy GUID closure, dual working/index binding schemas v2, deterministic
  staged inventory, exact nonempty HEAD matching, 13 adversarial release tests, and an isolated
  872-file Unity clean-index pass.
- Final Fable re-review after those corrections: `ship`; blocking findings: none.
- Reproducibility check: `ChannelPlayKhufuV10WindowsBuild` supplies
  `ChannelPlayKhufuV10InteriorBuilder.ScenePath` directly to `BuildPlayerOptions.scenes`, so the V10 build does not depend on the excluded `EditorBuildSettings.asset`.

The external review still requires the release validator to run against the live staged index. That
condition is enforced during exact staging and is not replaced by this receipt.

V10_EXTERNAL_FABLE_REVIEW: addressed
