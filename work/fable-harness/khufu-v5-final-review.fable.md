COLD_READER answers:

- current decision: adopt the six-document Fable-reviewed harness before any V5 Unity implementation.
- current phase: `KV5-G-000 Harness Ready`.
- next action: run the validator, obtain this Fable final review, then freeze Gate 0.
- blocker: none; Gate 0 stays open until a passing receipt and a Fable verdict both exist.
- proof: `STATUS.md` append-only evidence ledger.

COLD_READER: passed

**Blocking issues**

1. **Fable-verdict parsing is not proven token-safe** (`tools/validate_khufu_v5_harness.py`, check 8). The evidence says acceptance requires the artifact to "contain `FABLE_VERDICT: ship`". Any Fable review artifact that echoes the ask — including this very document, which quotes all three verdict tokens — will contain the ship token even when the actual verdict is revise. If the check is a substring match rather than "unique verdict token on the final non-empty line," this is a direct false-completion vector in the one gate the whole harness exists to protect. The supplied context does not show the parsing rule, so this is an evidence gap as well as a design risk. Codex check: add a unit test feeding an artifact that quotes all three tokens in the body but ends with `FABLE_VERDICT: revise`; the validator must reject it. Enforce exactly-one-verdict-line, matched only at the final non-empty line.

2. **The automatic-block paths are implemented but untested.** Mutation tests cover three rejections (`[x]` without evidence, requirement without test coverage, Fable evidence without ship verdict). They do not cover: warning/error token present alongside a ship verdict (the plan-critique's "warning-only output blocks automatically" rule), a stale artifact hash (check 6), or a tampered receipt (check 7). Four total tests for nine validator checks means the majority of the gate logic has never been proven to fail closed. Codex check: add mutation tests in `tools/tests/test_validate_khufu_v5_harness.py` for (a) warning-token-plus-ship rejection, (b) hash staleness after a one-byte doc edit, (c) receipt with mismatched artifact hash.

3. **Gate 0 freeze has no durable anchor.** The harness files are uncommitted, the receipt lives in `runs/` (confirm it is not gitignored), and baseline commit `2d6dbeb` contains none of the artifact. The baseline-plus-fingerprint exception was accepted, but nothing in the described protocol forces re-validation between "receipt exists" and "gate frozen" — the working tree can drift after the receipt is written. Codex check: make the freeze step itself commit the six docs, validator, tests, and receipt, then re-run the validator against the committed content so the fingerprint and a commit finally coincide. This should be a precondition of coordinate lock, not deferred to Gate 1.

**Non-blocking improvements (false-done-relevant only)**

- The cold-reader answers above were taken from the prompt snapshot, not from `STATUS.md` itself. Add a validator check that `STATUS.md` actually contains the five labeled lines, so the cold-reader audit tests the document rather than a curated summary.
- The "canonicalized self-hash placeholder" in check 9 is a classic tamper seam: the validator hashes itself with the hash field blanked. Add one test that mutates the validator post-receipt and confirms the receipt is then rejected.

**Assessment**

The harness is well-shaped: all seven prior critique items were applied, the ID grammar and evidence ledger are sound, the truth-classification and measurable-map contracts are concrete, and the integration run is clean. The three blocking items are all in the acceptance mechanism itself, which is exactly where the +2 risk for "a defective gate permits later false completion" lives. The fixes are small, fully local to the validator and its tests, and re-runnable in one pass — so revise, not investigate.

**Decision:** revise. Apply the three blocking corrections, re-run the validator and mutation suite, then resubmit for a ship verdict and Gate 0 freeze.

FABLE_VERDICT: revise
