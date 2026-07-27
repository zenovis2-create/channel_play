# Review Checkpoint

Task ID: task-0029
Reviewer: critic_reviewer
Status: reviewed
Created: 2026-07-27T18:00:56+09:00

## Findings First

No P1, P2, or P3 finding remains.

- Windows and Linux layouts resolve the module beneath the editor `Data`
  directory; macOS app bundles resolve it beneath `Unity.app/Contents`.
- A missing editor raises an explicit error before creating a run directory,
  avoiding a false module diagnosis.
- Missing-module receipts name the active editor, real expected module path,
  host platform, Unity Hub module action, and exact rerun command. Stale
  Mac-only and unimplemented-method claims are gone.
- No code path installs Unity modules, invokes Unity Hub, mutates host
  configuration, or creates a server build when support is absent.
- Handoff generation requires `Build status: passed` and
  `Build output exists: True` before advancing to x86_64 runner readiness.
  Blocked or failed receipts remain `waiting_for_linux_server_build`.
- Production Cockpit uses the same fail-closed markers. It exposes the blocked
  build receipt and Linux build command while retaining truthful dependency
  isolation evidence.
- Regression tests cover all three editor layouts, missing editor, missing
  module, latest receipt binding, blocked/passed handoff states, and Cockpit
  status. Focused and full suites pass.

## Residual Risk

The module and x86_64 runner are external dependencies, not repository defects.
After an operator installs Linux Build Support, the real build command must be
rerun and its new passing receipt must be reviewed before runner handoff. The
current expected result is safely blocked with no generated build output.

Decision: approved for evidence verification and merge.

## Task

Make Linux dedicated-server build preflight and handoff evidence accurate
across supported Unity editor layouts without changing host configuration.
