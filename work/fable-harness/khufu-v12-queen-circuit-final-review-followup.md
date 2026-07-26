Role: Perform a focused follow-up final review. Do not implement. Decide whether the two
first-round blockers are closed for a pre-commit release candidate. A real commit and its
post-commit receipt remain a procedural condition and are not claimed complete.

Task goal:
Approve or reject the Khufu V12 Queen Circuit candidate after resolving the first review
`work/fable-harness/khufu-v12-queen-circuit-final-review.opus.md`.

First-round blockers:
1. B1: no exact release validator/allowlist/clean-index gate.
2. B2: three accepted migration hashes existed in Builder but not in the contract.

Resolution evidence:
- `tools/validate_khufu_v12_release.py` and
  `tools/tests/test_validate_khufu_v12_release.py`: fail-closed source/artifact/receipt/GUID,
  capture, build, player, Fable, alternate-index, staged-blob, base-commit, and HEAD-blob checks.
- `docs/khufu-v12-queen-circuit/staging-allowlist.txt`: 108 exact paths; raw logs and Builds/
  excluded; post-commit report cannot be staged.
- `runs/khufu-v12-queen-circuit/clean-index-import.md`: isolated index/object-store export;
  candidate tree `377622bcd31af1f41f5dd92f416f3cda4961f2ae`, main index unchanged,
  scene `eec9cc9c...`, static `6f7faced...`, generated/material `33fbeb4d...`, six capture blobs
  identical, compiler errors 0.
- `.gitattributes`: four exact `-text` rules added after the clean gate exposed newline
  normalization of byte-bound inputs; final clean import reproduced source bytes.
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitBuilder.cs`:
  migration hash constants/branches removed. Only full V11-open or canonical V12-open binding,
  proxy, and V4 component states are accepted.
- `docs/khufu-v12-queen-circuit/RULES.md` rule 19: the three hashes are documented as retired.
- `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12WindowsBuild.cs`: snapshots and restores the
  V12 generated/material trees. `windows-build.md` proves `33fbeb4d... / 33fbeb4d...`,
  `0 errors / 185 warnings`, and current source/build hashes.
- `runs/khufu-v12-queen-circuit/python-tests.md`: focused `28 passed`; full
  `183 passed, 13 failed, 11 subtests passed`; exact 13 frozen unrelated IDs, no V12 failure.
- `runs/khufu-v12-queen-circuit/player-proof/`: normal 15/15, 136/136 grounded, mouths sealed;
  boundary 1.726 m start, empty overlap, 0.080 m step, exact Queen gate `Sides`, same-frame
  callback. Both bind the current assembly/trace and disclose controller
  `0.450 / 2.000 / 0.300 / 0.050`.
- `runs/khufu-v12-queen-circuit/release-validation.md`:
  `KHUFU_V12_RELEASE_VERDICT: passed` before review enforcement.
- Detailed classification: `khufu-v12-queen-circuit-final-review-resolution.md`.

Constraint:
The main Git index is empty and no commit was authorized. Treat exact-index staging convergence
and the actual post-commit validator as mandatory procedural next gates, not as evidence already
completed. Determine whether any implementation/evidence blocker remains before those gates.

Return:
1. Findings first, each tied to a file or contract.
2. State whether B1 and B2 are closed.
3. End with exactly one final nonblank line:
   `VERDICT: ship`, `VERDICT: revise minimally`, or `VERDICT: do not ship`.

Decision needed: Is the V12 candidate safe to advance to the exact staged-index and authorized
commit gates, or is any implementation/evidence blocker still unresolved?
