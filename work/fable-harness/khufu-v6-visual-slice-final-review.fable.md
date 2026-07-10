## Final review — Khufu V6 visual-fidelity slice

### Blocking issues

None found on the supplied evidence. Every false-done condition has a corresponding passed, mutation-tested check: current-scene hash binding across captures/PlayMode/build/player, 9/9 frozen-input hashes, visible D3D11 player (not hidden/no-graphics), fresh Gate 4 + CharacterController traversal, and Fable-verdict mutation tests in `tools/tests/test_validate_khufu_v6_visual_slice.py` (7/7).

### Assessment of question 3: semantic idempotence + scene-hash binding vs. large YAML reserialization

Sufficient, with one ordering condition that must be enforced by the validator rather than by narrative. Because the V5 rebuild reassigns serialized fileIDs, the rebuild is semantically idempotent but almost certainly **not byte-idempotent** — each rebuild can produce different scene bytes with the same semantic signature. That means the two idempotence runs and the evidence-generating run may each have distinct scene hashes. The scheme is sound only if the aggregate validator compares the scene SHA256 **recorded inside each artifact** (captures, PlayMode log, build receipt, player performance receipt) against the current on-disk scene `09c8…b95b`, not merely against each other, and confirms no rebuild occurred after evidence generation. The prompt states the pre-Fable aggregate "checks every above binding"; Codex-side check to confirm before commit: the validator fails when any single artifact's embedded scene hash diverges from the live file (the stale-scene mutation test suggests this exists — confirm it covers all four artifact classes, not only captures). Given that, the 25k-line diff is acceptable noise: fresh Gate 4 (6/6) and fresh PlayMode traversal re-prove topology on the exact current bytes, so byte-level stability of the YAML is not required.

### Non-blocking improvements (each tied to a concrete risk)

1. **Stage-time re-verification.** The dirty worktree is the highest residual risk for the "unrelated changes entering the commit" false-done condition. After Codex stages the V6 whitelist, rerun the frozen-input 9/9 check and the current-scene hash check against the **staged index** (`git show :<path>` content), not the worktree. This catches both an accidentally staged frozen file and a whitelist that misses the evidence-bound scene.

2. **Texture/material GUID stability across rebuilds.** The four generated albedo/normal pairs and seven materials are builder-created. If the builder regenerates them with new GUIDs, materials or the scene would dangle after a future rebuild even though the semantic signature passes. Codex-side check: confirm the semantic signature (or a companion check in `validate_khufu_v6_visual_slice.py`) includes material→texture GUID references, and that all generated assets **and their `.meta` files** are in the commit whitelist. A missing `.meta` is invisible locally and breaks on fresh checkout.

3. **Renderer-budget scoping.** The player run reports 792 renderers scene-wide while the V6 budget is 12. That is consistent only if the validator counts renderers under the V6 root exclusively. Confirm the budget query is rooted at the V6 hierarchy, not scene-wide, so a future regression outside the root cannot silently pass (or a legitimate V5 count fail) the wrong budget.

4. **16.3s Windows build.** Plausibly incremental. Since build-script and output hashes are recorded and the player was actually executed with the correct scene content (captures/perf bound to scene hash), this is acceptable; note it in the receipt so a future reader doesn't mistake it for a clean-build time.

### Explicitly acknowledged gaps — accepted

Unity MCP registration failure and NotebookLM expiry are honestly scoped out and substituted with batch/PlayMode/player evidence; no claims rest on them. The `git diff --check` trailing-space warnings are Unity-generated and correctly left untouched to preserve evidence binding. The 185 Sentis shader warnings are third-party and outside the slice.

### Decision rationale

All hard gates pass with margin (visual deltas ~2.3–2.5× minima, frame p95 8.34ms, artifact cap respected after a properly diagnosed and rerun profiling attempt), the false-done surface is mechanically checked with mutation coverage, and the remaining risks above are commit-hygiene items Codex can enforce during the scoped stage without regenerating any Unity evidence.

FABLE_VERDICT: ship
