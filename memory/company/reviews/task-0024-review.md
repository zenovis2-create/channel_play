# Review Checkpoint

Task ID: task-0024
Reviewer: critic_reviewer
Status: reviewed
Created: 2026-07-27T15:41:22+09:00

## Summary

Findings first: no P1, P2, or P3 issue remains.

- The apply endpoint inherits the loopback, Host, Origin, token, JSON
  content-type, and 20,000-byte request gates.
- Preview grants are random, in-memory, five-minute, one-time, capacity-bounded,
  and bound to asset, exact canonical answer digest, and normalized current
  manifest hash.
- Apply requires exact top-level request fields, all 16 valid owner answers,
  the original manifest hash, and the exact Korean confirmation phrase.
- The server revalidates under a process-local apply lock, consumes the grant,
  checks the current hash again, and atomically replaces only the decision
  manifest using a same-directory temporary file.
- Token, confirmation, replay, expiry, mismatch, stale-manifest, atomic-write,
  and no-receipt paths have regression tests.
- The UI adds two explicit confirmations, hides the save panel until a valid
  preview, disables save until the exact phrase matches, expires grants, and
  invalidates immediately when answer text changes.
- A successful save response must explicitly report `saved: true`,
  `contactAuthorized: false`, and `receiptCreated: false`; state refresh is
  handled separately so a refresh failure cannot be mistaken for save failure.
- Chrome sent zero apply requests and left browser storage, the real manifest,
  and the existing FAIL receipt unchanged. Focused/full suites, JavaScript
  syntax, and diff checks pass.

Informational residual risk: an external editor can race the narrow interval after the final
hash check. Studio apply requests are serialized, and any observed prior
change fails closed. The owner must review the saved diff, while artist contact
remains blocked until a separate current `PASS` receipt exists.

Decision: approved for evidence verification and merge.

## Task

Add a two-step, loopback-token-protected Studio apply flow for the 16 canonical Truth Pen owner answers. A valid memory-only preview must mint a short-lived one-time in-memory grant bound to the canonical answer digest and current normalized manifest SHA-256. Applying must require the same complete answers, the grant, an exact explicit Korean confirmation phrase, and the expected current manifest hash; revalidate server-side, consume grants once, reject expired/replayed/stale grants, atomically replace only the Truth Pen procurement manifest, never create a receipt or authorize contact in the response, and leave the existing procurement-check as the separate PASS-receipt gate. Add fail-closed UI, API/security/replay/stale-write tests, Chrome proof without applying fake values to the real manifest, unchanged real manifest/receipt hashes, full-suite evidence, docs, and findings-first review.
