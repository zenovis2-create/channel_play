# Khufu V12 Queen Circuit Test Plan

| Gate | Pass condition |
| --- | --- |
| Prewrite audit | Scene bytes unchanged; 10 V4 Queen targets; V10/V11 states and hashes exact. |
| Python mutations | Baseline, audit count/state, classification, budgets, and frozen hashes fail closed. |
| Static | Exact hierarchy, five renderers, bounded colliders, mesh derivation, pairs, clearance, enclosure, and transitions pass. |
| Idempotence | Two rebuilds produce identical scene, generated-asset, and validator signatures. |
| Negative controls | Gate/ramp/service-frame restore, V4 overlap restore, pair drift, enclosure removal, and `SetActive(false)` are rejected. |
| Rollback | Injected failure restores both bindings, both gate flags, all V4 states, assets, and scene bytes. |
| Legacy | Original V4–V11 validators pass with exact later-root detachment/restored bindings and scene equality. |
| Captures | Six fresh 1600x1000 PNGs pass hashes, dimensions, uniqueness, and manual semantic review. |
| Player normal | All serialized anchors reached and returned; max/final error <=0.40 m; grounded >=0.90; no Queen gate hit. |
| Player control | Start >=1.5 m outside; pre-Move overlap empty; <=0.1 m steps; same-frame `Sides` and exact callback collider. |
| Shaft boundary | Controller-sized overlap/cast cannot enter either narrow mouth. |
| Build | Windows development build has zero errors and binds scene, source, assembly, and output hashes. |
| Clean index | Dependency-closed staged export imports and validates in Unity 6000.0.76f1. |
| Release | Opus final review, resolution, exact allowlist, staged convergence, commit, and post-commit inventory pass. |

Negative controls also reject V12 ownership of `V4_Glow_Queens`; the builder must fail on that
drift instead of repairing it.
