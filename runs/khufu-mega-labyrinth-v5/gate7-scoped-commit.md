# Khufu V5 Gate 7 Scoped Evidence Commit

- Verdict: **passed**
- Commit: `868486abc3499ee1bf6517840891ac84e4fe59d5`
- Parent implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Commit subject: `docs: close Khufu V5 acceptance evidence`
- Files: `72`
- Top-level scope: `docs=6`, `runs=59`, `tools=2`, `work=5`

## Scope Audit

- Included: Khufu V5 harness docs, RULES, harness validator/tests, V4/V5 receipts, deterministic
  captures, profiler raws, build-input provenance, Fable prompt/output/metadata, and loop contract.
- Excluded: `ProjectSettings/`, `Packages/`, `Builds/`, `Library/`, `Temp/`, and `.omo/`.
- User-owned ProjectSettings/package changes were not staged; their exact bytes are bound by
  `build-input-binding.json`.
- Raw Unity/player logs containing host network addresses remain local and untracked. Committed log
  summaries contain raw SHA256 values and exact acceptance/failure markers.
- `git diff --cached --check` passed before commit after generated log sanitization and structured
  Bee JSON normalization.

## Commit Chain

```text
a31905297cae2d7e2d83ababab54b109460cfbe2  harness baseline
81c28f84d61d875a54f39d3fc74b202319103e24  V5 Unity implementation
868486abc3499ee1bf6517840891ac84e4fe59d5  Gate 7 evidence and Fable closure
```

GATE7_SCOPED_COMMIT_VERDICT: passed
