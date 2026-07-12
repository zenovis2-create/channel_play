# Khufu V10 traversal blocker analysis

Decision needed: approve or reject option A as the next implementation action. Return the review in
your response only. Do not write, edit, or propose writing any file.

## Decision needed

Choose the smallest truthful fix for a repeated Windows-player traversal failure at the first
descending turn of the HYBRID service return. Decide between (A) changing the proof driver to use
normal CharacterController horizontal motion plus a separate downward/grounding move, (B) changing
the floor-junction geometry, or (C) relaxing the 0.4 m route-error gate. Recommend one path and the
specific evidence that must pass before the result can be accepted.

## Goal and false-done condition

- Goal: prove that a real Unity `CharacterController` can walk the complete 96.672 m V10 round trip,
  while the named Great Step boundary remains impassable and an intentional error-metric mutation
  is rejected.
- False done: teleporting through geometry, disabling V10 colliders, accepting an error threshold
  wider than the 0.45 m player radius, or changing map geometry only to make the harness green.

## Exact repeated blocker

- Windows Development Player, Unity `6000.0.76f1`, 1536x1024, D3D11.
- Attempt 2: `reached=10/16`, `traversed=62.157 m`, `max_error=0.468 m`, blocked collider
  `V10_PROXY_HYBRID_Service_Return_Service_Return_01_Floor`.
- Attempt 3: `reached=10/16`, `traversed=62.036 m`, `max_error=0.457 m`, blocked on the same exact
  collider `V10_PROXY_HYBRID_Service_Return_Service_Return_01_Floor`.
- Both attempts fail when leaving HYBRID floor segment 01 for the next descending segment. The
  collider named in the hit is the floor just traversed, not a wall or the next segment.
- Static V10 gates still pass: 221 clearance samples, minimum enclosure 0.792, exact 6 renderers and
  70 V10 BoxColliders, stable build/idempotence/mutation gates.
- The player reached the North entrance, ascending bypass, Grand Gallery, Great Step stop, and
  returned to Gallery Foot before this failure. Both runtime captures produced fresh semantic PNGs.

## Attempts already made

1. Initial probe put a height-2 m capsule center only 0.08 m above the floor route. It correctly
   failed immediately because the capsule was embedded in the entrance floor by roughly 0.92 m.
2. Probe then offset the center using per-segment floor normal and capsule support. It progressed to
   10/16 anchors but the support vector changed discontinuously at the HYBRID turn; failure 0.468 m.
3. Probe then kept the upright capsule at a consistent world-up half-height plus 0.08 m. It reached
   the same point and failed on the same floor at 0.457 m.

## Current implementation behavior

- Each 3D route step calls `CharacterController.Move(target - currentPosition)` once.
- On a descending junction, that vector combines horizontal advance with downward displacement.
- The exact previous-floor hit suggests the downward component is resolved against the floor the
  controller is standing on, leaving the controller too high while horizontal motion continues.
- Unity documents `CharacterController.Move` as constrained by collisions and does not apply gravity
  automatically. Normal gameplay commonly supplies grounding/gravity movement separately.

## Proposed Codex path

Use option A only in the proof driver:

1. Move the controller toward each route sample in the XZ plane.
2. Apply a separate bounded vertical correction after horizontal collision resolution, with downward
   grounding allowed and upward progress expected from walkable floor slopes.
3. Keep all V10 colliders enabled and retain the 0.4 m three-dimensional error gate.
4. Rebuild and require normal round trip, named-boundary negative control, and error-metric mutation
   control to pass in independent Windows-player processes.
5. If the same floor still blocks, stop and collect a per-step position/target/collision trace before
   considering geometry changes.

## What Fable's answer changes

It determines whether Codex changes only the traversal driver or opens the higher-risk geometry
contract. Please return:

- `VERDICT: proceed | revise`
- ranked root-cause assessment
- blocking findings
- the next single implementation action
- acceptance conditions for normal, boundary, and mutation runs

Do not write implementation code.

Required response format:

1. `VERDICT: proceed` or `VERDICT: revise`
2. `ROOT CAUSE:` ranked concise assessment
3. `BLOCKERS:` concrete blockers or `none`
4. `NEXT ACTION:` exactly one action
5. `ACCEPTANCE:` normal, boundary, and mutation run conditions

## Post-Fable runtime evidence

- Fable retry verdict: `proceed` with option A, bounded downward correction, unchanged `0.4 m`
  error gate, and per-step collision tracing.
- Option A was implemented with a `0.35 m` grounding cap and the same driver was used by normal and
  Great Step control processes.
- Normal run still failed at `10/16` anchors on the exact HYBRID 01 floor. The decisive trace row was
  horizontal flags `None`, grounding flags `Below`, requested/applied grounding `0.350/0.010 m`,
  and three-dimensional error `0.4568 m`. The driver advances freely in XZ; the old floor physically
  holds the capsule above the next descending segment.
- The preceding trace shows a sharp crest: HYBRID 01 rises into the junction, then the next route
  immediately descends. The height deficit grows monotonically over five samples while the capsule
  remains within the old floor contact footprint.
- Great Step control advanced only `0.299/2.200 m` and hit
  `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp`, not the named boundary. Its final horizontal flags
  were `Sides | Above | Below` (`7`). The Gallery floor collider ends at `GalleryTop`, while the named
  diegetic boundary starts beyond it at `GalleryTop + forward * 0.38 m`.
- Error-metric mutation passed independently at `0.750 m`, proving the unchanged `0.4 m` gate is
  active.
- Windows D3D11 performance passed after bounding the raw capture to 300 frames: 3,562 samples,
  frame/main/render/GPU p95 `8.338/2.737/2.483/2.048 ms`, raw `36,969,049 bytes`.
- Final V4 validation, V5 Gate 4, V5 PlayMode, and ten focused Python tests passed.

## Geometry decision now required

The evidence no longer supports another proof-driver adjustment. The smallest map-contract revision
is to flatten or lengthen the HYBRID crest so the capsule can clear the previous floor before descent,
and to carry the Gallery floor under the named Great Step boundary so that collider becomes the first
blocking surface. Threshold relaxation and collider disabling remain prohibited.
