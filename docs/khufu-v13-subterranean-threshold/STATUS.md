# Khufu V13 Subterranean Threshold Status

## Current State

- Phase: final release validation and exact-index handoff.
- Baseline commit: `787476b58044e78f0c5164df408680e50fee47a2`.
- Baseline scene SHA256: `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`.
- Accepted V12 signature: `6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd`.
- Frozen V12 map metrics: 834 renderers, 67,070 vertices, 48,560 triangles, 589 colliders.
- Planned V13 budget: exactly five renderers and 20 colliders; final map totals 839 and 609.
- Frozen ownership: 13 V4 targets, including 12 renderer/collider pairs and one renderer-only pit.
- Canonical V13 static signature:
  `39b768e4885d8c9a6b7048786287ecd135492fa90bddd3e25a37ee32ed16493f`.
- Unity root metrics: 5 renderers, 792 vertices, 396 triangles, 20 colliders.
- Full-map metrics: 839 renderers, 67,862 vertices, 48,956 triangles, 609 colliders.
- V4-V12 regression, rollback controls, idempotence, and clean-import reproduction:
  passed.

## Next Gate

Regenerate final Windows build, built-player traversal receipts, and six bound captures from the
committed implementation. Then run the Python release validator against the exact staged index
and verify the committed bytes.

## Remaining Work

Finalize evidence receipts, resolve independent reviewer findings, validate the exact staged
inventory, commit only allowlisted paths, and complete post-commit verification.
