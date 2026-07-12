# Khufu V10 Interior Spine final review

Decision needed: decide whether the V10 implementation and evidence are ready for exact staging and
a scoped commit. Return `VERDICT: ship` only if no blocking evidence gap remains; otherwise return
`VERDICT: revise` with concrete blockers. Respond directly and do not write files.

## Intent and false-done condition

- Deliver a historically bounded, gameplay-adapted Khufu interior spine and HYBRID maze return in
  the integrated Unity map, with observable Windows traversal, exact boundary, performance, legacy,
  mutation, visual, and deterministic evidence.
- False done: static samples pass while a full capsule cannot traverse; the wrong collider is credited
  as Great Step; screenshots are nonblank but misleading; stale build/performance evidence is used;
  V4/V5 ownership is damaged; or unrelated work is committed.

## Implementation decisions

- Independent sibling root; V4/V5 builders are unchanged.
- Eight evidence segments classified FACT or HYBRID; disputed shaft naming is forbidden in runtime
  labels and receipts.
- Exact visual transition contract: 60 renderers, 39 colliders, zero V5 Crown intersection.
- Six batched renderers, 5,016 vertices, 2,508 triangles, 70 enabled V10 BoxColliders.
- The HYBRID service landing is level before a monotonic descent; route count remains 16.
- The Gallery floor continues beneath the named Great Step wall by more than one controller radius.
- Runtime controller movement separates XZ motion from capped grounding. Side, ground, and ambiguous
  contacts are recorded independently so floor callbacks cannot overwrite a wall assertion.

## Deterministic and mutation evidence

- Static suite: passed; 220 clearance samples, zero collisions, enclosure minimum 0.792, orphan
  legacy colliders 0, V5 Crown dependencies/intersection 42/0.
- Idempotence: two scene hashes identical at
  `d1778ecb2edfb7e83173a893ec82f5acb8959078ec68fc714a5f1a1320e83ad2`; V10 signature stable at
  `b9d56231cbc662a4fefef9ccd81a495d7bc7d1bd232ea16f8f0ad5e186571813`.
- Pair mutation, transition mutation, and independent 0.75 m observation mutation all rejected.
- Ten focused Python contract/performance tests pass.

## Windows evidence

- Development build passes with 0 errors; Assembly-CSharp SHA256
  `2fe263fa573edd5eec9022b1238588df92a6e48f6a86991c0af7228fa46af468`.
- Normal round trip: 16/16 anchors, expected/traversed 96.105/95.815 m, max/final error
  0.150/0.030 m, three fresh semantic 1536x1024 PNGs.
- Great Step negative control: attempted/advanced 2.200/0.299 m; exact side collider
  `V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary`; simultaneous ground collider
  `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp`; two fresh semantic PNGs.
- Error-metric negative control: independent 0.750 m offset rejected by unchanged 0.4 m threshold.
- Performance at 1536x1024 Ultra: 3,552 samples; frame/main/render/GPU p95
  8.339/2.849/2.679/2.330 ms; allocated/reserved/managed 155.1/262.6/2.8 MB; bounded raw
  36,978,740 bytes; validator passed.

## Visual and legacy evidence

- Eight normal editor captures plus one overlap mutation capture are fresh, 1600x1000, hash-bound to
  the final scene, and directly inspected.
- Required views show entrance, plug girdle, Queen boundary, Gallery axis, corbel/slot detail, Great
  Step, continuous HYBRID return, and cutaway integration.
- V4 validation, V5 Gate 4, V5 PlayMode, and the V9 regression wrapper pass on the integrated scene.
- The integrated cutaway remains a structurally readable production blockout. It does not claim
  photoreal materials, final lighting, VFX, audio, or production chamber art; those are explicitly
  deferred in the contract.

## Failure recovery evidence

- A repeated dark Queen capture triggered isolated-render diagnosis and an exact renderer-only
  transition amendment; all transition, idempotence, and mutation gates were rerun.
- A repeated HYBRID floor failure triggered Fable blocker review, bounded movement tracing, and a
  geometry fix rather than threshold relaxation.
- A repeated Great Step name mismatch triggered side/ground hit classification; the wall did not move
  to satisfy the test, and exact-name proof now passes.
- Three runtime debugging hypotheses and their confirming evidence are recorded in
  `runs/khufu-v10-interior-spine/debugging-audit.md`.

## Review scope and risk

- Risk score: `5/10` (cross-module generated scene/assets, many files, Windows-specific runtime).
- Review the V10 route/geometry contract, hit classification, fail-closed thresholds, evidence
  freshness, historical boundaries, and whether the stated blockout limitation contradicts the goal.
- Do not request full implementation code. Prioritize only findings that would make the completion
  claim false.

## Required response

1. Blocking findings, ordered by severity, or `none`.
2. Nonblocking risks, if any.
3. Evidence consistency verdict.
4. Final line exactly `VERDICT: ship` or `VERDICT: revise`.

## Revision after first final review

The first final review returned `VERDICT: revise` for two binding gaps. Both are now addressed:

1. Exact staging scope:
   - `docs/khufu-v10-interior-spine/staging-allowlist.txt` enumerates exactly 130 admissible paths.
   - The release validator rejects staged paths outside that set, missing dirty allowlisted paths,
     additional unstaged deltas on staged files, and unlisted V10 source/doc/harness files.
   - `Packages/manifest.json`, `Packages/packages-lock.json`, `ProjectSettings/EditorBuildSettings.asset`,
     and `ProjectSettings/ProjectSettings.asset` were diff-reviewed. Their changes are earlier Unity
     MCP/AI package setup and Unity platform serialization, not V10 implementation requirements; all
     are deliberately absent from the allowlist.
2. Runtime binding:
   - `tools/validate_khufu_v10_release.py` writes and verifies editor, player, and performance bindings.
   - Player and performance bindings include the final scene, executable, built level,
     Assembly-CSharp, every evidence artifact, and all 269 files in `Builds/KhufuV10` with size and
     SHA256.
   - The final release validator passes with scene `d1778ecb...`, Assembly `2fe263fa...`, 16 unique
     decoded PNGs, exact receipt tokens, and current artifact hashes.
   - Execution order was final scene rebuild -> final build -> normal/boundary/error controls ->
     bounded performance capture -> binding refresh. No renderer or geometry amendment followed.

The first review's nonblocking notes are also resolved in the validator report:

- `60/39` are renderer/collider transition scopes; `6/70` are enabled batched V10
  renderer/BoxCollider totals.
- Enclosure is a unitless hit ratio: observed minimum `0.792`, frozen pass threshold `0.750`.
- Controller radius is `0.450 m`; Great Step attempted/advanced remains `2.200/0.299 m`.
- The release-validator helpers add five tests; the focused Python total is now 15 passing tests.

Re-review the two former blockers and return the required final verdict format.

## Revision after independent code and gate review

The first independent code review and gate audit both rejected the candidate. Their substantive
findings have been implemented rather than waived:

1. Dependency closure:
   - Six V10 materials, their six metadata files, and the material-folder metadata are now required,
     allowlisted, GUID-checked against the scene, and cryptographically bound.
   - A full scan of every untracked Unity metadata GUID against the final scene found seven older V4
     mesh dependencies. Those seven assets, seven metadata files, and two parent folder metadata files
     are now also required and bound. V4 builder source remains unchanged.
   - The allowlist now contains 163 unique paths, including `.gitattributes`, clean-index evidence,
     and the deterministic staged inventory. Packages and ProjectSettings remain excluded for the
     previously documented scope reason.
2. Source and staged-byte binding:
   - All V10 C#/Python source, Unity source metadata, generated meshes, materials, legacy direct scene
     dependencies, and `.gitattributes` are recorded by path, size, and SHA256.
   - Bindings record both working-file bytes used by the build/evidence run and Git index blob bytes.
     The staged gate requires the scene and every release input to match those index records and
     rejects an additional worktree delta.
   - Binding schemas were advanced to v2.
3. Exact commit proof:
   - `staged-inventory.json` deterministically records every staged index blob except its own file and
     the staged validation receipt, avoiding a self-hash cycle.
   - The staged gate requires every dirty allowlisted release path, requires its two staging helpers,
     and rejects extras, omissions, staged/unstaged splits, and unlisted V10 paths. Already committed,
     unchanged contract files remain permitted dependencies without being falsely required in HEAD.
   - Post-commit validation requires the nonempty HEAD path set to equal the recorded inventory plus
     the two staging receipts exactly, requires an empty index, rejects worktree drift, and rechecks
     each committed blob.
4. Adversarial coverage and truthful output:
   - The release test module now has 13 tests, including binding drift, material GUID closure, staged
     source mutation, empty/subset/extra commits, and post-commit worktree drift.
   - Hardcoded geometry expectations were removed from aggregate observed facts.
   - Required receipts and player-facing evidence reject the prohibited shaft phrase.
5. Clean-index proof:
   - The staged tree was exported as an isolated 872-file Unity project.
   - The baseline package manifest cannot resolve one built-in package in Unity 6000.0.76f1, while
     current package changes belong to prior MCP/AI setup. The supported `-noUpm` editor option was
     therefore used without adding package files to V10 scope.
   - The first clean import exposed the seven missing V4 meshes. The second exposed raw-hash drift
     caused only by `core.autocrlf=true`. `.gitattributes` now fixes Unity `.asset`, `.mat`, `.meta`,
     and `.unity` paths to LF.
   - The final clean run exits 0 with zero compiler errors and zero validation exceptions, imports all
     six V10 material GUIDs, runs all static/idempotence/mutation gates, and ends with the same scene
     SHA256 `d1778ecb...`.
   - In the isolated no-UPM rebuild, `V10_Route_Amber.mat` is reserialized differently and the
     non-frozen diagnostic V10 signature differs. Structural counts, frozen V8/V9 signatures, all
     gates, and final scene bytes match. The original Windows/player/performance bindings remain tied
     to the original final scene and build.

Re-review these independent-review corrections. Do not treat the intentionally pending final
review-work/staged/post-commit receipts as absent implementation; assess whether the mechanisms and
clean-index evidence now close the reported false-done paths.
