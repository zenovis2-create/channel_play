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
Verification required: Official primary-source brief, evidence decision, and critic receipt (see `memory/company/task-0009-evidence-decision.md`)
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
