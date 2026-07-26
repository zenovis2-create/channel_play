## Blocking findings

**B1 — The release's own terminal gate cannot pass, and the artifact it reads is staged for commit.**

`tools/validate_khufu_v11_release.py:24` binds `FABLE_FINAL = work/fable-harness/khufu-v11-release-final-review.opus.md`, and `validate()` under `--require-reviews` requires `fable_verdict(...) == "ship"` (`tools/validate_khufu_v11_release.py:366-368`). That file currently contains, in full:

```
FABLE_HARNESS_ERROR: Claude Code CLI exited with code 1.
STDOUT:
Error: Exceeded USD budget (2)
```

`fable_verdict` returns `None` on `FABLE_HARNESS_ERROR` (`:135-137`), so the review gate fails closed — correctly. But that path is allowlist entry 96 (`docs/khufu-v11-royal-circuit/staging-allowlist.txt:96`), it exists, and `check_staged` requires every dirty allowlisted path to be staged (`:243-244`). With `staged_files: 92` reported as passing, this file is in the staged index. Committing now bakes a release artifact whose content records a harness budget failure into the SHA-bound inventory.

**B2 — The receipt that will be committed asserts the review chain was not checked.**

`runs/khufu-v11-royal-circuit/release-validation.md:4-6` records `Reviews required: False`, `Staged index checked: False`, `Post-commit checked: False`. `runs/khufu-v11-royal-circuit/review-resolution.md` (allowlist entry 81, required at `:312` and `:369-371`) does not exist on disk. So the only release receipt in the inventory is the weakest of the three modes, and the decision-pack claim "release gate passed" is true only for the `--check-staged` run (`staged-index-validation.md:4` also shows `Reviews required: False`). No execution of the gate has ever verified the review contract.

These are procedural rather than engineering defects — this review is the input that closes them — but they are the direct answer to "safe to commit?": not as currently staged.

## Non-blocking findings (verified, worth recording)

**N1 — V10 delta classifier is prefix-loose on two unbounded message families.** `ChannelPlayKhufuV11LegacyRegression.cs:130-134` accepts `Unexpected V10 root metrics:` and `Unexpected full-map V10 metrics:` by prefix, so any numeric value satisfies them; likewise `V10 mesh topology drifted: …`. The count-13 + bidirectional-set constraint bounds the *shape* of the delta, not its magnitude. This is adequately compensated: `ChannelPlayKhufuV11RoyalCircuitValidator.cs:310-313` binds both V10 filters to the exact generated open assets, and `ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ValidateV10TransitionAssets()` (`:141-151`) rebuilds the open variants from V10's own spec pipeline, compares full `GeometrySignature`, and pins the four frozen closed-source SHA256s (`:36-43`). Not a real hole, but the classifier alone would not catch it.

**N2 — Map-level metrics are ceilings, not equalities.** `performance-budget.json` gives `map.renderers_max: 829` / `colliders_max: 600`, checked with `>` (`Validator.cs:279-281`). Observed map is `829 / … / 567` (`validation.md:5`). A regression that *removes* map renderers is caught by nothing. Also note headroom is zero at the map level too, not only at the V11 root — residual risk 1 understates this slightly.

**N3 — The boundary control's collider attribution is inferred, and the stop is a depenetration, not a walk-into-wall.** `v11-final-boundary-control.md:14` shows `Named boundary contact proof: actual-controller capsule overlap before Move`, which means the promotion branch at `KhufuV11TraversalProofProbe.cs:278-284` fired — Unity recorded no hit name for that `Move`, and the name came from `BoundaryContact`'s `OverlapCapsule` (`:320-322`). The numbers confirm this: traversed 0.635 m against a 0.20 m step target with error 0.681 m, `records 1`, i.e. the controller began inside the enabled blocker and was ejected. The promotion is properly fenced (boundary mode only, same `Move` returned `Sides`, exact collider identity), and the control still falsifies the normal run (1/15 vs 15/15). But the pack's phrasing "stopped 1/15 at exact named blocker" is stronger than what was observed. Strengthening this would mean starting the boundary run one anchor short of the blocker so the stop is a genuine forward `Sides` collision with a callback-recorded name.

**N4 — Minor.** `BUILD_ROOT = Path("Builds/KhufuV11")` (`:16`) vs on-disk `builds/KhufuV11` — works only because Windows is case-insensitive; the gate is not runnable on a case-sensitive host, nor on a fresh clone (`[Bb]uilds/` is gitignored, `.gitignore:14`). Consistent with residual risk 4, but it means `release-validation.md` is not independently reproducible post-clone. `status_paths` (`:177-189`) also mis-parses rename records, which could mask a path.

## What closes B1/B2

1. Write this review's verdict into `work/fable-harness/khufu-v11-release-final-review.opus.md` as the final nonblank line, with no second `verdict:` line anywhere in the file (`:138-142`).
2. Create `runs/khufu-v11-royal-circuit/review-resolution.md` carrying `V11_REVIEW_RESOLUTION: passed`.
3. Re-run with `--require-reviews` to `release-validation.md`, stage it, then `--refresh-staged-inventory --require-reviews --check-staged` to `staged-index-validation.md`, stage the two helpers, and re-run once more to confirm byte-stable convergence (the count moves off 92; `staged ∩ unstaged` at `:250-252` will flag any non-converged pass).
4. Commit, then `--postcommit` to `post-commit-validation.md`.

Everything else I checked holds: scene SHA `dbc0c5e3…97b` is consistent across `validation.md`, `idempotence.md`, `clean-package-import.md` and `captures/manifest.md`; `5/2016/1008/33` matches the probe's runtime assertions `v11Colliders == 33 && v11Renderers == 5` (`:173`, `:177`); six capture SHA256s are distinct; both player receipts carry assembly `a8bbffb0…bc7`; idempotence and the five negative controls plus rollback are recorded. I made no changes to the repository.

VERDICT: revise

