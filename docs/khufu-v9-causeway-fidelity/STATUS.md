# Status

Current decision: **external Fable revisions are implemented and verified, Local Fable says `ship`, and the
staged V9 change set passes its scoped commit gate**.

## Completed

- V8 completion and frozen evidence were re-audited.
- The next highest-value corridor was bounded to Valley Gate -> Covered Causeway -> V8 Temple Hub.
- Existing V5 ownership was measured: two authoritative route-floor colliders; visible district and side-wall
  graybox currently lacks matching collision.
- Unity 6000.0 guidance was reviewed for mesh combination, static batching, LOD, MeshCollider use, and profiling.
- The source/scene audit passed with 20 superseded renderers, two inherited forward-floor colliders, and 562
  candidate source renderers. No causeway-specific donor mesh existed, so V9 uses a deterministic modular kit.
- The final V9 root contains five combined renderers, 1,512 vertices, 756 triangles, and 23 BoxCollider proxies.
- All 23 structural visual/proxy pairs match at 0.000m bounds delta. The inherited floor/art maximum bounds,
  position, scale, and angle deltas are 0.040m, 0.020m, 0.040, and 0.000 degrees.
- The causeway visual envelope contains 32 enabled solid colliders: 23 V9 proxies, two inherited floors, seven
  colliders with enabled visible geometry, and zero orphaned/invisible colliders.
- The hub-side 12m fanout remains open. This fixed a discovered Sun/Crown and hub-proxy regression; final V5
  Gate 4 passes 415 clearance samples and 8/8 hub proxy positions.
- V5 PlayMode traverses 1,758.6m over 3,533 CharacterController steps with 0.338m maximum error.
- The Windows D3D11 player binds its 88.146m route to serialized anchors and traverses it with 0.000m final error.
  The proxy negative control stops after 0.582m with 1.078m error; the independent metric control injects 0.750m
  error and trips the 0.400m threshold.
- Runtime captures delete same-path predecessors, prove fresh creation, decode in Unity, and pass pixel checks.
  Aggregate validation independently checks PNG CRCs, IEND, decompression, scanlines, and sampled pixels.
- The Windows build receipt hashes all 268 files returned by `BuildReport.GetFiles()`; editor/player/performance
  bindings independently include the same full runtime payload inventory.
- The refreshed aggregate passes 83 required files, 13 fully decoded PNGs (minimum sampled stddev/range/colors
  `0.1133 / 0.7779 / 3,089`), 159 V9-owned scene documents, and exactly 20 renderer transitions against
  baseline commit `c63e0ec6`.
- Performance passes for the documented 1536x1024 Ultra procedure: 3,592 samples; frame/main/render/GPU p95
  8.338/3.095/2.936/2.370ms; 132.7MB maximum allocated memory; 30,955,555-byte bounded raw capture.
- External Fable returned `revise, then ship`; both blockers (error-metric falsifiability and inverse collider
  ownership) are now implemented and verified. The independent runtime auditor's payload and image-integrity
  findings are also closed.
- Local Fable issued `ship`. Staged-index validation passes with 89 allowlisted files and zero staged/worktree
  drift, so the slice is ready for its scoped commit.

## In Progress

- None for this V9 slice. Deferred districts and polish remain outside its completion boundary.

## Deferred

- Authentic Interior Spine and every other V5 district.
- Baked occlusion, full-map LOD coverage, global lighting, VFX, audio, and fresh-player usability study.
