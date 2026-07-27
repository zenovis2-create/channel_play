# Task Plan

Task ID: task-0029
Status: complete
Suggested agent: coding_specialist
Suggested reviewer: critic_reviewer
Required evidence: cross-platform path tests, missing-editor and blocked-receipt tests, real local preflight receipt, refreshed server-handoff receipt, focused/full suites, syntax and diff checks, runtime receipt, and findings-first review

## Request

Fix the Unity Linux dedicated-server build preflight so Windows, macOS, and Linux editor layouts resolve the installed PlaybackEngines/LinuxStandaloneSupport module correctly; fail clearly when the active Unity editor is missing; replace stale Mac-only and unimplemented-method guidance with host-specific Unity Hub module instructions and the exact rerun command; add path and blocked-receipt regression tests; run the real local linux-server build preflight without installing modules or changing system configuration; refresh the x86_64 server handoff so it references the current receipt; preserve builds as ignored artifacts and commit only scoped source, tests, task records, and receipts.

## Allowed Write Paths

- tools/studio/company/unity.py
- tools/studio/company/game_loops.py
- tools/studio/company/game_production.py
- tools/studio/company/tests
- memory/company
- memory/sessions
- docs
- runs

## Acceptance Criteria

1. Windows and Linux editor executables resolve Linux Build Support beneath
   `Editor/Data/PlaybackEngines/LinuxStandaloneSupport`; macOS app bundles
   resolve it beneath `Unity.app/Contents/PlaybackEngines`.
2. A missing active Unity editor fails before creating a misleading
   module-missing receipt.
3. A missing module receipt names the actual host platform, active editor,
   expected module path, Unity Hub module action, and exact rerun command. It
   must not claim the already-implemented build method is missing.
4. The command never installs Unity modules or changes system configuration.
5. The real local preflight records the current missing-module result, and a
   refreshed x86_64 handoff references that exact receipt without claiming the
   runner is the next dependency before a passing build exists.
6. Focused and full automated suites, Python syntax, JSON validation, and diff
   hygiene pass. No generated build output is committed.

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

### Unity Scripts Standard

Path: memory/company/standards/unity_scripts.md

# Unity Scripts Standard

- Keep gameplay scripts under the task's allowed Unity script folder.
- Prefer small MonoBehaviour boundaries with explicit serialized fields.
- Do not introduce broad Unity package churn without a separate task.
- Every script change needs compile or playtest evidence.

### Unity Scene And Prefab Ownership Standard

Path: memory/company/standards/unity_scene_prefab_ownership.md

# Unity Scene And Prefab Ownership Standard

- One active owner per scene, prefab folder, or script system.
- Do not edit unrelated scenes or prefabs while implementing script-only tasks.
- Record ownership assumptions in the work order when touching Unity assets.

### GDX Worker Standard

Path: memory/company/standards/gdx_worker.md

# GDX Worker Standard

- Treat gdx1 as an optional worker until SSH health is confirmed.
- Remote sync, server runs, bots, and log collection must leave run receipts.
- Do not assume gdx1 availability when planning critical local work.
