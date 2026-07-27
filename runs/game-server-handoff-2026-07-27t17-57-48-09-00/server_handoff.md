# x86_64 Server Soak Handoff

Checked: 2026-07-27T17:57:48+09:00
Status: waiting_for_linux_server_build

## Current Topology

- Mac Studio: Unity editor, local playtest, capture, Mac/Linux build authority.
- gdx1: ARM/aarch64 AI/ops worker, repo sync, log collection.
- x86_64 Linux runner: required for real Unity dedicated server soak.

## Required Runner Contract

- Architecture: x86_64 Linux.
- Access: SSH or host-runner endpoint.
- Inputs: repo checkout, Linux dedicated server build, bot runner script.
- Outputs: server log, bot log, soak receipt, captured failure reasons.

## Current Build Evidence

- Linux server build receipt: runs/unity-build-linux-server-2026-07-27t17-53-42-09-00/unity_build.md

## Next Action

- Resolve the blocked or failed Linux server build receipt above, rerun `python tools/channelctl unity build linux-server`, then regenerate this handoff.
