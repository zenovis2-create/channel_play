**Recommendation: revise** — the harness concept is sound but over-fragmented and missing three load-bearing pieces.

**1. Blocking weaknesses**

- **Ten documents is too many for one map feature.** STATUS, EVIDENCE, and DECISIONS will drift apart because every state change requires touching two or three files. Drift between duplicated state is itself a false-done vector: STATUS says `[x]`, EVIDENCE has no row, nobody notices.
- **No requirement-ID schema is defined before writing.** GOAL acceptance IDs, TEST_PLAN test IDs, and EVIDENCE receipts need one shared ID grammar (e.g., `KV5-R-##` → `KV5-T-##` → receipt path) fixed up front, or traceability becomes prose links that rot.
- **Evidence quality is unspecified.** "A concrete evidence artifact" admits a stale screenshot or a receipt from a different commit. Each evidence row must bind: commit SHA, command line, timestamp, and artifact path under `runs/`. Without commit binding, the strongest false-done path stays open.
- **Fable gates have no failure default.** REVIEW_GATES must state that a missing or errored Fable wrapper output = **block**, not "review implied." This is already in your false-done list but must be a machine-checkable rule (receipt file exists and contains a verdict token), not prose.
- **Performance budget is deferred but the gate isn't.** You know budgets need a baseline machine; the plan must include an explicit "budget-capture" phase gate before any performance criterion can be marked, otherwise perf criteria get marked against Editor profiling.

**2. Smallest corrected document set (6 files)**

1. `README.md` — index, ID grammar, update protocol, source-of-truth order.
2. `GOAL.md` — intent, acceptance IDs, false-done conditions, RULES merged in as invariants (rules are goal constraints; separate file adds drift).
3. `PLAN.md` — phases + gates + rollback + Fable requirements per gate (merge REVIEW_GATES; gates without their phases invite skipping).
4. `STATUS.md` — current phase, items with `[x]/[~]/[!]`, each `[x]` carrying an inline evidence path (merge EVIDENCE ledger here as an append-only section, or keep EVIDENCE separate only if the validator enforces the join).
5. `TEST_PLAN.md` — R-ID → T-ID → surface (channelctl check / playtest / sim-check / screenshot / manual) matrix.
6. `DECISIONS.md` — append-only, absorbs RISKS as a "risk register" section (risks are decisions-in-waiting; 4–6 live risks don't need a schema-heavy file).

**3. Minimum checks before implementation**

Machine: (a) validator that every `[x]` in STATUS has a resolvable evidence path and every acceptance ID appears in TEST_PLAN — yes, build it, it's the only thing that makes this harness real rather than paperwork; (b) link/ID uniqueness check; (c) Fable-verdict-receipt-exists check per gate. Human: one cold-reader pass (someone or a fresh agent answers "current decision, next action, blocker, proof" from README alone within 5 minutes) and Fable critique of GOAL's acceptance IDs specifically — vague acceptance criteria are where false-done is born, not in the ledger.

**4. Most likely paperwork failure modes**

- Evidence rows citing artifacts from an earlier commit ("screenshot exists" but predates the change). Commit-SHA binding is the fix.
- Acceptance criteria written as activities ("run playtest") instead of measurable outcomes ("route A→exit ≤ N m, receipt shows pass"). Activities always "complete."
- The validator checking file-exists but not content — a zero-byte receipt passes. Require the receipt schema to include a pass/fail token the validator reads.
- STATUS updated in bulk at phase end rather than per-item, laundering unverified items in with verified ones. Require one evidence path per checkbox, no phase-level rollups.
- Fact/hypothesis/fiction separation living only in the research doc while STATUS language blurs it ("Khufu traversal validated" for SP-BV content). Add a source-class tag (fact/unknown/hypothesis/fiction) to any archaeology-derived requirement ID in GOAL.

**5. Verdict:** revise, then proceed. Cut to six documents, fix the ID grammar and evidence schema (commit + command + artifact + verdict) before writing anything, make the validator content-aware, and make missing Fable receipts an automatic block. No further investigation needed — the repo facts you list are sufficient.
