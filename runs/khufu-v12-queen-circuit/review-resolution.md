# Khufu V12 Opus Review Resolution

- First-round verdict: `revise minimally`
- Follow-up verdict: `ship`
- Resolution status: `implemented and externally reviewed`
- B1: release validator, focused tests, exact allowlist, clean alternate-index import, staged
  inventory schema, staged blob checks, base-commit binding, and post-commit blob checks added.
- B2: three development migration hashes retired from Builder code and documented in `RULES.md`.
- Frozen unrelated Python failures: `13`, with exact IDs recorded in `python-tests.md`.
- Additional release hardening: Git byte preservation for canonical inputs, protected
  generated/material snapshot around Windows build, and real controller dimensions in player
  receipts.
- Commit/post-commit receipt: not run because the user did not authorize staging or commit.
- Follow-up O1: adopted; staged and post-commit modes now automatically require review evidence.
- Follow-up F5: adopted; the clean-index receipt names all 10 deferred non-source artifacts.

The designated follow-up output ends in one exact `VERDICT: ship` line.

KHUFU_V12_REVIEW_RESOLUTION: passed
