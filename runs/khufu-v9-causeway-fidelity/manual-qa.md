# Khufu V9 Manual QA

## Matching Surface

- Rebuilt and launched the Windows Development Player under D3D11 at `1536x1024`.
- Directly inspected all six final editor captures, five final traversal/negative-control captures, and both final
  performance captures at original resolution after the final rebuild.
- Normal route observation: Valley Gate, roofed Covered Causeway midpoint, and V8 hub arrival are nonblank, framed, and visually distinct.
- Negative-control observation: the moved parapet graybox visibly enters the walkable lane and matches the collider that stops traversal.
- Mutation editor observation: re-enabled superseded graybox is visibly distinct from the clean production view.

## Runtime Results

- Happy path: `88.146m` traversed, maximum/final target error `0.000m`, three captures written.
- Negative path: stopped after `0.582m` by `V9_PROXY_Valley_To_Causeway_East_Parapet`, two captures written.
- Error-metric path: independent `0.750m` waypoint perturbation exceeded the `0.400m` gate and was rejected.
- Performance surface: participant and operator captures rendered successfully; no blank frame or V9 geometry overlap was observed.
- Every runtime route capture reports `fresh=True` and `semantic=True`; observed sampled luminance standard deviation
  is at least `0.1474` and range is at least `0.9272`.

## Boundary

- This passes matching-surface visual QA and collision-constrained Windows binary traversal QA.
- It does not claim a fresh human keyboard usability study; that remains a deferred product-playtest risk.

V9_MANUAL_QA: passed
