# Task 0011 Verification

Checked: 2026-07-26

Result: **PASS (packet only)**

## Checks

- `python -m pytest tools/tests tools/studio`
  - Result: 299 passed.
- `python -m pytest tools/studio/company/tests/test_asset_gate.py`
  - Result: 15 passed.
- `python tools/channelctl asset gate-a-check truth_pen`
  - Result: expected exit `1`.
  - Gate A remains `FAIL`; the first blockers are missing
    `applicable_jurisdiction`, `provider_or_source`, and
    `creator_or_affirmer`.
- `git diff --check`
  - Result: passed.

## Scope Decision

The repository now records `commissioned_human` as the procurement path and
provides an evidence intake packet. This verification does not approve source
creation, asset production, or Unity import. No external rights fact was
asserted.

## Remaining Gate

A named creator, signed rights instrument, jurisdiction, input-clearance
evidence, rights findings, and structured critic approval bound to the final
manifest SHA-256 are still required.
