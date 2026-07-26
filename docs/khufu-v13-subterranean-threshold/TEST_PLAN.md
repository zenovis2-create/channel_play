# Khufu V13 Subterranean Threshold Test Plan

| Gate | Pass condition |
| --- | --- |
| Prewrite | HEAD and scene SHA match V12; contracts freeze signature/metrics, 13 targets, observations, exclusions, and budgets. |
| Python mutations | Commit/scene, signature/metrics, target count/path/state, `SetActive(false)`, pair state, pit collider, marker/glow/light state, classification, exclusions, and budgets fail closed. |
| Unity audit | Scene bytes unchanged; 13 exact targets are active with original transforms; 12 colliders are enabled/non-trigger; pit has no collider; V10-owned visuals and inherited light are exact. |
| Static | Root name, five renderer buckets, 20 non-trigger colliders, structural pairs, clearance, slope, enclosure, pit backing, and transitions pass. |
| Idempotence | Two rebuilds produce identical scene, generated-asset, validator, and V13 static signatures. |
| Negative controls | Component re-enable, `SetActive(false)`, pair drift, ceiling removal, marker movement, predecessor-state drift, and injected failure are rejected. |
| Rollback | Injected failure restores all 13 target states, V10-owned states, generated files, and scene bytes. |
| Legacy | Original V4-V12 validators pass with V13 detached and exact required predecessor contexts restored. |
| Player normal | Branch-to-chamber round trip reaches every anchor with error `<=0.40 m` and grounded ratio `>=0.90`. |
| Player control | Start `>=1.5 m` outside, overlap empty, step `<=0.1 m`, with same-frame `Sides` and exact callback. |
| Pit | Controller-sized overlap and cast prove solid, non-traversable backing beneath the visual. |
| Captures | Six fresh 1600x1000 PNGs pass hashes, dimensions, uniqueness, and semantic review. |
| Build | Windows Development Player has zero errors and binds scene, source, assembly, and output hashes. |
| Clean index | Dependency-closed alternate-index export imports and validates without changing the main index/object store. |
| Release | External review, exact allowlist, staged convergence, commit, and post-commit inventory pass. |

Required captures are `v10_v13_junction.png`, `descending_long_axis.png`,
`bedrock_landing.png`, `chamber_doorway_release.png`, `subterranean_chamber_pit.png`, and
`below_grade_integration.png`.
