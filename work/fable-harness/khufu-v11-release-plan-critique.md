# Khufu V11 Release Plan Critique

Role: Act as the architecture and risk critic. Do not implement.

## Task goal

Close the Khufu V11 Royal Chamber Circuit as a bounded, reviewable Unity slice on top of committed
V10 baseline `42a63801ea4699c170dbe39838d63d6d93a506ec`, without absorbing unrelated dirty-worktree changes.

## Constraints

- V10 source meshes, materials, builders, and route contract are immutable.
- V11 may rebind only the two declared V10 renderers and disable only the named Great Step blocker.
- Queen, Subterranean, scan-anomaly, global lighting, VFX, audio, and multiplayer work remain out of
  scope.
- Do not weaken all-map clearance, enclosure, negative-control, or idempotence checks.
- The worktree has 44 modified tracked files and 958 untracked entries. Preserve unrelated work.
- Release requires deterministic local verification; Opus reviews risk but does not edit.
- No completion claim may rely only on numeric screenshot statistics.

## Relevant files and contracts

- `docs/khufu-v11-royal-circuit/GOAL.md`
- `docs/khufu-v11-royal-circuit/PLAN.md`
- `docs/khufu-v11-royal-circuit/RULES.md`
- `docs/khufu-v11-royal-circuit/TEST_PLAN.md`
- `docs/khufu-v11-royal-circuit/STATUS.md`
- `docs/khufu-v11-royal-circuit/performance-budget.json`
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitBuilder.cs`
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitMeshPipeline.cs`
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs`
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitScreenshotExporter.cs`
- `Assets/_Project/Scripts/Gameplay/KhufuV11RoyalRouteContract.cs`
- `Assets/_Project/Scenes/School_MVP.unity`
- `tools/validate_khufu_v11_prewrite.py`
- `tools/tests/test_validate_khufu_v11_prewrite.py`
- `runs/khufu-v11-royal-circuit/`

## Current evidence

- Prewrite validation: passed, 8 segments, 5-renderer/66-collider root budget, 6 captures required.
- Static validation: passed; root 5 renderers, 2,016 vertices, 1,008 triangles, 33 colliders;
  map 829 renderers and 567 colliders; 78 clearance samples, zero blockers; 13 enclosure rays,
  zero misses.
- Idempotence: passed; scene and generated signatures match across two rebuilds; frozen V10 source
  signature unchanged.
- Negative controls: five expected mutations rejected; injected transition failure rolled back.
- Clean package import log ends with `Exiting batchmode successfully now!`.
- Six 1600x1000 captures are fresh, unique, hashed, and pass nonblank statistics.
- Exact Unity executable exists at
  `C:\Users\User\Unity\Hub\Editor\6000.0.76f1\Editor\Unity.exe`.
- Existing code review reports no source blocker and warns only that the gabled cap has about 0.054 m
  envelope margin.
- No V11 Opus final review, focused pytest receipt, manual-QA receipt, or scoped release commit exists.
- No V10 frozen source path is modified in Git status.

## Direct visual inspection

- `great_step_open_axis.png`: readable interior, but the route opening is not strongly centered.
- `antechamber_portcullis_detail.png`: portcullis rhythm is visible; one angled element at right is
  visually ambiguous.
- `kings_chamber_wide.png`: enclosed chamber and sarcophagus are readable; the route inlay appears
  as a thin raised/floating line in the foreground.
- `sarcophagus_and_shaft_boundary.png`: chamber, sarcophagus, and one shaft boundary are readable.
- `relieving_stack_cutaway.png`: five stacked levels and gabled cap are legible as display art.
- `pyramid_royal_circuit_integration.png`: likely blocker. The visibility profile keeps only
  `V4_Foundation_Bedrock_Cutaway`, `V4_Smooth_Casing_With_Tapered_Cutaway`, and the V11 root.
  The resulting image reads as a mostly empty pyramid shell with a small floating royal suite and
  an angled element. This may trigger GOAL false-completion condition 5 and RULES art rule 4.

## Proposed plan

1. Treat existing V11 outputs as a candidate, not an accepted release.
2. Run the focused pytest suite and preserve a revision/source-hash-bound receipt.
3. Write a six-view manual-QA receipt. Fail the integration view unless review evidence shows that
   it retains enough section mass to read as a solid monument.
4. If the integration view fails, make the smallest exporter-only visibility/framing correction.
   First test adding the existing V4 `V4_Section_Poche` child to the Integration profile, because it
   owns the filled section mass and avoids altering V11 geometry or V10 bindings. Do not add new
   production geometry merely to fix a proof camera.
5. Regenerate all six captures and manifest after any exporter change. Rerun static validation,
   idempotence, negative controls, focused pytest, and manual QA because the evidence hashes change.
6. Reconcile `STATUS.md` with actual passed/unverified evidence and add a release inventory that
   excludes caches, raw superseded failure logs, unrelated `.omo/`, `AGENTS.md`, toolchain work, and
   other dirty paths.
7. Request Opus final review with exact diff, verification results, visual-QA decision, release
   whitelist, and residual risk.
8. Resolve findings, rerun affected checks, then stage and commit only the V11 release set. Run
   post-commit verification before any ship claim.

## Known unknowns

- Whether `V4_Section_Poche` is sufficient and correctly oriented in the integration camera without
  hiding the V11 suite.
- Whether the angled objects in the integration and antechamber views are intended portcullis tracks
  or visual overlap.
- Whether the static 78-sample capsule clearance is sufficient for the contract, or a real
  CharacterController traversal receipt is required before ship.
- Whether raw historical V11 failure logs belong in the release commit or only final receipts/logs.
- The root and map renderer budgets are exactly at their maxima (5/5 and 829/829), leaving no
  renderer headroom.

## Requested response

Return:

1. Blocking findings in priority order, citing the supplied contracts/evidence.
2. Missing tests or evidence.
3. A decision on the integration-view risk and the smallest safe correction.
4. A decision on whether static clearance is enough or real CharacterController traversal is needed.
5. Recommendation: adopt / adopt with changes / revise.

Decision needed: Is this plan safe and sufficient to close V11 without contaminating the release
with unrelated work, and what must change before implementation continues?
