# Session Summary

Session ID: 20260727-164826-help
Ended: 2026-07-27T17:07:12+09:00
Status: complete

## Changes

- Closed `task-0027`.
- Added a cryptographically keyed, value-redacted, five-minute in-memory apply
  result store capped at 64 attempts.
- Added a protected exact-schema apply-status endpoint.
- Added one-shot browser recovery after an ambiguous primary response without
  any automatic save retry.
- Added store, API, UI contract tests and owner-intake documentation.

## Evidence

- `runs/task-0027-procurement-apply-recovery/runtime_status.md`
- Focused suite: `75 passed, 15 subtests passed`
- Full suite: `356 passed, 33 subtests passed`
- Chrome 150: one preview, zero apply, zero apply-status
- Real manifest and existing FAIL receipt hashes unchanged
- `memory/company/reviews/task-0027-review.md`: no P1/P2/P3 finding
- Verification status: passed

## Next Actions

- Merge the scoped branch after CI/review.
- Keep artist contact blocked until a separate current procurement check
  produces a matching `PASS` receipt.
- On expired, evicted, restarted, pending, or mismatched recovery state, inspect
  the manifest diff and do not retry the save.
