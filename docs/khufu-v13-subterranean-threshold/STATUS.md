# Khufu V13 Subterranean Threshold Status

## Current State

- Phase: Phase 1 contract and Python prewrite gate.
- Baseline commit: `787476b58044e78f0c5164df408680e50fee47a2`.
- Baseline scene SHA256: `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`.
- Accepted V12 signature: `6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd`.
- Frozen V12 map metrics: 834 renderers, 67,070 vertices, 48,560 triangles, 589 colliders.
- Planned V13 budget: exactly five renderers and 20 colliders; final map totals 839 and 609.
- Frozen ownership: 13 V4 targets, including 12 renderer/collider pairs and one renderer-only pit.
- Unity scene/assets: unchanged in Phase 1.

## Next Gate

Create a read-only Unity prewrite audit that binds the canonical scene bytes, exact target
component states, target transforms, marker/glow ownership, inherited light, V10 anchor, V12
signature, and component metrics. Run the Python prewrite validator before authorizing the first
scene or generated-asset write.

## Remaining Work

Implement the deterministic mesh pipeline, builder, static validator, idempotence and negative
controls, rollback, V4-V12 legacy runner, built-player traversal, six captures, clean-index import,
external review, release validation, exact staging, commit, and post-commit verification.
