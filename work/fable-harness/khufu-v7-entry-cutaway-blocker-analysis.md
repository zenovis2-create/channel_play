You are Claude Fable 5 diagnosing a repeated Unity camera-cutaway blocker.
Return plain text only, under 500 tokens. Do not implement or call tools.

Goal:
At the initial Khufu Valley Gate camera, hide only the two exact V5 Valley Gate pylon renderers and
prove an unobstructed player view.

Decision needed:
What is the single fastest diagnostic experiment, and what is the most likely defect in the new
camera-proximity rule or its validator geometry?

Attempt 1 exact result from rendered Windows player:
`V7_ENTRY_PROOF: failed`, active cutaways=1, active Valley Gate pylons=0,
visible candidate occluders=0, camera=(150.007,7.311,-8.000), player=(150.007,1.311,0.000).
Direct screenshot remained blocked by red gate geometry.

Diagnosis after attempt 1:
The camera-to-look-target center ray passes about 0.7m above the rear pylon, while the camera is
adjacent to its bounds. The active renderer was likely the lintel, not a pylon.

Attempt 2 change:
- Candidate matching remains exact names only:
  `V5_Valley_Gate_Pylon_-1`, `V5_Valley_Gate_Pylon_1`.
- For those exact names only, copy renderer bounds, call `Expand(3.0f)`, and return true when the
  expanded bounds contain `ray.origin`; otherwise retain normal ray intersection.
- Editor validator now models the runtime camera at `(0,7.3,-8)`, target at `(0,1.2,0)` with
  lookHeight 1.35, rear pylon bounds center `(0,3,-7)` scale `(5,6,2)`, a front exact pylon on the
  center ray, one normal ceiling-beam on the ray, and one unrelated district pylon on the ray.
- Expected: hidden=3, active exact pylons=2, visible candidate occluders=0, unrelated pylon visible.

Attempt 2 exact result:
Unity compiles, then `ChannelPlayCameraCutawayValidator` throws:
`InvalidOperationException: Camera cutaway did not apply the exact Valley Gate pylon scope.`
The validator currently throws before logging individual renderer states, so hidden count and flags
are unknown.

Relevant implementation facts:
- `Configure()` refreshes renderer cache and calls `ForceRefresh()` once; validator then calls it a
  second time and reads state.
- `ShouldCutaway()` rejects inactive/tiny/non-candidate objects, then applies the exact-pylon expanded
  bounds check before normal `Bounds.IntersectRay`.
- Cutaway uses `renderer.forceRenderingOff`; diagnostic active-pylon count reads active renderer names.

Ask:
1. Most likely cause category.
2. One diagnostic change/run only, with exact fields to log.
3. Minimal fix direction only if the evidence already supports it.
End with `BLOCKER_NEXT: <one short action>`.
