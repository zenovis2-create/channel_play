# Khufu V5 Execution Rules

Updated: 2026-07-11

These rules govern implementation and acceptance for `Khufu - The Sealed Circuit`. They are
operational constraints, not a second requirements list. When a rule conflicts with an accepted
decision, the newer accepted decision wins and must name the superseded rule.

## Truth Rules

1. Every archaeology-derived district or claim has exactly one `FACT`, `UNKNOWN`, or `FICTION`
   class.
2. SP-BV, SP-NFC, and the Queen's Chamber shafts are observation or lore surfaces, not human
   traversal rooms.
3. Djoser and Hawara names never appear in the Khufu V5 runtime hierarchy or player-facing UI.
4. Fictional underworld space crosses a visible truth boundary before it becomes traversable.
5. A screenshot, concept image, or marker cannot be described as archaeological proof.

## Implementation Rules

1. Rebuild V4 first. V5 content must remain independently removable and must not become a child
   of the V4 root.
2. Runtime gameplay binds through `TraitorEscapeMapBindings`; runtime code must not reference an
   Editor builder.
3. An absent authored binding may use the legacy fallback. A present invalid binding fails loudly
   and never silently generates a different map.
4. Required routes use real collision ownership and CharacterController traversal evidence.
5. Real multiplayer is outside this goal. Evidence may claim only the tested eight-state roster
   and proxy circulation.

## Evidence Rules

1. `STATUS.md` is the only live progress ledger. Every completed line joins to at least one
   accepted, non-empty `KV5-E-NNN` artifact.
2. Implementation evidence names the tested commit and the relevant scene, source, capture, or
   receipt hash.
3. Export success does not equal visual acceptance. Visual acceptance needs a separate review.
4. Editor profiling cannot pass the Windows performance requirement. Hidden or black-window
   captures are invalid.
5. A legacy test may be replaced only by an accepted decision that proves it targets a different
   contract and names the V5-specific replacement surface.
6. Unknown, unmeasured, and not-applicable results remain explicit; they are never rewritten as
   passes.

## Loop And Failure Rules

1. Work proceeds one gate at a time using the smallest matching test after each meaningful batch.
2. The same exact failure twice stops blind retries and opens blocker analysis.
3. A threshold change is a decision made before the next run, never a post-failure adjustment.
4. New code or architecture requires current source or official-document verification when its
   API or behavior is uncertain.
5. Final reports separate completed, incomplete, and unverified surfaces.

## Git And Rollback Rules

1. Unrelated dirty worktree files are never staged, reverted, or used as completion evidence.
2. Generated V5 roots, assets, and evidence are scoped so V5 can be removed without changing the
   accepted V4 geometry contract.
3. Gate rollback returns to the last accepted gate and reruns every downstream affected test.
4. No gate closes on an uncommitted implementation snapshot.

## Final Acceptance Rules

1. All `KV5-T-001` through `KV5-T-016` surfaces must have passing evidence or an accepted,
   explicitly bounded superseding decision.
2. Final Fable output is plain text, contains no harness warning token, and ends with exactly one
   `FABLE_VERDICT: ship` line.
3. The final harness receipt must pass in committed mode.
4. Any contradiction between README, STATUS, evidence, Git, Unity, or Fable reopens Gate 7.
