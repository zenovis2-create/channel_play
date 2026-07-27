# Review Checkpoint

Task ID: task-0028
Reviewer: critic_reviewer
Status: reviewed
Created: 2026-07-27T17:41:45+09:00

## Findings First

No Critical, High, Medium, Low, P1, P2, or P3 finding remains.

- The manual affordance reaches the existing protected apply-status endpoint;
  it has no apply call site and sends only asset ID plus a 128-bit random
  attempt ID.
- The browser retains one process-memory object with exactly six approved
  metadata fields. Answer values, apply grants, confirmation text, local
  storage, and session storage are excluded.
- The recovery TTL comes from the server result store only with a valid
  non-no-op preview grant. The client accepts only positive integer TTLs up to
  one hour and cannot extend the original apply-time deadline.
- Recovered results pass the existing saved-field count/order, canonical-name,
  protected-state, contact-false, receipt-false, and hash-shape checks before
  input clearing or state refresh.
- Pending, unknown, malformed, mismatched, expired, and network-failed results
  preserve a possibly-saved/no-retry warning. A live ambiguous record blocks a
  new preview.
- Dynamic recovery content uses `textContent` and created DOM nodes, preventing
  field-name or response-driven HTML injection.
- Server tests cover protected preview/status/apply behavior, TTL exposure,
  expiry, redaction, exact request schemas, body limits, and side-effect gates.
  UI contracts, Chrome checks, JavaScript syntax, and the full regression suite
  pass.

## Threat and Blast-Radius Assessment

Abuse cases reviewed: replaying a write through the recovery button, extending
result retention, leaking owner values, tampering with result metadata, DOM
injection, bypassing contact authorization, and creating a false PASS receipt.
The implemented path is read-only and value-redacted; compromise is limited to
short-lived lookup metadata already bound to a protected loopback session.

## Residual Risk

Informational: browser reload, server restart, TTL expiry, or bounded-store
eviction removes recovery capability. This is deliberate fail-closed behavior;
the UI requires manual manifest inspection and prohibits a save retry. A
point-in-time verified hash cannot prevent a later external edit.

Decision: approved for evidence verification and merge.

## Task

Add manual, status-only recovery for an ambiguous Truth Pen owner save without
weakening the one-time grant, atomic write, contact, or receipt gates.
