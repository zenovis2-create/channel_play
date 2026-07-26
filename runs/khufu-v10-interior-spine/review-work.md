# Khufu V10 Review Work

## Initial Findings

- External Fable initially required an exact staging manifest and explicit final-scene runtime binding.
- The first independent code and gate reviews rejected the candidate because six scene-referenced V10
  materials and metadata were omitted, source/assets were not bound to staged bytes, post-commit
  validation accepted incomplete commits, and receipt vocabulary violated the truth contract.
- Clean-index validation then exposed seven older V4 mesh dependencies referenced by the final scene
  and raw-hash instability under Windows line-ending conversion.
- The first independent re-review found six preserved Fable planning sidecars caught by an overly
  broad strict prefix.

## Corrections

- Expanded the unique allowlist to 163 paths and added every V10 material plus seven directly
  referenced V4 mesh assets with all required metadata.
- Added GUID closure checks and verified that every non-built-in final-scene GUID resolves locally.
- Added LF checkout rules for Unity `.asset`, `.mat`, `.meta`, and `.unity` files.
- Advanced all bindings to v2 with 65 working-file and 65 Git-index release-input records; player and
  performance bindings retain all 269 runtime files.
- Added deterministic staged-inventory records, exact nonempty HEAD matching, worktree-drift checks,
  per-blob rechecks, and staged-receipt scene/Assembly/pass-token verification.
- Added adversarial tests for dependency binding, staged source mutation, empty/subset/extra commits,
  and post-commit drift. The full focused suite passes 23 tests.
- Ran an isolated 872-file Unity import from the staged index. It imports all V10 material GUIDs,
  passes all static/idempotence/mutation gates, and ends at the bound scene SHA256.
- Narrowed strict Fable scope to the four release-relevant evidence stems while preserving six
  planning sidecars outside the release.

## Programming Review

- Current code reviewer result: `CLEAR`; recommendation: `APPROVE`; blockers: none.
- Binding, staged-index, post-commit, GUID, and line-ending boundaries have behavior-level tests.
- Aggregate output no longer presents hardcoded geometry expectations as observed facts.
- Large validator and Unity modules remain maintenance debt but do not violate this bounded contract.

## Overfit And Slop Review

- No deletion-only, tautological, or implementation-mirroring release test remains in the corrected
  gate set.
- Mutation tests operate on real temporary Git repositories and induce actual index/commit drift.
- Generated evidence whitespace and the disclosed blockout visual density are nonblocking artifacts,
  not hidden pass conditions.

## Final Independent Decisions

- `Code Reviewer the 4th`: `APPROVE`; zero remaining findings.
- `Gate Reviewer the 4th`: `APPROVE`; sole strict-sidecar blocker cleared.
- External Fable final re-review: `VERDICT: ship`; blocking findings: none.
- Local Fable decision: ship only through exact staged and post-commit gates.

## Residual Risks

- The baseline package manifest has a pre-existing normal-import issue in Unity 6000.0.76f1; clean
  V10 validation therefore uses the supported `-noUpm` option and package changes stay out of scope.
- `V10_Route_Amber.mat` reserializes differently in the isolated no-UPM rebuild; the non-frozen
  diagnostic signature differs, while frozen V8/V9 gates and final scene bytes match.
- Enclosure minimum `0.792` is above the frozen `0.750` threshold but should be revalidated after any
  geometry change.
- Production chamber art, global lighting, VFX, audio, and fresh-player usability remain deferred.

V10_REVIEW_WORK: passed
