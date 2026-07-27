# Review Checkpoint

Task ID: task-0027
Reviewer: critic_reviewer
Status: reviewed
Created: 2026-07-27T17:05:52+09:00

## Findings First

No P1, P2, or P3 finding remains.

- Apply-attempt IDs contain 128 cryptographically random bits and use a strict
  lowercase-hex wire format. Duplicate IDs are rejected before grant
  consumption or writing.
- Reservation, grant consumption, atomic save, result validation, and result
  completion remain inside the existing apply lock. A completed safe result
  is retained before the primary HTTP response is sent.
- The result store is lock-protected, process-local, capped at 64 entries, and
  expires records after five minutes. It stores only an explicit allowlist,
  validates safety booleans, canonical field order/count, manifest path/hash,
  and next command, and defensively copies mutable data.
- The status endpoint inherits the loopback, Host, Origin, execution-token,
  JSON content-type, and no-store response gates. It adds a 1,000-byte limit,
  exact two-field schema, strict ID validation, and asset binding.
- Wrong-asset, unknown, and expired attempts are indistinguishable not-found
  results. Pending results disclose no saved metadata.
- Recovery performs one read-only status lookup only after a missing,
  malformed, or unsafe primary response. It never repeats the apply request,
  and the recovered object must pass the existing preview-bound verification.
- No answer values are persisted or returned. Browser local/session storage is
  unused, rendering remains `textContent`-only, artist contact stays false,
  and no procurement receipt is created.
- Store/API/UI contract tests, syntax checks, the full suite, and Chrome
  preview-only proof pass. The real manifest and existing FAIL receipt hashes
  are unchanged.

## Residual Risk

The recovery record is intentionally best-effort and process-local. Restart,
TTL expiry, or capacity eviction makes it unavailable. A completed hash is
still a point-in-time check and cannot prevent a later external edit. In every
unavailable, pending, or mismatched case, the UI conservatively says the write
may have occurred and instructs the owner to inspect the manifest without
retrying.

Decision: approved for evidence verification and merge.

## Task

Recover ambiguous Truth Pen owner-save results using a bounded, short-lived,
value-redacted in-memory attempt record and a protected status endpoint,
without retrying the write or weakening contact and receipt gates.
