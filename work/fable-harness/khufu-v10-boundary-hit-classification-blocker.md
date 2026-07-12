# Khufu V10 Great Step hit-classification blocker

Decision needed: approve or reject classifying all controller hits by contact normal and using the
side-contact collider for the Great Step assertion. Return the review directly. Do not write files.

## Goal and false-done condition

- Goal: prove the full-size Unity `CharacterController` is stopped by the exact named Great Step
  wall while preserving the playable Gallery floor and unchanged `0.4 m` error gate.
- False done: moving the wall only to satisfy the harness, ignoring a different side obstruction,
  accepting a floor `Below` hit as the blocker, or weakening the exact-name assertion.

## Repeated evidence

- Two independent Windows controls stop at the same world position near `GreatStepStop`.
- Before and after extending the Gallery floor beneath the wall, the control advanced
  `0.299/2.200 m`, reached error `0.511 m`, and returned horizontal flags containing `Sides`.
- The existing recorder stores only `LastHitName`. The last callback is the Gallery floor, so the
  receipt reports `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp` even though the `Move` flags include
  a side contact.
- Normal traversal approaches the same point continuously from below. It records only `Below` until
  the final sample, then returns `Sides | Below` and stops `0.150 m` short of the target. The normal
  route accepts this because the error remains below `0.4 m` and immediately turns around.
- The floor-extension mesh and collider are present in the final scene and static pair checks pass;
  changing their length did not alter the stop position.

## Capsule-to-wall geometry check

- Gallery forward vertical component: approximately `0.380`.
- Upright capsule radius / half-cylinder: `0.45 / 0.55 m`.
- Capsule support distance along Gallery forward:
  `0.45 + 0.55 * 0.380 = 0.659 m`.
- Named wall near face is `1.04 m` forward of `GreatStepStop`.
- Player center uses world-up half-height plus clearance; its projection along Gallery forward is
  approximately `1.08 * 0.380 = 0.411 m`.
- Remaining center-to-wall gap is `1.04 - 0.411 = 0.629 m`, less than capsule support `0.659 m`.
  Therefore the named wall should physically touch the capsule at the intended stop point.

## Proposed Codex action

1. Extend `KhufuControllerHitRecorder` to retain the latest side and ground hits separately, using
   the contact normal relative to world up.
2. During horizontal `Move`, record the side-hit name before the grounding `Move` can overwrite it.
3. Keep the exact expected boundary name and `CollisionFlags.Sides` assertion unchanged.
4. Rebuild and rerun the boundary control. The control passes only if the side-contact name is the
   exact Great Step wall.

## Required response

1. `VERDICT: proceed` or `VERDICT: revise`
2. `ROOT CAUSE:` concise assessment
3. `BLOCKERS:` concrete blockers or `none`
4. `NEXT ACTION:` exactly one action
5. `ACCEPTANCE:` exact evidence required

Do not write implementation code.
