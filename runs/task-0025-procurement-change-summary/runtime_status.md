# Task 0025 Runtime Status

Date: 2026-07-27 (Asia/Seoul)
Branch: `codex/procurement-change-summary`
Result: **PASS**

## Automated Evidence

- Focused procurement, API, and Studio contract suite:
  `71 passed, 15 subtests passed`
- Full Python suite:
  `352 passed, 33 subtests passed`
- JavaScript syntax:
  `node --check tools/studio/app/app.js` passed
- Diff hygiene:
  `git diff --check` passed

## Chrome Safety Proof

Chrome `150.0.7871.129` opened the loopback Studio on port `8771`.
A complete repository-safe sample was submitted to preview only; the save
button was never clicked.

- Preview HTTP status: `200`
- Preview result: valid, `16` changed, `0` unchanged
- Protected state: preserved
- Result and apply-panel summaries listed only the 16 canonical field names
- Response and both summaries contained none of the submitted sample values
- Instrumented pass: one `/api/procurement/preview`, one `/api/state`, zero
  `/api/procurement/apply` requests
- Browser storage contained only `channelPlayStudioView=system`; no grant or
  answer data was stored

## Repository State

The real owner manifest and existing FAIL receipt were unchanged before and
after Chrome verification.

- Manifest Git blob:
  `d39ff48880956e10e67b75dc741d7cff1e42fa9b`
- Manifest SHA-256:
  `0367a1ef176c51c76f7dcb7f2a966563bb1b9736dfd1633d4a7bdb21f7fd1648`
- Receipt Git blob:
  `c2e6f5e710493fc7c2e0ed3468e8472194ef62ec`
- Receipt SHA-256:
  `e0134652d096a0d29ecb4497beec15717e66501c7d78a5db75207af892af5faa`

Artist contact remains blocked. No owner value, manifest, receipt, or contact
authorization state was changed.
