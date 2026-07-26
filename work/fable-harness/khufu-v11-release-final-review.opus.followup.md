## Khufu V11 — Follow-Up Resolution Review

I re-read the primary artifacts rather than accepting the resolution's self-report. Findings below are indexed to the first-round review.

### B1 — closed

`tools/validate_khufu_v11_release.py:24` now binds `FABLE_FINAL = work/fable-harness/khufu-v11-release-final-review.opus.followup.md`, a distinct path from the first-round file. The budget failure is preserved verbatim at `khufu-v11-release-final-review.opus.budget-failure.md` (allowlist `:100`), and `khufu-v11-release-final-review.opus.md` still holds the unmodified first-round review ending in a revise verdict (allowlist `:98`). Both are inventory provenance only; neither is read by the gate.

The fail-closed logic is unweakened: `fable_verdict` (`:135-142`) still returns `None` on the harness-error sentinel, on any count other than exactly one verdict line, and when that line is not the last nonblank line. Two tests pin all three branches (`test_validate_khufu_v11_release.py:57-64`).

### B2 — closed as far as it can be pre-commit

`runs/khufu-v11-royal-circuit/review-resolution.md` exists, carries `V11_REVIEW_RESOLUTION: passed`, is allowlist entry `:81`, and is required under `--require-reviews` at `:327` and `:384-386`.

Both existing receipts still record `Reviews required: False` (`release-validation.md:4`, `staged-index-validation.md:4`). That is correct for pre-resolution artifacts and is exactly what the two follow-up runs replace. The gate cannot be bypassed here: `check_staged` requires every dirty allowlisted path to be staged (`:258-259`), requires staged blob bytes to match the inventory (`:238-244`, `:270-273`), and rejects any `staged ∩ unstaged` path (`:265-267`). Since `tools/validate_khufu_v11_release.py` and `test_validate_khufu_v11_release.py` were edited after being staged (their old blobs are still in `staged-inventory.json:390,400`), a commit without re-staging and refreshing fails closed. B2's closure is therefore conditional on both runs passing, which is the stated precondition for commit.

### N1 / N2 / N4 — classification accurate

- **N1 rejection is consistent** with the first review's own wording ("Not a real hole"). The exact-signature and frozen-SHA256 bindings it relies on are the ones the original reviewer verified.
- **N2 adopted**: `STATUS.md:26-27` states both `5/5` and `829/829` have no renderer headroom, matching `validation.md:4-5`.
- **N4 rename fix is correct.** `parse_status_paths` (`:177-192`) consumes the second NUL field on `R`/`C` records and retains both paths, which matches porcelain `-z` (new path first, original second) and prevents the old corruption where `scope/original.cs` was misread as status `sc` + path `pe/original.cs`. `test_status_paths_preserves_both_sides_of_rename_records` (`:89-101`) fails against the old code. Test count reconciles: 9 prewrite + 10 release = the recorded `19 passed`.
- **N4 build-case rejection is supported.** `ChannelPlayKhufuV11WindowsBuild.cs:12` is `Builds/KhufuV11/ChannelPlayKhufuV11.exe` and `release.py:16` is `Builds/KhufuV11`. Independent-clone regeneration remains a stated residual risk.

### One check the resolution did not claim, which I verified

The resolution edited two Python files that are inside `SOURCE_FILES`. Neither is hash-bound by an existing receipt: `windows-build.md` binds `SOURCE_FILES[:10]` (`:364`) and the capture manifest binds `SOURCE_FILES[:5]` (`:345`), both ending before the tools entries at indices 11 and 13. So no prior hash binding was silently invalidated, and the claim that existing Unity-side evidence remains applicable holds.

### Residual notes (not blocking)

1. `STATUS.md:20` still reads "stops at 1/15 on the named Great Step collider with `Sides`" without the depenetration qualifier. Literally true, and the qualifier now appears in both `manual-qa.md:26-31` and the receipt itself (`v11-final-boundary-control.md:14`), so the evidence chain is honest; the summary line is merely compressed. Worth aligning opportunistically.
2. `khufu-v11-release-final-review.followup.dry-run.txt:10` names a different output file than `FABLE_FINAL`. If the live call writes to the dry-run name, the gate fails closed on a missing required file — a re-run, not a correctness risk.
3. Convergence still requires the documented third pass: `staged-index-validation.md` is written after `validate()`, so the first `--check-staged` run necessarily dirties a staged helper. Re-stage and re-run until byte-stable; `:265-267` flags a non-converged pass.

The blockers were procedural, this output is their designated input, and the non-blocking findings are classified accurately with adopted items landed in the artifacts named. Residual risks (zero renderer headroom at both levels, V10's intentionally unsatisfiable closed Great Step contract, the controlled cutaway, and ignored build outputs) are recorded rather than hidden. Release may proceed to the review-required staged gate; commit remains gated on both runs passing.

I made no repository changes.

VERDICT: ship

