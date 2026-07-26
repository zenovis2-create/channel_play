# Fable Plan Recheck: Khufu V10 Interior Spine

Decision needed:

Do the implemented pre-write corrections close the blockers from the first plan critique well enough
to begin V10 scene implementation?

## First Review

The first review returned `FABLE_PLAN_VERDICT: revise` with six findings: per-segment truth/scale
classification, HYBRID return distinction, exact disable manifest, deterministic enclosure metric,
byte-identical mesh regeneration, and visible Great Step boundary.

## Corrections Applied Before Scene Write

1. `segment-classification.json` now classifies eight segments. Entrance, passages, Grand Gallery,
   Queen threshold, and Great Step explicitly separate factual relationships/features from HYBRID
   length, angle, width, height, and collision scale. Approximate ratios are frozen.
2. Runtime vocabulary forbids `Well Shaft`. The non-traversable factual aperture is
   `Historic_Service_Mouth`; the spatially separated adapted path is `HYBRID_Service_Return` with a
   distinct material and in-scene evidence marker.
3. A Unity read-only audit generated `disable-manifest.json` from the actual scene. It contains
   exactly 45 renderer and 39 collider transitions, snapshots all eight V4 route markers, records 42
   V5 Crown dependencies, and proves intersection count zero. Scene SHA256 remained
   `0af39f99386da722f228611e0482cee46f9dfba2b57b00e6a791fc7c7fe3e346`.
4. Gallery enclosure is frozen as 24 route samples x 24 bounded upper-hemisphere rays. At least 75%
   must hit V10 structure within 4.5m, with lateral and overhead hits at every sample.
5. Idempotence requires byte-identical generated mesh files and stable meta/GUID files across two
   rebuilds, plus identical scene hash.
6. Great Step receives a visible diegetic boundary; invisible blocker-only treatment cannot pass.
7. V4-V9 builder source, V5 Crown route, Queen/King/Subterranean geometry, and scan anomalies remain
   untouched. No V10 scene root has been written yet.

## Evidence

- Unity audit token: `KHUFU_V10_PREWRITE_AUDIT: passed`.
- Manifest: 45 renderers, 39 colliders, 8 markers, Crown intersection 0.
- Contract JSON files parse successfully; document diff check passes.
- External research is restricted to Egyptian Ministry, Harvard Digital Giza survey records,
  Miatello, and peer-reviewed Nature/Scientific Reports sources.

What would change implementation:

A remaining blocker would change the classification table, exact transition set, enclosure metric,
or route topology before any scene save. Non-blocking polish can be deferred to final review.

Return concise prioritized findings and end with exactly one line:

`FABLE_PLAN_VERDICT: proceed`

or

`FABLE_PLAN_VERDICT: revise`
