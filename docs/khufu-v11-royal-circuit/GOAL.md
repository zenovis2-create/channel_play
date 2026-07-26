# Khufu V11 Royal Chamber Circuit Goal

## Intent

Turn V10's upper ownership boundary into a coherent, inspectable royal-suite destination without
breaking the accepted exterior, temple, causeway, entry, or Grand Gallery work.

## Completion Surface

| ID | Class | Requirement |
| --- | --- | --- |
| V11-R-001 | FACT | The traversable order is Great Step, short entry, antechamber, King's Chamber. |
| V11-R-002 | FACT/HYBRID | The King's Chamber reads as a red-granite east-west room containing a granite sarcophagus. |
| V11-R-003 | FACT/HYBRID | The antechamber reads through granite lining, three portcullis-track positions, and low passages; all player clearances are adapted. |
| V11-R-004 | FACT/DISPLAY | Five stacked spaces and the upper gabled roof are legible above the King's Chamber, but are not a public traversal route. |
| V11-R-005 | FACT | The King's Chamber's two narrow shaft mouths remain boundary recesses and are not enlarged into routes. |
| V11-R-006 | HYBRID | Route inlay and selective cutaway lighting are clearly presentation devices, not archaeological claims. |
| V11-R-007 | ENGINEERING | V10 source meshes remain untouched; V11 owns reversible open-boundary variants and exact binding transitions. |
| V11-R-008 | ENGINEERING | Every structural visual spec with collision owns a named transform/collider pair. |
| V11-R-009 | ENGINEERING | V11 rebuild is idempotent and leaves V8, V9, and V10 evidence signatures unchanged except the declared V10 open-boundary bindings. |
| V11-R-010 | ENGINEERING | The normal route has no collider blocker at the Great Step, antechamber, or King's Chamber entry. |
| V11-R-011 | VISUAL | Captures prove long-axis continuity, portcullis detail, chamber identity, sarcophagus placement, stacked-chamber cutaway, and full-pyramid integration. |
| V11-R-012 | PERFORMANCE | The V11 root and complete map remain inside `performance-budget.json`. |
| V11-R-013 | PROCESS | Completion, deferred work, and unverified surfaces are reported separately. |

## False-Completion Conditions

V11 is not complete if any condition below is true:

1. The old Great Step wall or granite bars visually or physically block the new route.
2. A V10 source mesh asset is overwritten instead of using a V11-owned variant.
3. The relieving stack is presented as a normal historic visitor corridor.
4. A shaft mouth is widened into a player passage or given an unsupported purpose.
5. Static metrics pass while direct captures show opaque walls, floating geometry, exterior leaks,
   unreadable darkness, or section mass that makes the pyramid look hollow.
6. Rebuilding changes the scene or generated-asset signature after the first stable write.
7. Unity import, compilation, static gates, or required captures are not run and the result is still
   called complete.

## Deferred

- Queen's Chamber production art and horizontal passage.
- Descending route and Subterranean Chamber.
- ScanPyramids anomalies.
- Global lighting, cinematic VFX, production audio, and fresh-player usability study.

