The plan file tool isn't available in this context, so here is the review directly.

# Khufu V11 Release Plan Critique

**Verdict: Revise.** The sequencing spine is right. But the plan's central visual diagnosis is wrong, its release-inventory mechanism is weaker than the V10 precedent already sitting in this repo, and two evidence classes required by V11's own contract are missing from the plan entirely.

---

## 1. Blocking findings, priority order

**B1 — `great_step_open_axis.png` does not evidence the claim V11 exists to make.** Direct inspection: portcullis piers fill the left half, a continuous granite wall fills the right, and no opening recedes along the route. `GOAL.md:30` false-completion condition 1 is precisely "the old Great Step wall or granite bars visually or physically block the new route," and `GOAL.md:22` (V11-R-011) requires proof of long-axis continuity. This image cannot distinguish "open" from "blocked 3 m further on." It is the most load-bearing capture in the set and it is currently non-probative — this outranks the integration view, which your plan treats as the only likely blocker.

**B2 — The integration-view diagnosis in step 4 is incorrect; the real defect is different.** Direct inspection contradicts the premise. The pyramid does **not** read hollow: a full brick-textured section mass fills the cutaway behind the two casing wings, supplied by the already-retained `V4_Smooth_Casing_With_Tapered_Cutaway` and `V4_Foundation_Bedrock_Cutaway`. Art rule 4 (`RULES.md:30`) is satisfied as captured. What actually fails condition 5 is **floating geometry**: an angled tan element hangs below-right of the suite with no visible support, and the suite is a small off-center inset clipped at the right edge by the casing wing. Cause: `CaptureVisibilityScope.Apply` (exporter `:333-349`) hides every map child except V11 and V4, so the V11 limestone entry passage terminates in mid-air where V10's gallery should meet it.

Adding `V4_Section_Poche` fixes neither symptom. Per `ChannelPlayPyramidReferenceMatchedV4Builder.cs:191-207` it is a single double-sided quad (`V4_Section_Poche_Filled_Mass`, 4 verts) sloping from `z≈26.5 @ y=0` to `z≈4.45 @ y=28.7` — a thin backdrop plane behind the suite, and mass is not what is missing.

**B3 — Release-inventory control is a regression from V10 and will not hold.** Step 6 proposes prose in `STATUS.md`. Against 44 modified + 958 untracked entries that is not a gate. V10 already shipped the right mechanism: `docs/khufu-v10-interior-spine/staging-allowlist.txt` (164 explicit paths) plus `tools/validate_khufu_v10_release.py`, which rejects unexpected staged paths (`:519`), allowlisted-but-unstaged (`:522`), staged-with-extra-unstaged-delta (`:530`), and dirty paths outside the allowlist (`:526`), writing a hashed `staged-inventory.json` (`:462`). V11 has only a 9-test prewrite suite and no release validator or allowlist.

**B4 — V11-R-009 legacy-regression evidence is missing, and legacy receipts have already drifted.** `GOAL.md:20` requires V8/V9/V10 signatures unchanged, but V11 idempotence covers only its own signature plus frozen V10 source hashes. Meanwhile git status already shows `runs/khufu-v9-causeway-fidelity/v5-playmode-regression.md` and `runs/pyramid-reference-matched-v4/validation-receipt.md` modified. The plan never reconciles them; each must be explicitly classified as V11 regression evidence (rerun, include) or unrelated drift (exclude/restore) before staging. V10 shipped `legacy-regression.md` plus three legacy logs; V11 has no equivalent.

**B5 — Static clearance is weaker than V10's own accepted standard, with a specific blind spot.** `Validator.cs:489-525` uses `Physics.OverlapCapsule(p+0.58, p+2.05, r=0.32)` at 13 samples/segment, and line `:517` discards any collider whose `bounds.max.y <= point.y + 0.30f`. So a lip up to 0.30 m anywhere on the route is invisible to the gate; nothing verifies a floor exists beneath the route; step height between samples is untested; reachability from the V10 gallery is untested. That threshold is only safe if the real `MVP_Player` controller has `stepOffset ≥ 0.30` and `radius ≤ 0.32` — unverified.

**B6 — Enclosure does not cover the condition it is credited with.** `ValidateEnclosure` (`:527-560`) is 4 samples, one origin each at +1.55 m, rays only ±right, up, and forward-for-chamber; `ValidateBoundaryRay` (`:562-572`) accepts only V11-owned colliders. No downward, backward, or axis rays, and **no exterior-leak test at all** — yet condition 5 names "exterior leaks." Don't weaken it, but stop crediting it with leak coverage; manual QA must carry that explicitly.

**B7 — Capture statistics cannot detect what's being asked of them.** `Capture()` (`:197-204`) fails only on bytes < 65536, stddev < 0.03, range < 0.18, mean > 0.78, clipped > 0.22. No *minimum* mean, no occupancy test — exactly how the current integration frame passed at mean 0.2951. `EdgeDensity` is computed and written to the manifest but never gated.

**B8 — Zero renderer headroom, and the manifest doesn't hash the file you're about to change.** Root 5/5 and map 829/829 are at maximum (colliders have room: 33/66, 567/600). Record as a named accepted risk. Separately, the manifest binds scene/builder/pipeline/validator SHA-256 (`:86-89`) but not the exporter's own hash — and the exporter is the file B1/B2 change.

**B9 — Capture-time scene mutation is unproven not to dirty the scene.** The exporter toggles `SetActive` across map children, disables all scene lights, overwrites `RenderSettings` (`:51-79`), and calls `AssetDatabase.Refresh()` (`:119`) without saving. Plausibly clean, never proved. Fix by ordering: run idempotence *after* the capture pass.

**B10 — Doc drift.** `TEST_PLAN.md:20-23` lists 4 negative controls; `negative-controls.md` reports 5 plus rollback. And `STATUS.md` is stale in both directions — still reporting the Hub elevation-1223 failure and listing screenshots/idempotence/performance as "Unverified" while passing receipts exist.

## 2. Missing tests and evidence

| Artifact | Precedent to reuse |
| --- | --- |
| `tools/validate_khufu_v11_release.py` + tests + `staging-allowlist.txt` | `tools/validate_khufu_v10_release.py` |
| CharacterController traversal receipt + named-blocker negative control | `KhufuV10TraversalProofProbe.cs`, `KhufuControllerHitRecorder.cs`, `runs/khufu-v10-interior-spine/player-proof/` |
| Legacy regression across V4/V5/V8/V9/V10 | `runs/khufu-v10-interior-spine/legacy-regression.md` |
| Per-view manual-QA receipt against `TEST_PLAN.md:34-35` | `runs/.../manual-qa.md` |
| Focused pytest receipt bound to revision + source hashes | `runs/.../python-tests.md` |
| Post-commit verification receipt | `runs/.../post-commit-validation.md` |
| Exporter SHA-256 in the capture manifest | exporter `:86-89` |
| `MVP_Player` radius/height/stepOffset vs. validator constants `0.32 / 0.58 / 2.05 / 0.30` | — |

## 3. Integration-view decision and smallest safe correction

The stated risk (hollow monument) is not the actual defect. The actual defect is floating/clipped geometry from the visibility profile hiding V10. Smallest safe correction, exporter-only:

1. Add the V10 root to the `Integration` keep-set in `CaptureVisibilityScope.Apply` (`:333-349`). Verify empirically it doesn't occlude the suite from `z=-48`; fallback is keeping only the V10 gallery/Great Step children.
2. Re-aim and widen the integration camera (`:168-170`) so the suite is centered and uncut.
3. Re-frame `great_step_open_axis` (`:150-153`) per B1, with V10 visible so the former boundary is in shot.
4. Add the exporter's SHA-256 to the manifest.

Drop `V4_Section_Poche`. Add no production geometry to fix a proof camera. Regenerate all six captures and rerun every hash-bound gate, with idempotence moved to run *after* captures.

## 4. Static clearance vs. real traversal

**Static clearance is not sufficient; a CharacterController traversal receipt is required before ship.** Three independent reasons: the `+0.30 m` discard at `Validator.cs:517` hides sub-0.30 lips; nothing proves a floor exists under the route; and V10 proved the *closed* state of this exact boundary with a real controller, so proving the *open* state statically regresses the project's own accepted standard. The harness already exists — this is reuse, not new tooling. Minimum: normal round trip Great Step → antechamber → King's Chamber → return, plus the blocker-enabled run that must fail.

## 5. Recommendation — Revise

Keep candidate-not-release, regenerate-and-rerun, Opus review before staging, scoped commit, post-commit verify. Change before implementation continues:

1. Replace step 4's diagnosis and fix (B1, B2).
2. Add a traversal-proof step before the release gate (B5).
3. Replace step 6's prose inventory with the ported V10 allowlist + release validator + tests (B3); resolve the two drifted legacy receipts explicitly (B4).
4. Add a legacy-regression rerun step (B4).
5. Move idempotence after captures; add exporter hash to manifest (B8, B9).
6. Reconcile `TEST_PLAN.md` negative-control count; rewrite `STATUS.md` against actual receipts (B10).
7. Record zero renderer headroom as a named accepted risk in the review packet.

**Direct answer:** as written the plan is not sufficient to close V11 — it would ship a non-probative primary capture, an unproven traversal claim, and an unenforced release boundary against a 1002-entry dirty worktree. With those seven changes it is safe and sufficient.

One correction to your brief worth flagging plainly: the integration capture's problem is not hollowness. Section mass is present and reads correctly; the defect is the disconnected entry passage and the clipped, off-center suite.

