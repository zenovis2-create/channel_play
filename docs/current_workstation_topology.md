# Channel Play Workstation Topology

Updated: 2026-07-27

## Decision

Use Mac Studio as the Unity production authority.

Use gdx1 as an ARM/aarch64 AI/ops worker, not as the default Unity server runner.

## Machine Roles

| Machine | Role | Use |
|---|---|---|
| Mac Studio M2 Ultra 64GB | Unity production authority | Unity Editor, compile, playtest smoke, captures, Mac build, Linux dedicated server build, Blender/OBS host work |
| ASUS GX10 gdx1 | Remote AI/ops worker | SSH probe, repo sync, log collection, OpenClaw/gdx ops, long-running research or background jobs |
| Future x86_64 Linux runner | Server soak target | Run Unity Linux dedicated server and bot soak tests |

## Evidence

- gdx1 architecture: `aarch64`
- Unity Linux dedicated server output: `x86-64`
- Current gdx1 server-run receipt:
  `runs/gdx-run-server-2026-06-01t14-51-42-09-00/gdx_run-server.md`
- Current Linux server build preflight:
  `runs/unity-build-linux-server-2026-07-27t17-53-42-09-00/unity_build.md`
- Current x86_64 handoff:
  `runs/game-server-handoff-2026-07-27t17-57-48-09-00/server_handoff.md`
- The Windows Unity editor currently lacks Linux Build Support, so no current
  Linux server binary exists yet.

## Operating Rules

- Do Unity work on Mac Studio first.
- Install Linux Build Support for the active build-authority editor before
  rerunning `python tools/channelctl unity build linux-server`.
- Do not route critical Unity runtime execution to gdx1.
- gdx1 tasks must be AI/ops/log/research oriented unless a compatible runner script exists.
- Real remote Unity server soak requires an x86_64 Linux host.
- Every compile, build, capture, gdx operation, and feedback loop must leave a receipt.
