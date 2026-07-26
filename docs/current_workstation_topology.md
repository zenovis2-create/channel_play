# Channel Play Workstation Topology

Updated: 2026-06-03

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
- Current gdx1 server-run receipt: `runs/gdx-run-server-2026-06-03t20-36-52-09-00/gdx_run-server.md`
- Linux server build receipt: `runs/unity-build-linux-server-2026-06-03t20-33-36-09-00/unity_build.md`

## Operating Rules

- Do Unity work on Mac Studio first.
- Do not route critical Unity runtime execution to gdx1.
- gdx1 tasks must be AI/ops/log/research oriented unless a compatible runner script exists.
- Real remote Unity server soak requires an x86_64 Linux host.
- Every compile, build, capture, gdx operation, and feedback loop must leave a receipt.
