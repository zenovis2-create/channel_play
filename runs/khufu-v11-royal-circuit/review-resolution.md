# Khufu V11 Opus Review Resolution

First-round review: `work/fable-harness/khufu-v11-release-final-review.opus.md`.
Follow-up review: `work/fable-harness/khufu-v11-release-final-review.opus.followup.md`
(`VERDICT: ship`).

## Blocking Findings

- **B1 — adopted.** The failed budget output is preserved as
  `khufu-v11-release-final-review.opus.budget-failure.md`, and the successful first-round `revise`
  review remains unchanged. A separate follow-up Opus output is the release gate input and must end
  in exactly one `VERDICT: ship` before the release may proceed.
- **B2 — adopted.** This resolution receipt now exists. After a ship verdict, both the normal
  release receipt and exact-index receipt will be regenerated with `--require-reviews`; commit is
  prohibited until both pass.

## Non-Blocking Findings

- **N1 — rejected as a release blocker.** The prefix classifier only identifies the exact
  13-message V10 successor delta set. Exact open-mesh geometry signatures, frozen closed-source
  SHA256 values, and V11 binding checks independently constrain the numeric geometry.
- **N2 — adopted.** `STATUS.md` now records that both V11 root (`5/5`) and full-map (`829/829`)
  renderer budgets have zero headroom. The ceilings remain performance budgets; exact scene,
  static-signature, idempotence, and staged-blob hashes bind this release.
- **N3 — adopted.** `manual-qa.md` now states that the boundary control begins overlapped and proves
  route falsification by depenetration plus `Sides`, not a forward walk-into-wall callback.
- **N4 — partially adopted.** `status_paths` now parses Git porcelain rename/copy records and keeps
  both paths; a focused regression test passes. The build-path case concern is rejected:
  `ChannelPlayKhufuV11WindowsBuild.OutputPath` and Python `BUILD_ROOT` both use
  `Builds/KhufuV11`; the lowercase display is an existing Windows directory name, not the
  case-sensitive fresh-build contract. Build products remain intentionally ignored prerequisites.

## Verification After Resolution

- `python -m pytest tools/tests/test_validate_khufu_v11_prewrite.py tools/tests/test_validate_khufu_v11_release.py -q`
  — `19 passed in 1.72s`.
- No Unity runtime or generated-scene source changed, so the previously recorded build, traversal,
  capture, static-validation, and clean-import evidence remains applicable.

V11_REVIEW_RESOLUTION: passed
