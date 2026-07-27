# Task 0028 Runtime Status

Date: 2026-07-27 (Asia/Seoul)
Branch: `codex/procurement-manual-result-recovery`
Result: **PASS**

## Automated Evidence

- Focused Studio server and UI contract suite: `49 passed`
- Full Python suite: `357 passed, 33 subtests passed`
- JavaScript syntax: `node --check tools/studio/app/app.js` passed
- Python syntax: `python -m py_compile tools/studio/workspace_server.py`
  passed
- Diff hygiene: `git diff --check` passed

Coverage includes recovery TTL exposure only with a valid non-no-op grant,
protected preview/apply/status gates, pending/completed/expired result states,
exact status request fields, value redaction, the exact six-key browser record,
one-hour client TTL cap, status-only manual recovery, no write retry, no browser
storage, safe DOM rendering, and success/pending/network/expiry behavior.

## Chrome Safety Proof

Chrome opened loopback Studio on port `8878`. Complete repository-safe sample
answers were submitted only to preview. The final valid response reported 16
changed fields, a 300-second grant TTL, and a 300-second recovery TTL.

- Network: three `/api/procurement/preview` requests during validation
- Network: zero `/api/procurement/apply`
- Network: zero `/api/procurement/apply-status`
- Contact authorization: false
- Receipt created: false
- Apply panel: visible only after valid preview
- Manual recovery panel: hidden during preview

Controlled browser-boundary checks used a stubbed status helper and sent no
write or status request. Pending retained the record/button, success cleared
the six-key record and input after verification, and expiry removed the button
while requiring manifest inspection. See `runs/task-0028/browser-proof.json`.

## Repository State

The real owner manifest and existing receipt remained unchanged.

- Manifest Git blob:
  `d39ff48880956e10e67b75dc741d7cff1e42fa9b`
- Manifest SHA-256:
  `0367a1ef176c51c76f7dcb7f2a966563bb1b9736dfd1633d4a7bdb21f7fd1648`
- Receipt Git blob:
  `c2e6f5e710493fc7c2e0ed3468e8472194ef62ec`
- Receipt SHA-256:
  `2e95792c850af6e82b4236ddd4ec0adeb578b6226188586be3b9bebf4870bc77`

No owner value, artist-contact state, PASS gate, or receipt content changed.
