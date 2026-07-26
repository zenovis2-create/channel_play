# Current Brief

Generated: 2026-07-26T18:02:50+09:00
Repo: channel_play
Git: 309dab84
Dirty files: 0
Current session: none
Open tasks: 0
Active locks: 0
gdx1: online_via_tailscale / auth_blocked

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

Integrated goal:

- ID: `mvp_traitor_escape_gameshow`
- Goal: 8명이 접속하고 운영자가 포인트/아이템을 주며 OBS로 촬영 가능한 작은 3D 게임쇼 세트장을 만든다.
- First game mode: `배신자 탈출게임`
- Success criterion: 게임 출시가 아니라 파일럿 영상 1편을 만들 수 있는 플레이 가능한 세션.
- First development milestone: Unity에서 플레이어가 작은 3D 맵을 돌아다니고, 화면에 포인트가 표시되는 상태.

MVP scope:

- 참가자 4~8명 접속
- 작은 3D 맵 1개
- 운영자 1명 접속
- 제한시간 30~40분
- 팀 구분
- 포인트 획득
- 상점 이용
- 아이템 3개 사용: 진실의 펜, 위치 스캐너, 도플갱어 시약
- 운영자 관전 모드
- 기본 점수판/상태창
- OBS 녹화 가능

First mode rules:

- 일반 참가자는 제한시간 안에 열쇠 3개를 찾아 최종 탈출문을 연다.
- 배신자는 정체를 숨기고 일반 참가자의 탈출을 방해한다.
- 모든 참가자는 미션으로 포인트를 얻고 상점 아이템을 구매한다.

Current constraints:

- One writer per Unity scene, prefab folder, or script system.
- Agent work must produce evidence before completion.
- Shared memory must be updated after meaningful decisions.
- Do not ask an agent to build the whole game at once. Split work into scoped, verifiable tasks.

## Project Brain

# Project Brain

Generated: 2026-07-26T16:33:49+09:00

## Current Goal

8명이 접속하고 운영자가 포인트/아이템을 주며 OBS로 촬영 가능한 작은 3D 게임쇼 세트장

## MVP Scope

- 참가자 4~8명 접속
- 작은 3D 맵 1개
- 운영자 1명 접속
- 제한시간 30~40분
- 팀 구분
- 포인트 획득
- 상점 이용
- 아이템 3개 사용

## Style

- Korean-first planning and status language.
- Quiet production UI, visible evidence, no hidden automation.
- Every agent output should name the task, changed files, evidence, and next risk.

## Constraints

- Studio owns orchestration state; external AI tools are adapters.
- gdx1 is optional until health is verified.
- Unity work needs compile, playtest, screenshot, or receipt evidence.

## Forbidden Actions

- Do not mark done without evidence or receipt.
- Do not edit broad unrelated Unity folders.
- Do not re-enable Claude as a default adapter unless the user requests it.
- Do not use non-loopback Studio execution APIs without an explicit trusted-network setting.

## Standards Registry

- Asset Import Standard: memory/company/standards/asset_import.md
- Evidence Standard: memory/company/standards/evidence.md
- GDX Worker Standard: memory/company/standards/gdx_worker.md
- Unity Scene And Prefab Ownership Standard: memory/company/standards/unity_scene_prefab_ownership.md
- Unity Scripts Standard: memory/company/standards/unity_scripts.md

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
- research_librarian: agents/roles/research_librarian.agent.md
- production_planner: agents/roles/production_planner.agent.md
- coding_specialist: agents/roles/coding_specialist.agent.md
- toolchain_integrator: agents/roles/toolchain_integrator.agent.md
- operator_broadcast_designer: agents/roles/operator_broadcast_designer.agent.md
- critic_reviewer: agents/roles/critic_reviewer.agent.md

## Active Locks

- none

## Git Working Tree

- clean

## Latest Session

- 20260726-163349-process-feedback-md: memory/sessions/20260726-163349-process-feedback-md/summary.md

## Memory Freshness

- current context fresh

## Required Rules

- One writer per Unity scene, prefab folder, or script system.
- No broad agent fanout before scope check.
- No done state without evidence.
- Decisions that affect future work go to Obsidian or decision log.

## Next Recommended Action

- Create the next scoped work order with `tools/channelctl company plan <request>`.
