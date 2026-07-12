# Khufu V10 Debugging Audit

## Hypothesis 1: the traversal driver caused the HYBRID failure

- Evidence against: after separating XZ movement and bounded grounding, horizontal flags remained
  `None` while the old HYBRID floor repeatedly returned `Below`; applied grounding fell to `0.010 m`
  and error grew to `0.4568 m` at the same point.
- Root cause: the route rose into a crest and immediately descended while the `0.45 m` capsule still
  overlapped the previous floor footprint.
- Resolution: level the service landing without changing route count or collider count.
- Runtime confirmation: normal Windows traversal now reaches `16/16` anchors with max error `0.150 m`.

## Hypothesis 2: the Gallery floor edge, not Great Step, was the blocker

- Evidence against: extending the Gallery floor beneath the boundary did not move the stop position.
  Capsule support math predicted wall contact at the stop, and `CollisionFlags.Sides` was present.
- Root cause: a single `LastHitName` slot let a later floor callback overwrite the simultaneous side
  callback from the named wall.
- Resolution: classify side, ground, and ambiguous hits separately and snapshot the side slot before
  grounding movement.
- Runtime confirmation: the same move reports the exact Great Step wall as side and Gallery ramp as
  ground; the exact-name boundary control passes without moving the wall.

## Hypothesis 3: green frame metrics were enough performance evidence

- Evidence against: the first raw profile streamed all 3,555 frames and reached `919,154,102 bytes`,
  failing the frozen `100 MiB` artifact ceiling despite green timing metrics.
- Root cause: `-profiler-capture-frame-count` was omitted.
- Resolution: capture 300 raw frames while retaining the full 35-second in-player metric procedure.
- Runtime confirmation: final raw profile is `36,978,740 bytes`; timing, memory, geometry, image, log,
  and raw-size gates all pass.

V10_DEBUGGING_AUDIT: passed
