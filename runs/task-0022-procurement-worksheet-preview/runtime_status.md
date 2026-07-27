# Task 0022 Runtime Status

Recorded: 2026-07-27T13:38:34+09:00
Branch: `codex/procurement-worksheet-preview`
Scope: sanitized worksheet preview and browser-local Markdown download

## Runtime State

- Procurement status: `blocked`
- Validator errors: `16`
- Structural progress: `0/16`
- Worksheet available: `true`
- Worksheet items: `16`
- Current FAIL receipt present: `true`
- Procurement passed: `false`
- Artist contact ready: `false`

## Browser Validation

Chrome loaded the local Studio at `http://127.0.0.1:8767/`.

- Preview and download controls were enabled for the current unresolved state.
- Preview was collapsed initially and opened with `aria-expanded="true"`.
- Preview contained 16 blank owner-approved placeholders.
- Preview contained neither `UNKNOWN` nor validator-message text.
- Download filename: `truth_pen-owner-decision-worksheet.md`
- Download size: `3300` bytes
- Download content matched the escaped preview text exactly.
- UI reported: `16개 미결정 항목 양식을 내려받았습니다.`

The temporary object URL is scheduled for revocation after the browser starts
the download. The download handler does not call Studio commands or network
APIs.

## Safety Boundaries

- Preview content is rendered through HTML escaping.
- Copy, preview, and download share the same unavailable state for complete or
  indeterminate decisions.
- No manifest value, authorization flag, candidate selection, contact state,
  or receipt changed.
- Decision manifest Git blob:
  `d39ff48880956e10e67b75dc741d7cff1e42fa9b`
- Existing readiness receipt Git blob:
  `c2e6f5e710493fc7c2e0ed3468e8472194ef62ec`

## Verification

- `node --check tools/studio/app/app.js` — passed
- Focused Studio suite — `61 passed, 4 subtests passed`
- `python -m pytest tools/tests tools/studio -q --disable-warnings` —
  `330 passed, 33 subtests passed`
