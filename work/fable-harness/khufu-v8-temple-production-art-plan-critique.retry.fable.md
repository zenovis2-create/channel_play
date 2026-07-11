This is a review request, not an implementation task — I'll deliver the critique and record it in the plan file.

**Assessment**

1. **Is any remaining gap blocking?** No. The two prior hard blockers are resolved with evidence: the Editor-side combine works with Read/Write disabled without mutating FBX or `.meta` (byte-identical hashes), and the post-combine budget is measured and sane (9 buckets, 33,378 verts, 27,540 tris vs. the rejected 333,700-tri full source). The two acknowledged unknowns — exact V5 hub renderer count and X/Y art offset — can only be measured during integration and are correctly frozen by tests afterward; deferring them does not change the implementation path. The worst-angle profile likewise requires the integrated scene, so scheduling it as a step-8 gate rather than a pre-implementation spike is acceptable, provided it remains a hard gate that can revert the slice.

   One correctness note, not a blocker: step 5's corridor clearance is scoped to "every selected structural **donor**," but step 2 introduces an **authored** square red-granite pillar mesh that is not a donor. As written, the clearance gate could pass while the new pillars block the route. Fold authored placements into the same gate.

2. **Must-add tests (two):**
   - **Corridor clearance including authored geometry:** the 1.8m × 2.2m route sweep must enumerate donors *plus* every authored pillar instance, and fail on any non-floor/non-overhead-trim intrusion — with one negative control (a pillar deliberately placed in-corridor must fail).
   - **Selector-drift budget assertion:** regenerate the selection and assert exactly 9 material buckets, vertex/triangle counts equal to the dry-run figures (33,378 / 27,540), and zero matches for the forbidden classes (helpers, pyramid, trap, burial, rear, round columns, route-crossing podium/stairs). This freezes the selector so a future source-scene edit cannot silently reintroduce rejected geometry.

PLAN_CRITIQUE: proceed
