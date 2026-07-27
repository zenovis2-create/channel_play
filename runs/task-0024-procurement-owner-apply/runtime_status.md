# Task 0024 Runtime Status

Recorded: 2026-07-27T15:40:47+09:00
Branch: `codex/procurement-owner-apply`
Scope: explicit two-step owner-answer save gate

## Runtime State

- Real owner progress: `0/16`
- Current FAIL receipt present: `true`
- Artist contact ready: `false`
- Real apply requests sent during Chrome proof: `0`

## Chrome Validation

Chrome loaded local Studio at `http://127.0.0.1:8770/`.

- A complete repository-safe example produced a five-minute one-time grant.
- The apply panel remained hidden and disabled before a valid preview.
- Both checkboxes alone kept the save button disabled.
- The exact phrase `소유자 승인값 저장` enabled the button.
- Studio displayed `모든 확인이 완료되었습니다. 한 번만 저장할 수 있습니다.`
- Editing the answer JSON hid the panel, disabled the button, and reported
  `입력이 변경되었습니다. 다시 사전검증하세요.`
- Local/session storage stayed empty and the browser console had no errors.
- The save button was never clicked; no `/api/procurement/apply` request ran.

## Security Boundaries

- Grants expire after 300 seconds, are consumed once, and are capped at 64.
- Each grant is bound to the canonical answer digest, asset, and current
  normalized manifest SHA-256.
- Apply requires the loopback/Host/Origin/token gate, strict exact request
  fields, finite JSON, the grant, expected hash, and exact confirmation.
- The server revalidates under an apply lock and atomically replaces the
  manifest from a temporary file in the same directory.
- Apply never creates a receipt and returns `contactAuthorized: false`.
- Replay, expiry, answer mismatch, and stale-manifest cases fail closed.

## Unchanged Real Files

- Decision manifest Git blob before and after:
  `d39ff48880956e10e67b75dc741d7cff1e42fa9b`.
- Existing readiness receipt Git blob before and after:
  `c2e6f5e710493fc7c2e0ed3468e8472194ef62ec`.

## Verification

- `node --check tools/studio/app/app.js` — passed
- Focused suite — `91 passed, 19 subtests passed`
- Full suite — `347 passed, 33 subtests passed`
- `git diff --check` — passed
