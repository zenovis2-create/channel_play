# Test Plan

| Gate | Surface | Passing Evidence |
| --- | --- | --- |
| V6-T-001 | Frozen inputs | Nine baseline SHA256 values reproduce exactly |
| V6-T-002 | Unity static validation | `V6_VALIDATION: passed`; 11 renderers, 520 vertices, 404 triangles, 0 colliders |
| V6-T-003 | Rebuild idempotence | Matching visual signatures and metrics across two rebuilds |
| V6-T-004 | Visual delta | Four valid 1536x1024 captures; required Hub and dense-core ROI/global deltas pass |
| V6-T-005 | V5 static regression | 6/6 objective permutations, 415 clearance samples, 8/8 hub proxies |
| V6-T-006 | V5 PlayMode regression | 1,758.6 m, 3,533 steps, maximum controller error 0.338 m |
| V6-T-007 | Windows build | StandaloneWindows64 Development Player, one scene, 0 errors, settings restored |
| V6-T-008 | Visible performance | 1536x1024 Ultra/D3D11, 3,594 samples, all frozen V5 limits pass |
| V6-T-009 | Aggregate validator | Current scene/source/output hashes and all required markers pass |
| V6-T-010 | Mutation suite | Ten pass/mutation tests, including stale capture, PlayMode, build, and performance scene bindings |
| V6-T-011 | External review | Fable final review contains exactly `FABLE_VERDICT: ship` |

## Commands

```powershell
python -m unittest tools.tests.test_validate_khufu_v6_visual_slice -v
python tools/validate_khufu_v6_visual_slice.py
```

Unity checks are invoked through the public methods in the V6 Editor scripts. Their logs and compact
receipts live under `runs/khufu-v6-visual-slice/`; raw Unity logs are diagnostic, not acceptance
markers.
