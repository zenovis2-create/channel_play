# Rules

## Ownership Boundary

- V5-V8 source code, materials, generated assets, accepted roots, and gameplay bindings are frozen inputs.
- All new hierarchy belongs under `Runtime_Khufu_V9_Causeway_Fidelity`.
- All generated meshes belong under `Assets/_Project/Art/Generated/KhufuV9CausewayFidelity`.
- V9 may disable renderers only in the exact Valley Gate, Covered Causeway, and duplicated critical-route segment
  whitelist. It may not disable or delete their GameObjects, inherited colliders, or components.
- V9 may add BoxCollider proxies only under its own `V9_Collision_Proxies` child.
- No V9 camera, light, trigger, gameplay binding, MeshCollider, or Rigidbody is allowed.

## Corridor Contract

- Route endpoints are `(150, 0.15, 0)`, `(105, 3.15, 0)`, and `(62, 1.15, 0)` in world space.
- Windows CharacterController proof points use those serialized floor anchors plus the fixed 1.25m capsule-center offset.
- Existing route-floor collider count remains exactly two for the forward approach.
- Structural visual/proxy pairs use matching world bounds within 0.05m per axis.
- Sampled player clearance is at least 1.8m wide and 2.2m high.
- Decorative floor inlays and relief accents remain non-collidable.
- Enabled solid collision in the V9 renderer envelope must resolve to a V9 proxy, an inherited floor, or enabled
  visible geometry. A collider attached to any other superseded renderer is forbidden.

## Budget

- V9 root: at most 6 renderers, 80,000 vertices, 70,000 triangles, 24 BoxColliders, 0 MeshColliders,
  0 lights, 0 cameras, and 0 rigidbodies.
- Full map: at most 819 renderer components and 465 colliders before runtime participant components.
- The V8 frame, main, render, GPU, and memory limits remain hard limits.
- Generated mesh GUIDs, topology signatures, and hashes must be stable across two rebuilds.

## Evidence

- Editor, player, and performance binding inventories each hash the V8 baseline revision, scene, every V9
  source/meta/mesh, every BuildReport runtime payload file, and their exact evidence artifacts.
- Final visual evidence requires the rendered Windows D3D11 path plus direct image inspection.
- Runtime screenshots must delete any same-path predecessor, prove fresh creation, decode successfully, and pass
  luminance/range checks. Aggregate PNG validation rechecks chunk CRCs, IEND, scanlines, and sampled pixels.
- Normal traversal, deliberate collision/graybox mutation, and a 0.75m error-metric perturbation must produce the
  expected opposite outcomes.
- Scope validation rejects package, ProjectSettings, studio, memory, and pre-existing asset-pipeline changes;
  every staged V9 artifact must equal the already-validated worktree bytes.

## Historical Boundary

- V9 is a game-art interpretation of an east-side causeway approach using basalt, limestone, red granite,
  and painted/relief accents.
- The exact intact causeway superstructure is not preserved; the layout must not be labeled a reconstruction.
