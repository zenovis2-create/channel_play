## Prioritized Findings

**1. FACT-label overclaim baked into the clearance gate (blocker).** The real Ascending Passage is roughly 1.05m wide by 1.2m high; a mandatory 1.8m × 2.2m clearance means every passage segment is dimensionally invented for gameplay. The plan says "Own Entrance → … → Great Step as FACT/HYBRID art" without saying which segments are which. As written, the Ascending Passage will pass the clearance gate while carrying an implicit FACT claim it cannot support. Smallest fix: a per-segment classification table (segment → FACT-shape/HYBRID-scale, with the compression ratio stated) committed *before* any scene write, and the semantic-screenshot gate checks labels against it. This changes the ownership/labeling policy, which per your own criteria is a pre-write blocker.

**2. HYBRID return risks reading as the Well Shaft despite the disclaimer (high).** The historical well shaft connects the Gallery Foot area toward the Descending Passage/subterranean zone — explicitly outside V10 truth boundaries. Adding a two-way Gallery Foot ↔ Branch return in nearly the same location, while also showing a "service-shaft mouth as boundary," invites conflation no matter what the docs say. Require: the return uses a visibly distinct material/marker language, carries an in-scene HYBRID tag queryable by the validation gates, and is spatially separated from the boundary-only service-shaft mouth. Add a check that no V10 object name or metadata contains "Well Shaft."

**3. The disable list is described but not produced (high).** "Disable only an audited exact list of superseded V4/V5 renderers/colliders" is the plan's most regression-prone step, and V5's Crown route bypasses V4 — disabling V5 objects can break a route V10 doesn't own. The Codex-side check: enumerate the exact object paths in a committed manifest, diff it against the V5 Crown route's dependency set before the scene write, and run the inverse-ownership gate against that manifest (every disabled renderer's paired collider disabled or explicitly transferred), not against a post-hoc scene scan.

**4. "Reads as freestanding staircase" has no objective gate (medium).** Corbel count plus human screenshot review is exactly the false-done you listed. Add a cheap enclosure metric: from N sampled points on the Gallery route, cast hemisphere rays and require ≥X% hit V10 geometry within a bounded distance. This converts the "hollow/freestanding" failure into a deterministic pass/fail.

**5. Determinism gate should hash generated assets, not just rebuild (medium).** For the combined-mesh kit, require byte-identical regeneration (stable GUIDs/meta, sorted iteration, fixed seeds) verified by hashing the generated files across two rebuilds; a scene that merely loads identically can hide GUID churn that breaks future staged-index validation.

**6. Great Step boundary needs a visible treatment (low).** An invisible blocking collider at the royal-suite boundary is indistinguishable from a collision bug to a player and to the traversal gate. Use a visible, diegetic boundary object owned by V10.

The negative controls (named blocker mutation, 0.75m error control), staged-index validation, and marker-transform preservation are sound as specified.

## Smallest Safer Plan

Before any V10 scene write: (a) commit the per-segment FACT/HYBRID classification with stated compression ratios; (b) commit the exact V4/V5 disable manifest diffed against the V5 Crown route; (c) add the enclosure-metric gate and the no-"Well Shaft"-naming check. Then proceed with steps 1–8 unchanged.

FABLE_PLAN_VERDICT: revise
