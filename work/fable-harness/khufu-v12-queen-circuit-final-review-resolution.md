# Khufu V12 Final Review Resolution

First-round review: `khufu-v12-queen-circuit-final-review.opus.md` (`revise minimally`).

## Blocking Findings

- **B1 — adopted.** Added the exact 108-path staging allowlist, fail-closed release validator,
  18 focused release-validator tests, staged-blob/base-commit/post-commit checks, and clean
  alternate-index import evidence. The final clean source candidate used an isolated index and
  object store, reproduced scene `eec9cc9c...`, static signature `6f7faced...`, generated/material
  signature `33fbeb4d...`, and all six capture blobs without changing the main index. The actual
  post-commit check remains a procedural condition because no commit was authorized.
- **B2 — adopted more strongly than requested.** The three development migration hashes were
  removed from executable Builder input handling. `RULES.md` rule 19 records them as retired;
  release input accepts only a complete V11-open or canonical V12-open component state.

## Additional Review Actions

- **Python failure inventory — adopted.** `python-tests.md` freezes exactly 13 unrelated failure
  IDs. The focused V12 suite is `28 passed`; the full suite is `183 passed, 13 failed,
  11 subtests passed`, with no V12 failure.
- **Warning count — accepted.** The rebuilt Windows player has `0 errors / 185 warnings`, matching
  the reviewed baseline.
- **Evidence binding — adopted.** Capture manifest hashes current scene/static receipt and four
  generator sources. Build receipt hashes the player, level, assembly, scene, and 11 C# inputs.
  Player receipts hash the current assembly and CSV traces and now disclose the real
  `CharacterController` dimensions.
- **New release-gate findings — adopted.** Exact `.gitattributes` rules preserve four byte-bound
  inputs across Git checkout. The Windows builder now snapshots and restores the V12 generated
  and material trees, preventing `_EMISSION` keyword loss; its receipt proves `33fb... / 33fb...`.
- **Follow-up O1 — adopted.** `--check-staged` and `--postcommit` now automatically imply external
  review enforcement, so neither mode can omit the designated Fable ship verdict or review
  resolution token. A focused regression test pins all four flag combinations.
- **Follow-up F5 — adopted.** The clean-index receipt now names the exact 10 deliberately deferred
  non-source artifacts rather than leaving the 98/108 delta implicit.

## Verification

- `python -m pytest tools/tests/test_validate_khufu_v12_prewrite.py tools/tests/test_validate_khufu_v12_release.py -q`
  -> `28 passed`.
- `python tools/validate_khufu_v12_release.py --output runs/khufu-v12-queen-circuit/release-validation.md`
  -> `KHUFU_V12_RELEASE_VERDICT: passed` before external-review enforcement.
- Unity Builder, static, idempotence, nine negative controls, V4–V11 legacy regression, six
  captures, Windows build, normal traversal, and Queen boundary control all passed after the
  implementation changes.
