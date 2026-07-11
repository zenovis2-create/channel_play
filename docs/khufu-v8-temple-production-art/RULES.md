# Rules

## Ownership Boundary

- V5, V6, and V7 builders, validators, runtime scripts, materials, and accepted root metrics are frozen inputs.
- New hierarchy belongs under `Runtime_Khufu_V8_Temple_Hub_Art`.
- Generated meshes belong under `Assets/_Project/Art/Generated/KhufuV8TempleHub`.
- V8 may disable renderers only in `V5_District_Pyramid_Temple_Hub` and
  `V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized`; it may not disable or delete their GameObjects or colliders.
- The imported FBX's cameras, lights, gameplay markers, and review collision meshes never enter the final V8 hierarchy.
- Frozen source identity covers both the FBX binary
  (`234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d`) and its `.meta`
  (`6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094`).
- The source importer remains Read/Write disabled; the verified Editor combine path must not rewrite importer state.

## Art Budget

- V8 root: at most 12 renderers, 120,000 vertices, 100,000 triangles, 0 colliders, 0 lights, 0 cameras.
- Full map: at most 815 renderer components and 441 colliders before runtime-only player components.
- The final frozen implementation tightens the V8 root to 10 renderers, 33,550 vertices, and 27,180 triangles;
  the Windows performance pass allows at most 60,000 visible vertices and 48,000 visible triangles while retaining
  the V5 frame/main/render/GPU and memory limits.
- Materials must distinguish limestone, basalt, red granite, shadow, and painted/relief accents.
- The generated mesh build must preserve stable asset GUIDs and produce identical topology/signatures on repeated rebuilds.
- Structural donor bounds must preserve a 1.8m-wide visual corridor along the causeway axis; floors, lintels,
  and overhead trim are classified separately from route-blocking walls.

## Evidence Rules

- Every receipt binds the source FBX, frozen V5-V7 files, scene, generated meshes, and final executable by SHA256 where applicable.
- A rendered Windows-player screenshot is mandatory; editor-only or synthetic evidence cannot approve visual quality.
- Normal and mutation screenshots must be distinct files and directly inspected.
- Performance passes only through raw profiler data plus matching screenshots, logs, and scene/build bindings.
- Screenshot acceptance is valid only on the pinned rendered Windows D3D11 path; `-nographics` or another graphics
  API cannot substitute for final visual evidence without a new baseline.
- The scoped commit whitelist must exclude the existing dirty package, ProjectSettings, studio, memory, and pipeline state.

## Collision Scope

- V8 is presentation-only and intentionally adds no colliders. The V5 gameplay collider scaffold remains authoritative.
- The causeway/Temple Hub critical corridor is validated at 1.8m width and 2.2m height, including authored pillars.
- Visible-to-collider fidelity outside that corridor is explicitly not approved by V8 and remains future full-map work.

## Metric Accounting

- Static map metrics count every scene MeshFilter, including disabled V5/V6 graybox renderers.
- Runtime performance metrics count enabled renderers plus the instantiated participant/runtime meshes. Therefore the
  observed `57,332 vertices / 44,104 triangles` is expected to differ from static `57,518 / 43,784`; both have
  independent hard limits and the runtime GPU p95 remains the decisive rendering gate.

## Historical Claim Boundary

- Supported vocabulary: an east-side pyramid temple approached by a causeway, black basalt paving/threshold,
  limestone walls, red-granite pillars, painted relief fragments, and a narrow northwest court exit.
- The exact intact superstructure is not preserved and must be labeled as a game-art interpretation.
- V5's large labyrinth and V8's wayfinding treatment are fictional gameplay design, not archaeological evidence.
