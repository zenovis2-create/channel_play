# Channel Play Game Development Optimization Loops

Updated: 2026-06-03

## Purpose

This document defines the production loops used by Channel Play Studio after the workstation topology was corrected.

## Loop 1: Play, Capture, Feedback

- Command: `tools/channelctl game feedback-loop`
- Runs Unity playtest smoke.
- Renders `School_MVP` from `Operator_Overview_Camera` inside Unity.
- Creates a feedback note linked to the latest capture.
- Next command: `tools/channelctl feedback process <feedback.md>`

Use this when the user reviews the game visually and wants a captured issue turned into agent work.
The loop fails closed if the playtest fails or Unity cannot produce a valid,
non-blank PNG. It never captures unrelated desktop applications.

`feedback process` is a routing step, not a fake completion step. It creates QA, implementation, and review work orders and leaves them assigned until an agent run, review, and Unity evidence exist.

## Loop 2: 2D to 3D Asset Factory

- Command: `tools/channelctl asset prepare <asset-id>`
- Creates source intake notes.
- Creates 2D-to-3D generation handoff.
- Creates Blender cleanup template.
- Creates Unity import manifest.
- Updates `asset_pipeline/index.json`.

Use this for props, level dressings, interactables, and visual assets that move from concept/source image into Unity.

## Loop 3: x86_64 Server Soak Handoff

- Command: `tools/channelctl game server-handoff`
- Writes the current server-soak handoff receipt.
- Keeps the Mac Studio/gdx1/x86 runner boundary explicit.

Current constraint: gdx1 is ARM/aarch64 and should be used for AI/ops, repo sync, and logs. Real Unity dedicated server soak requires an x86_64 Linux runner or cloud host.

## Loop 4: Agent Progress Visibility

- Source: `memory/company/jobs/jobs.json`
- UI surface: Production Cockpit and Task Tracker.
- Shows active jobs, latest command, receipts, artifacts, and recent events.

Use this when the user needs to see whether a task is running, blocked, failed, or completed with evidence.

## Next-Best Action

The Production Cockpit exposes `nextBestAction` from the current game production state.

Priority order:

1. Restore readiness if the validation chain is incomplete.
2. Create the play/capture/feedback loop.
3. Route open feedback into QA, implementation, and review work orders.
4. Run/review/verify assigned game work.
5. Prepare the first asset pipeline packet.
6. Create or refresh the x86_64 server handoff only when the handoff receipt is missing.
7. Inspect job receipts and continue agent implementation work.

External dependency rule: a missing x86_64 runner must not trap the user in a dead-end next action if local Unity, feedback, or agent work can continue.
