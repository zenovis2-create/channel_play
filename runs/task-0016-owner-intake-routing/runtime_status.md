# Task 0016 Owner Intake Routing Verification

Checked: 2026-07-26T23:30:58+09:00
Scope: Production Cockpit next-best-action and Studio artifact routing

## Current Procurement State

- Asset: `truth_pen`
- Decision SHA-256:
  `ebd90c2d28c3bc2e7b763b323ba5da71a3067fcd51a8612facfff451bdff9a2f`
- Receipt result: `FAIL`
- Unresolved owner decisions: `16`
- Artist contact: blocked
- Owner values changed: none

## Routing Contract

- Missing, stale, or mismatched receipt:
  `asset.procurementCheck {"assetId": "truth_pen"}`.
- Current matching FAIL receipt:
  `docs/research/truth_pen_owner_decision_intake.md`.
- Current matching FAIL receipt with a missing intake guide: explicit blocked
  action; procurement does not fall through to asset or server work.
- Ready decision without a current PASS receipt:
  `asset.procurementCheck {"assetId": "truth_pen"}`.
- Current matching PASS receipt: procurement routing may advance.

The Studio artifact action opens the tracked guide through the existing
repository file viewer. It does not execute a mutation or contact an artist.

With the verified task queue closed, `python tools/channelctl game status`
reported:

- Next action: `Complete artist procurement owner decisions`
- Target: `docs/research/truth_pen_owner_decision_intake.md`
- Work queue actionability: passed for the tracked intake artifact
- Artist procurement gate: pending

## Verification

- Focused tests: `50 passed`.
- Full Python suite: `319 passed, 29 subtests passed`.
- `node --check tools/studio/app/app.js`: passed.
- `git diff --check`: passed.
