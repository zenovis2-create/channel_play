# Task 0013 Verification

Checked: 2026-07-26

Result: **PASS**

## Checks

- `python -m pytest tools/studio/company/tests/test_asset_gate.py tools/studio/company/tests/test_assets.py -q`
  - Result: 17 passed and 3 subtests passed.
  - Covers LF/CRLF manifest equivalence and exact binary byte hashing.
- `python -m pytest tools/tests tools/studio`
  - Result: 300 passed in 181.06 seconds.
- `python tools/channelctl asset gate-a-check truth_pen`
  - Result: expected exit 1 with 22 unresolved requirements.
- Canonical manifest and receipt SHA-256
  - Both equal
    `0595bc27b1274e73d271b713cc50b0d3f581bdcad5d530448eeb4c810c7620f2`.
- `git diff --exit-code -- asset_pipeline/manifests/truth_pen_source_gate_a.json`
  - Result: passed; the evidence manifest was not edited.

## Safety Decision

Only UTF-8 gate-record CRLF and CR line endings are normalized to LF. Binary
source assets retain exact byte hashes, so any source-byte change still fails
the Gate B binding.

## Remaining Gate

Truth Pen Gate A remains intentionally blocked until the owner supplies real
contracting, rights, input-clearance, and critic-approval evidence.
