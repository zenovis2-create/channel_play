# Khufu V5 Live Status and Evidence

Updated: 2026-07-11
Current gate: `KV5-G-007 Final Acceptance`
Gate verdict: in progress; Fable and cold-reader pass, while scoped commit and final receipt remain
Unity implementation: V5 authored map, runtime binding, visual proof, and Windows profile implemented
Baseline commit: `a31905297cae2d7e2d83ababab54b109460cfbe2`
Implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with accepted evidence
- `[!]` blocked with reason and evidence where available

No phase-level bulk completion is allowed. Each `[x]` line requires its own `evidence: KV5-E-NNN`.

## Current Decision

Hold the accepted `KV5-D-011` Windows performance budget, `KV5-D-012` V5-specific simulation
surface, and `KV5-D-013` build-input binding. Bind every final claim to implementation commit
`81c28f84d61d875a54f39d3fc74b202319103e24` before requesting Fable ship review.

## Gate Board

- [x] `KV5-G-000` Harness Ready; evidence: KV5-E-009
- [x] `KV5-G-001` Coordinate Lock; evidence: KV5-E-010
- [x] `KV5-G-002` Authored Graybox; evidence: KV5-E-014
- [x] `KV5-G-003` Gameplay Integration; evidence: KV5-E-014
- [x] `KV5-G-004` Traversal and Social Play; evidence: KV5-E-014
- [x] `KV5-G-005` Art and Truth Language; evidence: KV5-E-015
- [x] `KV5-G-006` Performance and Regression; evidence: KV5-E-016
- [~] `KV5-G-007` Final Acceptance

## Gate 0 Work Items

- [x] Create and cross-link the six harness documents; evidence: KV5-E-004
- [x] Implement content-aware harness validation; evidence: KV5-E-003
- [x] Run validator unit and integration tests; evidence: KV5-E-003
- [x] Generate revision-bound Gate 0 pre-review receipt; evidence: KV5-E-004
- [x] Complete cold-reader audit; evidence: KV5-E-006
- [x] Complete Fable final review and apply blocking findings; evidence: KV5-E-007
- [x] Generate final working-tree validation receipt; evidence: KV5-E-008
- [x] Obtain user authorization for the scoped harness commit; evidence: KV5-E-009
- [x] Commit the freeze set and pass `--require-committed`; evidence: KV5-E-009
- [x] Freeze Gate 0 and begin Coordinate Lock; evidence: KV5-E-009

## Gate 1 Work Items

- [x] Inspect V4 builder, scene bootstrap, runtime cache, operator bounds, and validators; evidence: KV5-E-010
- [x] Score the implementation loop contract at 80 or higher; evidence: KV5-E-010
- [x] Freeze district roots, bounds, coordinates, evidence classes, and key/terminal/exit positions; evidence: KV5-E-010
- [x] Freeze route-marker order, loop/shortcut markers, and validation thresholds; evidence: KV5-E-010
- [x] Record target-machine identity and baseline performance procedure; evidence: KV5-E-016
- [x] Run architecture and QA sidecar reviews; evidence: KV5-E-010
- [x] Commit Coordinate Lock and implementation evidence; evidence: KV5-E-014

## Implementation Work Items

- [x] Preserve the V4 dense core and build eleven independent V5 district roots; evidence: KV5-E-014
- [x] Pass six physical-key permutations, terminal confirmation, and extraction flow; evidence: KV5-E-014
- [x] Traverse critical and three key routes with an actual CharacterController; evidence: KV5-E-014
- [x] Pass collision, shortcut, route-time, and eight-proxy hub checks; evidence: KV5-E-014
- [x] Record the simulated-roster social rehearsal and per-key public/private review; evidence: KV5-E-018
- [x] Pass static 1536x1024 and PlayMode UI visual review; evidence: KV5-E-015
- [x] Build the Windows Development Player with zero errors; evidence: KV5-E-016
- [x] Freeze and pass the visible-window Windows performance budget; evidence: KV5-E-016
- [x] Revalidate the V4 contract with a focused comparison and hierarchy snapshot; evidence: KV5-E-017
- [x] Pass `channelctl` batch compile and generic playtest with the accepted V5 probe substitution; evidence: KV5-E-019
- [x] Commit the implementation closure without unrelated worktree files; evidence: KV5-E-014

## Gate 7 Work Items

- [x] Add `RULES.md` to the required harness set and rerun fail-closed tests; evidence: KV5-E-020
- [x] Obtain implementation-level external Fable review ending in `FABLE_VERDICT: ship`; evidence: KV5-E-021
- [x] Run a fresh cold-reader audit from README alone; evidence: KV5-E-022
- [ ] Commit Gate 7 evidence without unrelated worktree files.
- [ ] Pass the final harness receipt in `--require-committed` mode.

## Blockers

- No technical implementation blocker. Gate 7 release acceptance remains open until the scoped
  evidence commit and committed final receipt exist.

## Next Action

Commit the scoped Gate 7 evidence without unrelated worktree files, then create and verify the
final committed-mode harness receipt.

## Evidence Ledger

Ledger rows are append-only. Corrections add a new row and mark the old row superseded in Notes.

| Evidence ID | Requirements / tests | Revision | Command or procedure | Verdict | Artifact | Timestamp | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KV5-E-001 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable plan-critique wrapper, first call | failed | ../../work/fable-harness/khufu-v5-plan-critique.fable.md | 2026-07-10 | Invalid tool-call warning; never acceptable for a gate. |
| KV5-E-002 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable plan-critique wrapper, tightened retry | revise | ../../work/fable-harness/khufu-v5-plan-critique.retry.fable.md | 2026-07-10 | Valid critique; required six docs and a content-aware validator. |
| KV5-E-003 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | `python -m unittest tools.tests.test_validate_khufu_v5_harness -v` | passed | ../../runs/khufu-v5-harness-20260710-gate0/unit-tests.txt | 2026-07-10 | Nine tests cover the valid harness and fail-closed mutations at the pre-review snapshot. |
| KV5-E-004 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | `python tools/validate_khufu_v5_harness.py --root . --receipt runs/khufu-v5-harness-20260710-gate0/pre-fable-receipt.md` | passed | ../../runs/khufu-v5-harness-20260710-gate0/pre-fable-receipt.md | 2026-07-10 | Historical pre-review receipt; embedded hash matches this evidence revision. |
| KV5-E-005 | KV5-R-012 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba | Fable final review, first pass | revise | ../../work/fable-harness/khufu-v5-final-review.fable.md | 2026-07-10 | Found token parsing, fail-closed test, and durable-freeze gaps. |
| KV5-E-006 | KV5-R-014 / KV5-T-016 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | Cold-reader section of Fable final review | passed | ../../work/fable-harness/khufu-v5-final-review.fable.md | 2026-07-10 | Contains `COLD_READER: passed` and correct five-field answers at the reviewed snapshot. |
| KV5-E-007 | KV5-R-012, KV5-R-014 / KV5-T-014 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:7f7620287dc02dedd8ad8ebb965dc739386a6f08c787cff35968ef13d7e76b2d | Fable final-review retry after blocking fixes | accepted | ../../work/fable-harness/khufu-v5-final-review.ship.fable.md | 2026-07-10 | Final non-empty line is exactly `FABLE_VERDICT: ship`; reviewed the 7f7620 snapshot. |
| KV5-E-008 | KV5-R-010, KV5-R-014 / KV5-T-001 | HEAD:2d6dbebdc5c572c8d59572134026165c7dfee8ba+ARTIFACT:26e66cbbdfcfb86750bb7e3554bc39d8006daa3b88ae11c466667f5d3d9edaf3 | `python tools/validate_khufu_v5_harness.py --root . --receipt runs/khufu-v5-harness-20260710-gate0/final-working-tree-receipt.md` | passed | ../../runs/khufu-v5-harness-20260710-gate0/final-working-tree-receipt.md | 2026-07-10 | Historical working-tree acceptance before commit freeze. |
| KV5-E-009 | KV5-R-013, KV5-R-014 / KV5-T-001, KV5-T-015 | COMMIT:a31905297cae2d7e2d83ababab54b109460cfbe2+ARTIFACT:26e66cbbdfcfb86750bb7e3554bc39d8006daa3b88ae11c466667f5d3d9edaf3 | `python tools/validate_khufu_v5_harness.py --root . --receipt runs/khufu-v5-harness-20260710-gate0/final-working-tree-receipt.md --require-committed` | accepted | ../../runs/khufu-v5-harness-20260710-gate0/committed-freeze.txt | 2026-07-10 | Scoped freeze set is committed and committed-mode validation passed. |
| KV5-E-010 | KV5-R-010, KV5-R-013 / KV5-T-003, KV5-T-004, KV5-T-006, KV5-T-009 | HEAD:a31905297cae2d7e2d83ababab54b109460cfbe2+ARTIFACT:e9f6f6c8c99f2168e18c9dd32199b2aa0e40826eb2cf3aca79a3502f7db08db6 | Architecture and QA sidecar reviews plus loop-contract scoring | passed | ../../work/khufu-v5/IMPLEMENTATION_LOOP.md | 2026-07-10 | Loop contract scored 100; reviews require explicit map bindings, V4-first rebuild, authored reset transforms, V5-specific structural and gameplay proof. |
| KV5-E-011 | KV5-R-001, KV5-R-002, KV5-R-003, KV5-R-004, KV5-R-005 / KV5-T-003, KV5-T-004, KV5-T-005 | HEAD:a31905297cae2d7e2d83ababab54b109460cfbe2+ARTIFACT:4e9a62e83bc3e48e2ab8b019fc796d042f655d0f9e07da43af7729e32de01582 | Unity menu `Channel Play/Khufu V5/Rebuild Validate Render` | passed | ../../runs/khufu-mega-labyrinth-v5/validation.md | 2026-07-10 | Scene contains 11 districts, six loops, three shortcuts, preserved V4, evidence tags, and a 746.2 m marker route. Controller traversal is not yet proven. |
| KV5-E-012 | KV5-R-006, KV5-R-008, KV5-R-010 / KV5-T-006, KV5-T-009, KV5-T-011 | HEAD:a31905297cae2d7e2d83ababab54b109460cfbe2+ARTIFACT:60512d267c1e339acffa7c7973d6aa1bdaf8b91c4ae6f2f5bd7dc43c8ce7a215 | Unity MCP Play Mode startup and error-console inspection | passed | ../../runs/khufu-mega-labyrinth-v5/runtime-smoke.md | 2026-07-10 | Authored bindings start with zero Unity errors. Key permutations, terminal recognition, extraction traversal, and operator coverage remain unverified. |
| KV5-E-013 | KV5-R-007 / KV5-T-012 | HEAD:a31905297cae2d7e2d83ababab54b109460cfbe2+ARTIFACT:9c6e13e9ef579050e8294a366fe430cd4c9f8677b5d1d5881d0028d2859b8bd9 | Deterministic V5 RenderTexture capture export and human inspection | revise | ../../runs/khufu-mega-labyrinth-v5/captures/manifest.md | 2026-07-10 | Six non-empty hashed captures exist; graybox density improved, but final art/readability acceptance is not granted. |
| KV5-E-014 | KV5-R-001, KV5-R-002, KV5-R-003, KV5-R-004, KV5-R-005, KV5-R-006, KV5-R-007, KV5-R-008, KV5-R-010, KV5-R-013 / KV5-T-003, KV5-T-004, KV5-T-005, KV5-T-006, KV5-T-007, KV5-T-008, KV5-T-009, KV5-T-010, KV5-T-011 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:af045dc5671440610dfe296a1cb1cee95b3f277edece4b9952c6ba6a1d040cac | Unity `Run Gate 4 Acceptance` plus committed post-check `Run PlayMode Probe` | accepted | ../../runs/khufu-mega-labyrinth-v5/gate4-final.md | 2026-07-11 | Supersedes E011/E012 for completion; 6/6 permutations, 1758.6 m CharacterController traversal, 415 clearance samples, eight hub proxies, and zero Unity errors. |
| KV5-E-015 | KV5-R-001, KV5-R-008, KV5-R-011, KV5-R-013 / KV5-T-002, KV5-T-009, KV5-T-012 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:f9a20fb0e99c65f8e43e32b2b94f0481b2de3b787ae1628c7e1eb8db7d16d539 | Static eight-view export, PlayMode UI capture, and local visual inspection | accepted | ../../runs/khufu-mega-labyrinth-v5/visual-review.md | 2026-07-11 | Supersedes E013; truth labels, dense core, landmarks, underworld cutaway, full operator map, and non-overlapping UI passed. |
| KV5-E-016 | KV5-R-009, KV5-R-010, KV5-R-013, KV5-R-014 / KV5-T-001, KV5-T-010, KV5-T-013, KV5-T-015 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:716316e8f4c0c9c92590bb59ff3ee9febe7d2d2e9b169c6cc9ce2a763d9e8731 | Windows Development Player build, visible baseline, frozen budget, independent final profile, and fail-closed validator | accepted | ../../runs/khufu-mega-labyrinth-v5/gate6-acceptance.md | 2026-07-11 | 3580 final samples; p95 frame 8.337 ms, main 2.401 ms, render 2.794 ms, GPU 2.240 ms; performance and harness tests 14/14 passed. |
| KV5-E-017 | KV5-R-002, KV5-R-013 / KV5-T-003, KV5-T-015 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:92345258c8b0698add6d1d6b518e891ce2f93d03bc2021397983ed2ae730a754 | Unity V4 validator, pre/post contract comparison, and live hierarchy snapshot | accepted | ../../runs/khufu-mega-labyrinth-v5/v4-regression.md | 2026-07-11 | Pre-V5 and post-implementation metrics match: 217 core blocks, 14 corbels, five relieving chambers, eight casing panels, and zero envelope violations. |
| KV5-E-018 | KV5-R-007, KV5-R-014 / KV5-T-007, KV5-T-008 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:00f40ee086de8628610e62502244c98c154e74958476aa5b2777273958e8adfa | Named local reviewer plus committed controller replay, hub snapshot, captures, and per-key review form | accepted | ../../runs/khufu-mega-labyrinth-v5/social-rehearsal.md | 2026-07-11 | Pass is limited to the simulated eight-state roster; reviewer is explicitly not represented as a human multiplayer participant. |
| KV5-E-019 | KV5-R-005, KV5-R-006, KV5-R-010, KV5-R-013 / KV5-T-010, KV5-T-011, KV5-T-015 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:2315d6f2e8d48f3a724a2eab782399d6da3bf613d2fd29fbef03530011c22a29 | `channelctl unity check --batch`, generic playtest, fail-closed V2 applicability run, and `KV5-D-012` V5 replacement | accepted | ../../runs/khufu-mega-labyrinth-v5/channelctl-validation.md | 2026-07-11 | Batch compile exit 0/errors 0; generic playtest 15/15. V2 sim failed on the intentionally absent root and is not mislabeled; V5 Gate 4/PlayMode receipts provide the accepted route proof. |
| KV5-E-020 | KV5-R-009, KV5-R-010, KV5-R-013, KV5-R-014 / KV5-T-001, KV5-T-010, KV5-T-013, KV5-T-015 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:25a84780a5807e174f42e7da20427b1857f191b982dead9a56bd509d2a54c058 | Close Fable conditions with `KV5-D-012` assertion map, `KV5-D-013` build binding, required RULES, and fail-closed tests | accepted | ../../runs/khufu-mega-labyrinth-v5/gate7-remediation.md | 2026-07-11 | Build inputs remain unstaged but hash-bound; missing manifest, changed input, bad Fable metadata, and missing RULES fail. Focused suites pass 18/18. |
| KV5-E-021 | KV5-R-012, KV5-R-014 / KV5-T-014 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:40071ceccf26da41a5dea1e88876a084704a50fd08bdfcc00569a3be39a6314f | External Fable implementation final review through `codex-fable-harness` | accepted | ../../work/fable-harness/khufu-v5-implementation-final-review.fable.md | 2026-07-11 | Wrapper exit 0, warnings empty, output validation passed, and final non-empty line is exactly the ship verdict. Conditions are closed by E020; final cold-reader/committed receipt remain mandatory. |
| KV5-E-022 | KV5-R-014 / KV5-T-016 | COMMIT:81c28f84d61d875a54f39d3fc74b202319103e24+ARTIFACT:9307a4164f29e0837c7297f93abcc6bf5195b7283dd2324a7634ae1a33e3846e | Fresh isolated reviewer reads README only and answers the five cold-reader fields | accepted | ../../runs/khufu-mega-labyrinth-v5/cold-reader-final.md | 2026-07-11 | Reviewer identified decision, phase, next action, blocker, and proof within five minutes and reported no ambiguity. |

## Unresolved

- Real multiplayer remains outside the current goal.
- The social rehearsal proves only the simulated roster contract; no human networked balance claim
  is made.

## Unverified

- Final scoped evidence commit and committed harness receipt do not yet exist for implementation
  commit `81c28f84d61d875a54f39d3fc74b202319103e24`.
