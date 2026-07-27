# Task 0029 Runtime Status

Date: 2026-07-27 (Asia/Seoul)
Branch: `codex/linux-server-build-preflight`
Result: **PASS — preflight correctly blocked**

## Automated Evidence

- Focused Unity/game-loop/game-production suite:
  `36 passed, 4 subtests passed`
- Full Python suite: `363 passed, 33 subtests passed`
- Python syntax: Unity, game-loop, and production modules passed `py_compile`
- Diff hygiene: `git diff --check` passed

Tests cover Windows, Linux, and macOS module paths; missing-editor fail-fast;
Windows blocked-receipt wording; no Unity batch invocation without support;
latest receipt selection; passing and blocked handoff states; and fail-closed
Production Cockpit status.

## Real Local Preflight

Command: `python tools/channelctl unity build linux-server`

- Active editor:
  `C:\Users\User\Unity\Hub\Editor\6000.0.76f1\Editor\Unity.exe`
- Editor exists: true
- Expected module:
  `Editor\Data\PlaybackEngines\LinuxStandaloneSupport`
- Module exists: false
- Receipt:
  `runs/unity-build-linux-server-2026-07-27t17-53-42-09-00/unity_build.md`
- Build output exists: false
- System modules installed or configuration changed: no

## Handoff and Cockpit

- Handoff:
  `runs/game-server-handoff-2026-07-27t17-57-48-09-00/server_handoff.md`
- Handoff status: `waiting_for_linux_server_build`
- Server-soak loop: `worker_blocked`
- Server-dependency isolation gate: passed
- Next prerequisite: install Linux Build Support on the build-authority editor,
  rerun the build, then regenerate the handoff
- x86_64 runner attachment is not presented as ready before that passing build

No generated `builds/linux-server` artifact is present or committed.
