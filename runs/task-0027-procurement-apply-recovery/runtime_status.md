# Task 0027 Runtime Status

Date: 2026-07-27 (Asia/Seoul)
Branch: `codex/procurement-apply-recovery`
Result: **PASS**

## Automated Evidence

- Focused procurement, API, and Studio contract suite:
  `75 passed, 15 subtests passed`
- Full Python suite:
  `356 passed, 33 subtests passed`
- JavaScript syntax:
  `node --check tools/studio/app/app.js` passed
- Python syntax:
  `python -m py_compile tools/studio/workspace_server.py` passed
- Diff hygiene:
  `git diff --check` passed

The tests cover strict 128-bit apply-attempt IDs, duplicate reservation,
pending/completed/expired states, five-minute TTL, 64-result capacity, asset
binding, value allowlisting, defensive copies, unsafe-result rejection, common
execution gates, exact status request fields, body-size limits, primary apply
integration, and no value echo. The UI contract proves cryptographic ID
generation, one apply call site, recovery-only status lookup, existing
preview-bound verification, no automatic write retry, no browser storage, and
text-only result rendering.

## Chrome Safety Proof

Chrome `150.0.7871.129` opened loopback Studio on port `8773`. A complete
repository-safe 16-field sample was submitted to preview only; the save button
was never clicked.

- Preview result: valid, `16` changed, `0` unchanged
- Network: one `/api/procurement/preview`
- Network: zero `/api/procurement/apply`
- Network: zero `/api/procurement/apply-status`
- Post-save verification panel: hidden and empty
- Browser local/session storage: empty

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

No owner value, manifest, receipt, or contact authorization state changed.
Recovery records remain process-local, value-redacted, bounded to 64 entries,
and expire after five minutes. Restart, expiry, eviction, or a point-in-time
post-write mismatch still requires manual manifest diff inspection without a
retry.
