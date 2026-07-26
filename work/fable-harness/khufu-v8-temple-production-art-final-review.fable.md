## Blocking issues

None that require code changes before staging, but one gate must hold:

1. **Scene-file staging bundles pre-existing dirt.** `Assets/_Project/Scenes/School_MVP.unity` was already modified in the worktree before V8 work began (per git status), and the V8 builder saves that same file. The staged scene diff will therefore contain any unrelated pre-existing edits unless the builder's `V7.Rebuild()` deterministically overwrites them. The frozen V6/V7 root signature checks partially cover this, but the Codex-side check must be explicit: after staging, diff the staged scene against a scripted rebuild-from-HEAD and confirm zero deltas outside the `Runtime_Khufu_V8_Temple_Hub_Art` root and the 16 `m_Enabled` flags. If that diff shows anything else, do not commit.

## Non-blocking findings (real-risk reducers)

2. **V8 art has 0 colliders; collision remains the disabled graybox's.** Validation proves the central route (corridor sweep X 48–78, PlayMode 1,758.6m run), but nothing asserts that every *visible* V8 structural surface is backed by a collider, or that no invisible graybox collider protrudes into visually open space off the main route. A player can walk through a visible V8 wall or bump an invisible one outside the swept corridor. Named check: bounds-overlap assertion between each V8 structural renderer and the surviving collider set (coverage ratio threshold), or an explicit acceptance note that off-route collision fidelity is out of V8 scope.

3. **Profiler vs. static count mismatch.** Static final map: 43,784 triangles; player profile: 44,104 triangles and 57,332 vs. 57,518 vertices. Likely shadow-pass/batching accounting, but the performance validator should either normalize the metric or document why runtime triangles exceed the static ceiling, so the budget check can't be silently satisfied by a counting artifact.

4. **Disable list robustness.** The exact-count (5+11) arrays plus the graybox-mutation test (16 renderers restored, proof fails) are good, but confirm the arrays bind by hierarchy path or fileID, not name-only lookup, so future scene edits fail loudly rather than disabling the wrong renderers. If already fileID-bound, no action.

5. **Capture determinism is D3D11/Windows-pinned.** The `-nographics` crash is fine to exclude, but the acceptance doc should state that screenshot evidence is invalid on any other graphics API, so a future CI migration doesn't silently regress the proof.

## Decision

The validation lattice is unusually strong: mutation tests fail in the right direction (pillar offset, +5m placement, graybox re-enable), rebuild idempotence and GUID preservation are asserted, source FBX is byte-frozen with SHA256, route and PlayMode evidence match, and the Windows participant proof plus its negative control both behave correctly. The only open evidence-integrity risk is staging scope (finding 1), and the plan already names the whitelist + negative control as the next step — that gate must pass as specified, with the scene-diff check from finding 1 added.

Ship, conditional on the staged-scope negative/positive controls passing exactly as described, including the scene-only-delta diff.

FINAL_REVIEW: ship
