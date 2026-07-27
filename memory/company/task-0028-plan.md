# Task Plan

Task ID: task-0028
Status: complete
Suggested agent: coding_specialist
Suggested reviewer: critic_reviewer
Required evidence: preview TTL contract, memory-only manual recovery state tests, status-only retry UI contracts, pending/success/expiry coverage, JavaScript syntax, Chrome preview-only proof, unchanged real hashes, focused/full suites, runtime receipt, and findings-first security review

## Request

Add a user-triggered result-only recovery affordance for ambiguous Truth Pen owner saves. Return the server result-store TTL with valid preview grants. After the existing automatic status lookup is pending, unavailable, or temporarily fails, retain only asset ID, random apply-attempt ID, preview manifest hash, canonical changed field names/count, and expiry in browser memory; never retain answer values or use browser storage. Render a clearly labeled button that only calls the protected apply-status endpoint and never calls apply. Keep it available until the server-aligned TTL expires, then clear it and require manual manifest inspection. A recovered result must pass the existing preview-bound verification before clearing the input and refreshing state; pending, missing, malformed, mismatched, or network-failed results keep the possibly-saved/no-retry warning. Preserve the one-time preview grant, explicit owner confirmation, atomic save, separate PASS-receipt gate, and zero contact or receipt side effects. Add server/UI contract tests, manual recovery success/pending/expiry coverage, JavaScript syntax, Chrome preview-only proof with zero apply/status calls, unchanged real manifest and receipt hashes, focused/full suites, runtime receipt, and findings-first security review.

## Allowed Write Paths

- tools/studio/workspace_server.py
- tools/studio/app
- tools/studio/tests
- docs
- memory/company
- memory/sessions
- reviews
- runs

## Acceptance Criteria

1. A valid preview grant reports the server result-recovery TTL, bounded to a
   positive finite integer. Invalid and no-op previews expose no recovery TTL.
2. The browser keeps at most one recovery record containing only asset ID,
   32-hex attempt ID, preview hash, canonical field names/count, and expiry.
3. The existing automatic recovery still runs once. If it cannot confirm a
   result, the UI exposes a user-triggered status-only lookup until expiry.
4. The manual button never sends answers, grants, confirmation text, or an
   apply request. It cannot extend the original server-aligned expiry.
5. A recovered result must pass the existing preview-bound verification before
   clearing input or refreshing state. Pending, missing, malformed, mismatched,
   expired, and network-failed results remain no-retry/manual-diff states.
6. Recovery state is cleared after verified/mismatched completion, expiry,
   successful primary response, or page reload; no browser storage is used.
7. Artist contact remains false and no procurement receipt is created.

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

### GDX Worker Standard

Path: memory/company/standards/gdx_worker.md

# GDX Worker Standard

- Treat gdx1 as an optional worker until SSH health is confirmed.
- Remote sync, server runs, bots, and log collection must leave run receipts.
- Do not assume gdx1 availability when planning critical local work.
