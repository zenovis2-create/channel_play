# Khufu V10 capture blocker analysis

## Decision needed

Choose the next implementation path for the Queen-branch evidence view after the same deterministic
capture gate failed twice. Decide between (A) local proof lighting, (B) camera relocation, (C) a
diagnostic V10-only render to identify legacy-renderer overlap, or (D) expanding the frozen renderer
transition manifest. Recommend the smallest truthful path that preserves runtime fidelity.

## Goal and false-done condition

- Goal: produce readable, semantically correct evidence of the V10 Gallery Foot and Queen branch
  boundary while preserving the integrated map.
- False done: a PNG passes byte/variance thresholds but is dark, occluded, capture-only deceptive, or
  unlike the actual Windows player view.

## Cheap evidence already gathered

- The full V10 static suite passes: 221 route-clearance samples, minimum enclosure 0.792, zero route
  collisions, exact 45 renderer and 39 collider transitions, stable idempotence and mutation gates.
- First capture attempt used directional intensity 1.15 plus point intensity 3.8. It rendered readable
  pixels but visibly overexposed and framed from outside the route.
- Second attempt disabled scene lights, used flat ambient 0.23 and directional 0.38, and moved cameras
  to route centerlines. The Queen view failed the custom quality gate.
- Third attempt used flat ambient 0.30 and directional 0.52, and moved the camera onto the Queen branch
  centerline. It failed again with: bytes=1780455, mean=0.1462, stddev=0.0323, range=0.2927,
  clipped=0.0000.
- Direct inspection shows a large dark/flat surface dominates the Queen frame. The ascending route
  view is now geometrically readable, suggesting the global light setup alone is not the root cause.
- The V10 transition manifest was frozen before scene write. Expanding it without identifying exact
  offending renderers would violate the evidence contract.
- Unity documentation confirms flat ambient color controls scene-wide ambient light and camera
  culling/renderer visibility can isolate groups for diagnosis. A diagnostic-only isolated render can
  distinguish geometry/lighting from legacy overlap, but must not be presented as runtime proof.

## Proposed Codex path

1. Add a diagnostic-only capture that temporarily hides non-V10 renderers and captures the same Queen
   camera, restoring all states afterward.
2. Compare normal and isolated images directly.
3. If both are bad, fix camera/material/geometry. If only integrated is bad, enumerate exact
   foreground renderers and amend the transition contract before changing the manifest.
4. Re-export the normal integrated evidence and verify it manually. Keep the isolated image only as a
   debug receipt, never as the final semantic capture.

## What Fable's answer changes

It determines whether Codex should keep tuning lighting/camera or open the higher-risk frozen
transition contract. Please return:

- `VERDICT: proceed | revise`
- blocking findings, if any
- the next single diagnostic action
- conditions that justify changing the frozen manifest

