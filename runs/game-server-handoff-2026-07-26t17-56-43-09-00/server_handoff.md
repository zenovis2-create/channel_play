# x86_64 Server Soak Handoff

Checked: 2026-07-26T17:56:43+09:00
Status: waiting_for_x86_64_runner

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

- Linux server build receipt: missing; run tools/channelctl unity build linux-server

## Next Action

- Attach an x86_64 Linux runner or cloud host, then map gdx.runServer/gdx.runBots to that runner.
