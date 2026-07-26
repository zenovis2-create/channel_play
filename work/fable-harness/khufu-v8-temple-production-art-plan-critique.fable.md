**1. Is the plan safe and efficient?** Broadly yes. Steps 1–3, 6, 8, and 10 are the right shape: freeze hashes, whitelist donor vocabulary, disable (not delete) graybox renderers, and use restore-verified negative controls. The main efficiency risk is step 4's ambition (deterministic GUID-stable combine) relative to the two known gaps you already listed.

**2. Hidden failure modes that matter most:**

- **CombineMeshes readability (your gap #2) is the plan's load-bearing unknown.** If the FBX importer has Read/Write disabled, `Mesh.CombineMeshes` fails at edit time or silently produces empty meshes in a player build. This must be exercised *before* committing to the 12-mesh architecture, not discovered during evidence capture. Fallback: flip Read/Write on the FBX importer — but that changes the FBX .meta, which may collide with your frozen-FBX-hash contract. Decide now whether the freeze covers the .meta or only the binary; if it covers the .meta, the plan is internally contradictory and needs the read/write toggle done first, then frozen.
- **Vertex budget headroom is thin.** Donor total is 379,938 verts across 2,565 renderers; your slice budget is 120k verts in ≤12 renderers. Combining inflates vertex counts at material-bucket seams (split normals/UVs duplicate vertices), so post-combine counts can exceed the naive sum of selected subparts. Validate the budget against the *combined* mesh, and expect the selector to need iteration — don't treat first-pass selection failure as a plan failure.
- **Combined meshes defeat frustum culling.** Twelve hub-spanning combined renderers are always-on-screen from most route angles. At 120k verts this is fine on Windows, but your 35-second performance check should capture the *worst* camera angle (looking through the whole slice down the causeway), not an average one.
- **Placement conflict is under-specified.** You state the route approaches along world -X and branches, and that "closed donor side walls would conflict" — but exclusion list (step 3) removes side/rear walls by *source group naming*, and FBX hierarchies frequently misname wall segments. The +5m negative control catches gross misplacement, not a single mis-bucketed wall segment clipping the route. Add a route-corridor clearance check: raycast or bounds-sweep the 1,758.6m CharacterController path against the 12 new renderer bounds (they're collider-free, so only a visual/bounds check works).
- **Renderer-disable whitelist drift.** Step 6 disables "exact V5 hub and V6 colonnade" renderers. If the whitelist is by name/path and the scene has duplicate names, you can disable the wrong renderer or miss one. Whitelist by stable component identity (scene fileID or full path + index) and assert the expected count (V6 = exactly 11) before and after.

**3. Minimal checks Codex should run (ordered):**
1. Spike: combine two donor subparts, verify Read/Write behavior and vertex inflation, in a throwaway asset — before building the selector.
2. Selector dry-run emitting counts (renderers/verts/tris per bucket) with zero scene mutation; compare against budgets.
3. Route-corridor bounds clearance check against the 12 combined renderer AABBs.
4. Disabled-renderer whitelist count assertion (V6 == 11; V5 hub == exact known count).
5. `git diff --stat` against the staging whitelist before commit — the dirty worktree makes this the single highest-value guard against the false-done condition.
6. Worst-angle frame in the performance capture.

**4. Should Codex change the plan?** Yes — one reorder, one addition, no scope change:
- **Reorder:** run the CombineMeshes read/write spike and selector dry-run (checks 1–2) as step 0, before freezing the FBX .meta, and define exactly what the FBX freeze covers.
- **Add:** the route-corridor clearance check and whitelist count assertions to step 7's validation set.
Everything else (selective slice at (62,1,0) +90°, renderer-disable approach, negative controls, staged whitelist) stands. Options B (whole FBX, 3,368 renderers) and C (new kit) remain correctly rejected.

**5.** PLAN_CRITIQUE: revise
