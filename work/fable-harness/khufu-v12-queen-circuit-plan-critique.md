# Khufu V12 Queen Circuit — Plan Critique

Role: Act as the architecture, level-flow, regression, and evidence critic. Do not implement.

## Task Goal

Implement the next bounded Unity production-art slice after committed V11: open V10's Queen branch
ownership gate, replace only the old V4 Queen horizontal-passage/chamber blockout with a coherent
V12 passage and chamber, prove a standing-player round trip, and preserve the accepted V4–V11 map.

The conventional label “Queen's Chamber” is an architectural name, not a burial-purpose claim.

## Baseline And Constraints

- Baseline commit: `1dd7156b064a99eaa2d19ccca0ae605befae54fd`.
- Baseline scene SHA256:
  `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`.
- Unity is fixed at `6000.0.76f1`.
- Shared worktree has extensive unrelated changes; V12 must use an exact allowlist and may not
  stage or edit them.
- V11 map metrics are `829 renderers / 65918 vertices / 47984 triangles / 567 colliders`; root and
  map renderer budgets have zero headroom.
- V10 `GalleryFoot = (3.2, 5.4, -7.4)` and `QueensChamber = (-1.8, 5.35, -2.8)`.
- V4 already owns the marker `V4_Route_Queens_Chamber` and primitive Queen passage/chamber
  renderers/colliders. V10 intentionally excludes those objects from its suppression manifest.
- V10 combines `Queen_Ownership_Gate` into its red-granite mesh and owns a same-name proxy collider.
- V11 already rebinds V10 limestone/granite to V11-owned Great-Step-open variants and disables the
  Great Step proxy. V12 must preserve that state while additionally removing only the Queen gate.
- V4/V5/V8/V9/V10/V11 validators, V11 signature, V10 frozen source assets, Crown route, and scene
  behavior outside the declared Queen transition are immutable evidence boundaries.
- Descending/Subterranean routes, scan anomalies, global lighting, VFX, audio, enemies, objectives,
  and fresh-player usability remain out of scope.

## Research And Player Intent

Repository and source audit supports a horizontal passage from the Gallery Foot, a limestone
chamber with an east-wall niche, a gabled ceiling, and two narrow shaft mouths. No purpose is
assigned to the chamber, niche, or shafts. Historic dimensions are compressed to the existing
56 m project pyramid; the route is widened only enough for the existing CharacterController.

Player experience: the low, restrained passage should release into one readable limestone room.
The chamber is a destination and turnaround point, not a hub or invented shortcut.

Primary references:

- Egyptian Ministry, *The Great Pyramid*.
- Petrie, *The Pyramids and Temples of Gizeh*, measured Queen's Chamber dimensions and ridge.
- Maragioglio and Rinaldi, *L'Architettura delle Piramidi Menfite IV*, passage/chamber survey.

## Proposed Implementation

### 1. Freeze a pre-write contract

Create V12 `GOAL`, `RULES`, `RESEARCH_BRIEF`, `PLAN`, `TEST_PLAN`, classification, performance
budget, and a Python fail-closed prewrite validator with mutation tests. Add a Unity read-only audit
that records:

- exact V4 Queen renderer/collider/glow transition set and preserved marker;
- V10 Queen gate mesh spec and proxy path;
- current V11 open mesh bindings and Great Step blocker state;
- V11 root signature, complete map metrics, scene hash, and conflicting bounds.

No scene write is allowed until the prewrite gate passes.

### 2. Own the successor transition

- Add a V12 root with separate visual, structural-pair, collision-proxy, and metadata children.
- Disable only the audited V4 Queen passage/chamber visuals and colliders plus its route glow;
  preserve `V4_Route_Queens_Chamber`.
- Generate V12-owned V10 successor meshes from frozen V10 specs, filtering the already removed
  Great Step boundary/bars and additionally `Queen_Ownership_Gate`. Do not modify V10 or V11 mesh
  assets.
- Rebind V10 limestone/granite to those successor assets, keep the Great Step proxy disabled, and
  disable the exact Queen gate proxy. Capture and restore every binding/component state on failure.
- Rebuild must be idempotent and rollback must restore the pre-build scene and asset signatures.

### 3. Build a small, readable route

- Route: Gallery Foot -> opened threshold -> low horizontal passage -> chamber entrance -> chamber
  center -> return by the same passage.
- Use five or fewer combined renderers: limestone structure, niche/shaft shadow, restrained
  limestone detail, route inlay, and optional inspection accent.
- Structural visuals with gameplay collision receive exact named BoxCollider proxies.
- Preserve the chamber's gabled spatial read, east-wall niche, and two non-traversable shaft-mouth
  recesses. No shaft is enlarged into a route.
- Keep the critical path visually legible from the threshold and make the exit readable from the
  chamber center without UI.

### 4. Validate fail-closed behavior

- Exact root identity, hierarchy, segment classification, geometry signatures, collider pairs,
  route clearance, chamber enclosure, V4 transition set, V10 double-open bindings, marker
  preservation, budgets, forbidden components, and baseline source hashes.
- Negative controls: V10 Queen gate re-enabled, V4 overlap restored, structural pair displaced,
  chamber enclosure removed, and injected builder failure with exact rollback.
- Legacy runner invokes original V4/V5/V8/V9/V10/V11 validation logic with only later roots
  detached or predecessor bindings restored in memory. Any successor delta needs an exact named
  set and count; no free-form prefix-only acceptance.

### 5. Prove runtime and visual behavior

- Six fresh 1600x1000 captures: opened branch axis, low passage, chamber wide view, east niche,
  gabled ceiling with shaft boundaries, and full-pyramid cutaway integration.
- Windows development build with scene/source/assembly hashes and zero build errors.
- Built-player CharacterController round trip with serialized anchors, <=0.40 m maximum/final
  error, >=0.90 grounded fraction, and exact V12 renderer/collider totals.
- Boundary control starts outside the enabled Queen gate and walks into it. Require the same
  `Move` to report `Sides` and `OnControllerColliderHit` to name the exact gate; overlap-based
  promotion is not acceptable for this control.

### 6. Close release scope

Run focused Python tests, Unity import/compile, static/idempotence/negative/legacy gates, captures,
Windows controls, a dependency-closed clean-index import, Opus final review, review resolution,
review-required exact-index convergence, scoped commit, and post-commit inventory validation.
Raw logs and ignored builds are evidence inputs, not commit artifacts.

## Proposed Success Checks

1. Normal built-player route reaches every anchor and returns to Gallery Foot.
2. Re-enabled Queen gate blocks before the threshold and reports its exact collider by callback.
3. V4 Queen blockout is fully superseded without touching other V4 content.
4. V10 remains Great-Step-open and becomes Queen-gate-open only through V12 assets.
5. Original validators pass under the documented scoped/restored context; no unexpected delta is
   classified.
6. Map renderers do not exceed 829 and colliders do not exceed 600.
7. Scene/generated signatures stabilize after rebuild and after final capture.
8. Six captures show a coherent enclosed route without hollow-pyramid implication.
9. Exact staged inventory contains no unrelated dirty-worktree path.

## Known Unknowns

- The exact audited count of V4 Queen renderers/colliders and net map-budget headroom must be
  measured before builder code.
- Removing the Queen gate may change only V10 granite topology, but original-validator failure
  wording/count must be observed rather than predicted.
- A genuine callback-named walk-in collision may require probe start/distance tuning in the built
  player.
- Existing casing/cutaway renderers may require capture-only isolation; normal player views must
  remain enclosed.

Return:

1. Blocking findings in priority order
2. Missing tests or evidence
3. Recommendation: adopt / adopt with changes / revise

Decision needed: Is this V12 boundary safe and sufficient to implement, and what must change before
the first Unity scene write?
