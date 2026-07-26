# Khufu V11 Royal Chamber Circuit Status

## Current State

- Phase: release verified; local commit pending.
- Verdict: implementation, evidence, clean staged-index import, Opus final review (`ship`), and
  review-required exact-index gate complete.
- V10 baseline commit: `42a63801ea4699c170dbe39838d63d6d93a506ec`.
- Unity: exact editor `6000.0.76f1` at `C:\Users\User\Unity\Hub\Editor\6000.0.76f1`.

## Verified

- Static validation: 5 renderers, 2,016 vertices, 1,008 triangles, and 33 colliders.
- Full map: 829 renderers, 65,918 vertices, 47,984 triangles, and 567 colliders.
- Clearance: 78 samples, zero blockers; enclosure: 13 rays, zero misses.
- Rebuild idempotence preserves scene, generated, and frozen V10 source signatures.
- Five negative controls and rollback checks pass.
- Six fresh 1600x1000 captures pass integrity and manual semantic review.
- Windows build succeeds with zero errors and restores `ProjectSettings.asset`.
- Actual CharacterController round trip reaches 15/15 anchors with 0.977 grounded fraction.
- Blocker-enabled control starts overlapped, then depenetrates and stops at 1/15 on the named
  Great Step collider with `Sides`; it is a route-falsification control, not a walk-in collision.
- V4, V5, V8, and V9 original logic passes. V10 differs only by the 13 allowlisted
  V11 Great Step transition deltas; its frozen validator source remains hashed in the receipt.

## Constraints And Risks

- The V11 renderer budget is exactly `5/5`, and the full-map renderer budget is
  exactly `829/829`; neither level has renderer headroom.
- The stacked chambers are non-traversable evidence art shown only through a controlled cutaway.
- The integration capture exposes the route for review; it is not evidence that the pyramid mass is hollow.
- Queen, descending, Subterranean, scan-void, global-lighting, VFX, and audio work remain deferred.

## Remaining Release Gates

1. Commit only the exact allowlisted V11 inventory.
2. Run the post-commit inventory validator and retain its local receipt.
