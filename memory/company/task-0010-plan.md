# Task Plan

Task ID: task-0010
Status: implementation_approved_and_verified
Suggested agent: coding_specialist
Suggested reviewer: critic_reviewer
Required evidence: unit tests, fail-closed Gate A/Gate B runtime receipts, and critic review

## Request

code license Gate A validator for Truth Pen asset generation and fail-closed production handoff

## Allowed Write Paths

- tools/studio/company
- tools/channelctl
- asset_pipeline
- memory/company
- memory/sessions
- reviews
- runs
- docs/research

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

### Asset Import Standard

Path: memory/company/standards/asset_import.md

# Asset Import Standard

- Track source, license, import path, preview, and acceptance status for every asset.
- Keep Blender/2D-to-3D outputs in the asset pipeline until accepted.
- Imported assets need a short readability and scale check.

## Implementation Decision

- Gate A authorizes only source creation/download. Gate B binds the exact source
  path/hash and one approved 3D provider before production.
- Require structured critic JSON bound to the asset, task, gate, current
  manifest SHA-256, reviewer role, review time, and authorization scope.
- Keep lifecycle `status` orthogonal to evaluator-owned source/production gate
  state.
- Make all scaffolds display Gate A/Gate B blocks dynamically.
- Reject absolute or changed production sources, provider mismatches,
  `auto`/`both`, and unreviewed local fallback.
- Keep Truth Pen unselected and blocked; do not invent creator, contract,
  account, source work, or approval evidence.
