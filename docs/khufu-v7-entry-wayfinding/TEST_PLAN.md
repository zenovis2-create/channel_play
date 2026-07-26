# Test Plan

| ID | Surface | Pass condition |
| --- | --- | --- |
| V7-T-001 | Camera synthetic | Wall and two exact pylons hide; unrelated pylon stays visible; all restore. |
| V7-T-002 | Static validation | V7 is 8 renderers, 192 vertices, 96 triangles, 0 colliders. |
| V7-T-003 | Idempotence | Two rebuild signatures and metrics match. |
| V7-T-004 | Off-route mutation | Moving guide 01 by +3m Z is rejected, then restored. |
| V7-T-005 | V5 Gate 4 | 6/6 objectives, 415 clearance samples, 8/8 hub proxies. |
| V7-T-006 | PlayMode | V5 CharacterController traversal passes on the final scene. |
| V7-T-007 | Normal player | Player in frame, guides >=2, center route clear, exact pylon cutaway >=1. |
| V7-T-008 | Pylon mutation | Renamed pylon remains visible, center route is blocked, proof fails as expected. |
| V7-T-009 | Performance | V5 budget validator passes final raw profiler data and both screenshots. |
| V7-T-010 | Aggregate | Frozen inputs, bindings, docs, Fable decision, and staged scope all pass. |

Unit mutation tests additionally reject stale scene hashes, missing off-route evidence, false route-center
success, corrupted binding hashes, and duplicate Fable ship decisions.
