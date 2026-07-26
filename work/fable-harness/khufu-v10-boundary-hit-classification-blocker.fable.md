**VERDICT: proceed**

**ROOT CAUSE:** Single-slot last-write-wins recorder, not geometry. The horizontal `Move` genuinely contacts a side surface — the `Sides` flag is present, and your capsule math holds (support along Gallery forward = 0.45 + 0.55×0.380 = 0.659 m vs. a 0.629 m center-to-wall gap, so ~3 cm of geometric interference, plus skin width margin on top). The grounding contact against the Gallery floor ramp simply fires later in the frame sequence and overwrites `LastHitName`. The receipt misreports the blocker; the physics is consistent with the named wall. The floor-extension length change not moving the stop position further supports a wall stop rather than a floor-edge snag.

**BLOCKERS:** none that reject the approach; three conditions on the fix:
1. Make the normal thresholds explicit. The Gallery ramp normal has y ≈ 0.925 and a vertical wall face has y ≈ 0, so side = |normal.y| < 0.3 and ground = normal.y > 0.7 is safe — but capsule-vs-step-edge contacts produce interpolated normals, so log hits in the ambiguous band instead of silently binning them.
2. Reset the side-hit slot at the start of each horizontal `Move` and read it immediately after that `Move` returns, before the grounding `Move`. Separate slots remove the floor-overwrite problem, but a lateral slide during the grounding `Move` could still write a different collider into the side slot.
3. The side-contact identity is still unverified — that is the exact evidence gap this change closes. If the side slot names the floor-extension edge or some other obstruction instead of the wall, the exact-name assertion must fail loudly rather than be widened. That outcome would be the correct false-done catch, not a reason to relax the check.

**NEXT ACTION:** Implement the dual-slot normal-classified recorder as proposed (side + ground slots, per-Move side reset, unchanged exact-name and `CollisionFlags.Sides` assertions), rebuild, and rerun the boundary control once.

**ACCEPTANCE:**
- Boundary control receipt shows the side-hit collider name exactly equal to the named Great Step wall, flags containing `Sides`, and the ground slot showing `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp`.
- Stop position unchanged from prior runs (advance ~0.299/2.200 m, error ~0.511 m), confirming no geometry was moved to satisfy the harness.
- Normal traversal route still passes with error < 0.4 m and its final sample still shows `Sides | Below`.

**Tool Call: ExitPlanMode**

```json
{
  "allowedPrompt": "Return the Great Step hit-classification review verdict (proceed, with conditions on normal thresholds, per-Move side-slot reset, and fail-loud exact-name assertion)"
}
```
