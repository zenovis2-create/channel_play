# Khufu V12 Queen Circuit Status

## Current State

- Phase: verified release candidate; commit and post-commit gates await explicit authorization.
- Baseline: `1dd7156b064a99eaa2d19ccca0ae605befae54fd`.
- Baseline scene SHA256: `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`.
- Final scene SHA256: `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`.
- Opus plan critique: `adopt with changes`; all six blockers are incorporated into the contract.
- Opus final review: `ship`; B1 and B2 are closed, and follow-up O1/F5 are adopted.
- Strengthened Unity prewrite audit: passed; scene bytes remained unchanged.
- Focused V12 Python suite: `29 passed`.
- Full Python suite: `184 passed / 13 frozen unrelated failures / 11 subtests passed`.
- Frozen V12 component budget: 5 renderers and 22 colliders; map totals 834 and 589.
- Final geometry: 1,176 vertices / 588 triangles; static signature `6f7faced...`.
- Idempotence, nine negative/rollback cases, and original V4-V11 legacy gates: passed.
- Windows Development Player: passed with 0 errors; 185 warnings.
- Built-player round trip: 15/15 anchors, 0.050 m maximum error, 100% grounded.
- Gate control: 1.726 m outside start, empty overlap, 0.080 m steps, exact same-frame callback.
- Six final captures and manual semantic review: passed.
- `channelctl` Unity compile: 0 errors; playtest smoke: 15 checks passed.
- Clean alternate-index import: passed from 98 release paths at tree `16dcc654...`;
  static/generated/scene signatures and all six capture blobs reproduced without changing the
  main index.
- Review-required release validator: passed.
- Exact alternate staged-index gate: passed at its fixed point with 107 staged paths; the
  post-commit-only receipt is correctly excluded.

## Next Gate

After authorization, stage the exact allowlist into the main index, commit only that inventory,
then run the post-commit blob and parent check. Do not stage unrelated pre-existing worktree
changes.
