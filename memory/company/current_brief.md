# Current Brief

Generated: 2026-06-01T15:08:53+09:00
Repo: /Volumes/AI2/channel_play
Git: cdc4d05
Dirty files: 12
Current session: none
Open tasks: 0
Active locks: 0
gdx1: online_via_tailscale / ok

## Current Context

# Current Context

Project: `channel_play`

Date: 2026-06-01

Current production direction:

- Unity game is the product.
- Channel Play Studio is the production cockpit.
- Channel Play Agent Company is the team/orchestration layer.
- Mac Studio is the Unity/Blender/OBS implementation machine.
- gdx1 is reserved for server, bot, soak-test, and background worker jobs after SSH authentication is fixed.

Current constraints:

- One writer per Unity scene, prefab folder, or script system.
- Agent work must produce evidence before completion.
- Shared memory must be updated after meaningful decisions.

## Registered Agents

- chief_orchestrator: agents/orchestrator.agent.md
- game_director: agents/roles/game_director.agent.md
- unity_architect: agents/roles/unity_architect.agent.md
- unity_gameplay: agents/roles/unity_gameplay.agent.md
- multiplayer_server: agents/roles/multiplayer_server.agent.md
- asset_factory: agents/roles/asset_factory.agent.md
- technical_artist_blender: agents/roles/technical_artist_blender.agent.md
- sound_designer: agents/roles/sound_designer.agent.md
- qa_playtest: agents/roles/qa_playtest.agent.md
- performance_build: agents/roles/performance_build.agent.md
- gdx_ops: agents/roles/gdx_ops.agent.md
- librarian: agents/roles/librarian.agent.md
- critic_reviewer: agents/roles/critic_reviewer.agent.md

## Active Locks

- none

## Git Working Tree

-  M docs/channel_play_agent_company_checklist.md
-  M docs/channel_play_agent_company_implementation_plan.md
-  M memory/company/state.json
-  M tools/studio/company/gdx.py
- ?? runs/gdx-collect-logs-2026-06-01t15-08-09-09-00/
- ?? runs/gdx-probe-2026-06-01t15-08-04-09-00/
- ?? runs/gdx-run-bots-2026-06-01t15-08-08-09-00/
- ?? runs/gdx-run-server-2026-06-01t15-08-08-09-00/
- ?? runs/gdx-sync-2026-06-01t15-08-06-09-00/
- ?? tools/__pycache__/
- ?? tools/studio/company/__pycache__/
- ?? tools/studio/company/tests/__pycache__/

## Latest Session

- 20260601-145709-process-feedback-md: memory/sessions/20260601-145709-process-feedback-md/summary.md

## Memory Freshness

- current context fresh

## Required Rules

- One writer per Unity scene, prefab folder, or script system.
- No broad agent fanout before scope check.
- No done state without evidence.
- Decisions that affect future work go to Obsidian or decision log.

## Next Recommended Action

- Implement `company session start/end`, then work orders and locks.
