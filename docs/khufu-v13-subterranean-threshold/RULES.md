# Khufu V13 Subterranean Threshold Rules

1. The immutable baseline commit is `787476b58044e78f0c5164df408680e50fee47a2`; its scene SHA256
   is `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`.
2. The accepted V12 static signature is
   `6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd`.
   V12 root metrics are `5/1176/588/22`; map metrics are `834/67070/48560/589`
   (renderers/vertices/triangles/colliders).
3. No Unity scene or asset write is allowed until a read-only audit and
   `tools/validate_khufu_v13_prewrite.py` both pass.
4. V13 owns exactly five renderers and 20 non-trigger colliders. Because disabled components
   remain counted, final map component totals are exactly 839 renderers and 609 colliders; the
   map collider ceiling is 612.
5. V13 owns exactly the 13 V4 targets in `segment-classification.json`: 12 renderer/collider pairs
   and one renderer-only unfinished-pit visual.
6. Target transitions are component-only. Deletion, reparenting, transform edits, and
   `SetActive(false)` are forbidden; rollback restores every predecessor component state.
7. `V4_Glow_Descending`, `V4_Glow_Subterranean`, `V4_Route_Subterranean_Approach`, and
   `V4_Route_Subterranean_Chamber` remain V10-owned disabled renderers. V13 asserts but never owns
   or restores them.
8. The V4 branch marker remains `(-2.5, 1.2, -18.3)`, the V10 branch anchor remains
   `(-2.5, 3.8, -19.2)`, the approach marker remains `(0, -3.8, -5.6)`, and the chamber marker
   remains `(1, -3.6, 1.5)`.
9. `V4_Light_Subterranean` remains enabled as an inherited dependency and is disclosed in captures.
10. Every structural visual has one named collision proxy. Missing, extra, trigger, disabled, or
    misaligned proxies fail closed.
11. The chamber is enclosed in six directions except for its declared doorway. Pit overlap/cast
    evidence must prove a solid non-traversable floor.
12. Built-player traversal requires maximum/final anchor error `<=0.40 m` and grounded ratio
    `>=0.90` in both directions.
13. Boundary control starts at least 1.5 m outside the wall, has an empty pre-Move overlap set,
    moves at most 0.1 m per frame, and records same-frame `Sides` plus the exact callback name.
14. ScanPyramids/void work, Well Shaft claims, Underworld/Earth-key fiction, and global polish are
    forbidden scope expansions.
15. A predecessor rebuild is incomplete until V13 is rebuilt and validated in canonical context.
