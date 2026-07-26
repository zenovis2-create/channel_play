# Khufu V13 Subterranean Threshold Goal

## Intent

Replace the remaining V4 descending-bedrock, subterranean-level, and chamber blockout with one
bounded below-grade route. The slice begins at the accepted V10 branch, descends through bedrock,
reaches a fully enclosed Subterranean Chamber, and supports a same-route return.

## Completion Surface

| ID | Class | Requirement |
| --- | --- | --- |
| V13-R-001 | FACT/HYBRID | The descending and level passages preserve their factual relationship while using project-scale player clearance. |
| V13-R-002 | FACT/HYBRID | The conventionally named Subterranean Chamber reads as an unfinished bedrock space without assigning a purpose. |
| V13-R-003 | ENGINEERING | V13 disables exactly 13 audited V4 renderers and the 12 colliders that exist on those targets; all GameObjects and transforms remain intact. |
| V13-R-004 | ENGINEERING | V10-owned route markers and glows remain disabled, and `V4_Light_Subterranean` remains enabled as an inherited dependency. |
| V13-R-005 | GAMEPLAY | A real `CharacterController` travels from the V10 branch to the chamber and returns by the same route. |
| V13-R-006 | COLLISION | Three enclosed passage shells and one chamber shell own exactly 20 non-trigger colliders; the unfinished-pit presentation has a solid, non-traversable backing. |
| V13-R-007 | VISUAL | Six fresh captures prove the junction, descent, landing, doorway, chamber/pit, and full below-grade integration. |
| V13-R-008 | REGRESSION | Original V4-V12 gates pass under exact V13 detachment or restored predecessor context. |
| V13-R-009 | PROCESS | Prewrite, idempotence, negative controls, rollback, built-player, clean-index, review, and release gates fail closed. |

## False Completion

V13 is incomplete if it starts from the obsolete V4 branch height, moves an inherited marker,
owns a V10-disabled glow/route renderer, makes the pit traversable, removes a target GameObject,
exceeds the exact component budget, introduces a ScanPyramids or fictional route claim, or relies
on stale Editor-only evidence.

## Deferred

ScanPyramids anomalies, SP-BV, SP-NFC, the Well Shaft, Underworld/Earth-key fiction, global
lighting, VFX, production audio, enemies, objectives, and fresh-player usability remain outside
this slice.
