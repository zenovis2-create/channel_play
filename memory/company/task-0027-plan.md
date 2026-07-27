# Task Plan

Task ID: task-0027
Status: planned
Suggested agent: coding_specialist
Suggested reviewer: critic_reviewer
Required evidence: bounded/redacted result-store tests, protected API tests, response-loss recovery UI contracts, JavaScript syntax, preview-only browser proof, unchanged real hashes, focused/full suites, runtime receipt, and findings-first security review

## Request

Recover an ambiguous Truth Pen owner-save response without automatically
retrying the write. Generate a cryptographically random apply-attempt ID in
the browser, reserve it before the atomic save, and retain only a bounded,
short-lived, value-redacted result in server memory. Expose a protected,
strict-schema status endpoint so the browser can recover a completed result
after a lost or malformed primary response. Never persist answer values,
authorize contact, create a receipt, use browser storage, or weaken the
existing preview grant and confirmation gates.

## Implementation

1. Add a lock-protected in-memory result store with a five-minute TTL, a
   64-entry capacity, strict attempt IDs, asset binding, pending reservation,
   defensive copies, and a safe result-field allowlist.
2. Reserve the attempt ID before consuming the one-time grant and performing
   the write. Complete the record before sending the primary response.
3. Add `POST /api/procurement/apply-status` with the existing loopback, token,
   Host, Origin, content-type, body-size, and exact-field gates.
4. Generate attempt IDs with `crypto.getRandomValues`, send the ID on apply,
   and query status only after an ambiguous response. Validate recovered
   results with the existing preview-bound save-verification contract.
5. Keep pending/not-found/expired outcomes fail-closed with the current
   possibly-saved/no-retry instruction.

## Allowed Write Paths

- tools/studio/workspace_server.py
- tools/studio/app
- tools/studio/tests
- docs
- memory/company
- memory/sessions
- reviews
- runs

## Verification

- Unit-test TTL, capacity, asset binding, duplicate reservation, redaction,
  defensive copies, pending, completion, and expiry.
- API-test exact request fields, invalid IDs, protected execution gates,
  completed recovery, pending/not-found/expired results, and no value echo.
- Contract-test cryptographic ID generation, recovery-only status lookup,
  no automatic apply retry, no browser storage, and text-only rendering.
- Run JavaScript syntax, focused tests, full Python suite, and a Chrome
  preview-only proof with zero apply/status calls.
- Record unchanged real manifest and receipt hashes plus residual process-local
  and point-in-time verification risks.
