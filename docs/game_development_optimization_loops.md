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

## Loop 4: Artist Procurement Readiness

- Command: `tools/channelctl asset procurement-check truth_pen`
- Reads the owner decision manifest without changing it.
- Shows the unresolved decision count and latest readiness receipt.
- Renders every unresolved decision as a read-only Studio checklist; the only
  checklist action opens the tracked owner intake guide.
- Groups checklist items by decision area and pairs the exact field path with
  Korean owner guidance while retaining the original validator message.
- Shows total and per-area completion for the 16 canonical fields. Unknown or
  structural errors make progress indeterminate instead of guessing.
- Can copy a blank response worksheet containing only unresolved canonical
  field names and repository-safe guidance. Stored values and validator
  messages are omitted; complete or indeterminate states disable the action.
- Keeps all artist contact blocked until the check passes.
- Runs the check when no current receipt exists. When a matching FAIL receipt
  already exists, the next action opens the owner decision intake guide instead
  of regenerating the same receipt.
- A decision that evaluates ready still requires a matching PASS receipt before
  the workflow advances beyond procurement.
- If a current FAIL receipt exists but the owner intake guide is missing, the
  next action remains explicitly blocked until the tracked guide is restored.

This loop never contacts an artist, approves a budget, or authorizes artwork.
Even after proposal-only outreach passes, artwork remains blocked until a signed
agreement and source Gate A `PASS` exist.

## Loop 5: Agent Progress Visibility

- Source: `memory/company/jobs/jobs.json`
- UI surface: Production Cockpit and Task Tracker.
- Shows active jobs, latest command, receipts, artifacts, and recent events.
- When no Studio job entry exists, the latest closed task counts only if its
  board status is verification-passed and its repository-relative verification
  receipt still exists and records `Status: passed`. This preserves progress
  visibility without inventing a job.

Use this when the user needs to see whether a task is running, blocked, failed, or completed with evidence.

## Next-Best Action

The Production Cockpit exposes `nextBestAction` from the current game production state.

Priority order:

1. Restore readiness if the validation chain is incomplete.
2. Create the play/capture/feedback loop.
3. Route open feedback into QA, implementation, and review work orders.
4. Run/review/verify assigned game work.
5. Resolve owner-controlled artist procurement decisions and rerun the read-only check.
6. Prepare the first asset pipeline packet.
7. Create or refresh the x86_64 server handoff only when the handoff receipt is missing.
8. Inspect job receipts and continue agent implementation work.

External dependency rule: a missing x86_64 runner must not trap the user in a dead-end next action if local Unity, feedback, or agent work can continue.
Procurement rule: a blocked readiness check is actionable validation, not authorization to contact an artist or request artwork.
