# Status

Current decision: **ship**.

## Completed

- NotebookLM deep research completed with 75 sources and an implementation-focused synthesis.
- Unity source audit passed for the 16,090,700-byte FBX.
- Source metrics measured: 2,583 transforms, 2,565 renderers, 379,938 vertices, 333,700 triangles,
  0 colliders, 4 lights, and 6 cameras.
- Direct full-FBX placement was rejected because the accepted V7 scene already contains 803 renderers.
- Historically unsupported deep-maze, burial, trap, and duplicate pyramid-cap geometry was removed from V8 scope.
- Fable plan critique returned `PLAN_CRITIQUE: revise` with a required read/write spike, combined-count dry run,
  route-clearance check, and exact graybox-renderer count assertions; the corrected review returned
  `PLAN_CRITIQUE: proceed`.
- The no-save spike passed with ModelImporter Read/Write disabled; FBX and `.meta` hashes were unchanged.
- The selector chose 255 source renderers and combined them in memory into 9 buckets, 33,378 vertices, and
  27,540 triangles with zero forbidden donor objects.
- The final tightened selector excludes route-crossing door/podium/stair donors and freezes 245 source renderers,
  9 buckets, 32,110 vertices, and 26,460 triangles.
- Final V8 root, static/idempotence/mutation gates, V5 Gate 4, 1,758.6m PlayMode traversal, Windows player
  normal/mutation proofs, and the 35-second performance budget all passed.
- The final scene is hash-bound at `4f15673e1de7eeb9f92dbfa058c40ae263549449c9ee2c5b98b59c7161a5d32f`.
- Fable final review returned `FINAL_REVIEW: ship` conditional on staged-scope and semantic scene-delta checks.
- HEAD-to-current semantic scene scope passed: unchanged non-V8 name/component ownership, exactly five V5 plus
  eleven V6 renderer state changes, and ten enabled V8 renderers.
- The out-of-scope negative control rejected `Packages/manifest.json` as expected.
- The explicit V8 staged whitelist and semantic index validation passed with zero out-of-scope files.
- Canonical YAML comparison proved all 4,043 pre-existing scene documents unchanged apart from the allowed
  sixteen renderer `m_Enabled` transitions and one V8 child reference; all 64 added documents are V8-owned.
- Scene-scope comparison is pinned to V7 baseline commit `d8e4af4b172cebc3de56210efc04def543a82e3b`
  and verifies the baseline scene SHA-256 before comparison.

## Pending

- None inside the V8 acceptance scope.

## Deferred

- Off-route visible/collider fidelity beyond the validated causeway corridor remains owned by the V5 gameplay
  collision scaffold and needs a later full-map art/collision pass.
- The wider map still needs full production art, baked lighting, LODs, VFX, audio, and fresh-player usability testing.
