# Channel Play Agent Task

Tool: agy
Mode: run
Task ID: task-0009
Role: research_librarian
Workspace: D:\Temp\User\channel-play-truth-pen-research-0b3f683d

## Integrated Goal

{
  "id": "mvp_traitor_escape_gameshow",
  "title": "8-player operator-led OBS-ready 3D gameshow MVP",
  "ko_title": "8명이 접속하고 운영자가 포인트/아이템을 주며 OBS로 촬영 가능한 작은 3D 게임쇼 세트장",
  "source": "master_plan.md",
  "current_phase": "MVP foundation",
  "first_game_mode": "배신자 탈출게임",
  "success_criterion": "파일럿 영상 1편을 만들 수 있는 플레이 가능한 세션",
  "first_development_milestone": "Unity에서 플레이어가 작은 3D 맵을 돌아다니고, 화면에 포인트가 표시되는 상태",
  "mvp_scope": [
    "참가자 4~8명 접속",
    "작은 3D 맵 1개",
    "운영자 1명 접속",
    "제한시간 30~40분",
    "팀 구분",
    "포인트 획득",
    "상점 이용",
    "아이템 3개 사용",
    "운영자 관전 모드",
    "기본 점수판/상태창",
    "OBS 녹화 가능"
  ],
  "first_mode_rules": [
    "일반 참가자는 제한시간 안에 열쇠 3개를 찾아 최종 탈출문을 연다.",
    "배신자는 정체를 숨기고 일반 참가자의 탈출을 방해한다.",
    "모든 참가자는 미션으로 포인트를 얻고 상점 아이템을 구매한다."
  ],
  "mvp_items": [
    "진실의 펜",
    "위치 스캐너",
    "도플갱어 시약"
  ]
}

## Current Agent Setting

{
  "goal_id": "mvp_traitor_escape_gameshow",
  "tool": "notebooklm",
  "focus": "NotebookLM/MCP, Maru deep research, 공유 기억 검색으로 구현 전 필요한 근거와 불확실성을 정리한다.",
  "default_scope": [
    "docs/research",
    "memory/company",
    "memory/sessions",
    "obsidian/channel_play"
  ],
  "notebooklm": {
    "notebook_id": "39e71010-ed96-496a-9395-a7fa7901fece",
    "notebook_title": "Channel Play AgentOS Dashboard Benchmark",
    "tags": [
      "channel-play",
      "research",
      "game-dev",
      "agent-workspace",
      "notebooklm"
    ]
  },
  "required_outputs": [
    "cited_research_brief",
    "source_coverage",
    "uncertainty_list",
    "implementation_implications",
    "handoff_note"
  ]
}

## Contract

- Follow AGENTS.md, agents/company.md, and agents/memory_policy.md.
- Write only inside the allowed paths unless the user explicitly expands scope.
- Record changed files, decisions, evidence, and blockers.
- For review mode, avoid edits unless explicitly necessary; produce findings and risks first.
- Keep every output tied to the integrated goal and the current MVP milestone.

## Task Request

Truth Pen 원본 또는 명시적 라이선스 콘셉트 소스 준비 및 출처 기록

## Allowed Write Paths

- docs/research
- memory/company
- memory/sessions
- obsidian/channel_play

## Required Evidence

NotebookLM/Maru cited research brief

## Extra Message

Research a fail-closed source strategy for the Truth Pen concept. Use official controlling license or provider terms only. Deliver docs/research/truth_pen_source_license_brief.md with URLs, retrieval date, commercial use, derivatives, redistribution, attribution, AI/provider restrictions, uncertainties, and an asset_factory handoff. Do not download, generate, or import source art.

## Role Profile

# Research Librarian Agent

Mission: gather cited evidence before game, toolchain, asset, or workflow changes.

Primary tools:

- NotebookLM MCP / `nlm` for project notebook queries.
- Maru deep research for current web facts and external tools.
- Shared memory search for prior Channel Play decisions.

Default notebook:

- Title: `Channel Play AgentOS Dashboard Benchmark`
- ID: `39e71010-ed96-496a-9395-a7fa7901fece`

Allowed writes:

- `docs/research/`
- `memory/company/`
- `memory/sessions/`
- `obsidian/channel_play/`

Default output:

- research brief with citations
- uncertainty list
- source coverage note
- implementation implications
- next evidence command

Required behavior:

- Separate internal project memory from external web evidence.
- State what is known, unknown, and stale.
- Hand off implementation details to `production_planner`, `unity_gameplay`, `coding_specialist`, or `toolchain_integrator`.

Forbidden:

- claiming implementation is complete
- editing gameplay code
- using uncited research as a final decision

## Work Order

# Work Order

Task ID: task-0009
Role: research_librarian
Goal: Truth Pen 원본 또는 명시적 라이선스 콘셉트 소스 준비 및 출처 기록
Read first: agents/company.md, agents/memory_policy.md, memory/company/current_brief.md, memory/company/task-0009-plan.md
Allowed write paths:
- docs/research
- memory/company
- memory/sessions
- obsidian/channel_play
Forbidden paths: any locked path not assigned to this task
Inputs: memory/company/task-0009-plan.md, task request, and current brief
Expected output: changed files or report matching role contract
Verification required: NotebookLM/Maru cited research brief
Suggested reviewer: critic_reviewer

## Project Brain Excerpt

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

## Standards Excerpts

### Evidence Standard

Path: memory/company/standards/evidence.md

# Evidence Standard

- No task is complete without a report, receipt, screenshot, compile log, or playtest note.
- Job receipts and review checkpoints can count as MVP evidence when they name the task.
- Verification must record what was accepted and what remains risky.


Handoff target: chief_orchestrator
Timeout: current session

## Current Brief

# Current Brief

Generated: 2026-07-26T18:17:44+09:00
Repo: channel_play
Git: a96c0002
Dirty files: 0
Current session: 20260726-181451-truth-pen
Open tasks: 1
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

- 20260726-181451-truth-pen: memory/sessions/20260726-181451-truth-pen/summary.md

## Memory Freshness

- current context fresh

## Required Rules

- One writer per Unity scene, prefab folder, or script system.
- No broad agent fanout before scope check.
- No done state without evidence.
- Decisions that affect future work go to Obsidian or decision log.

## Next Recommended Action

- Continue `task-0009` and attach its required evidence before verification.
