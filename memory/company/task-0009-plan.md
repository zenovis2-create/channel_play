# Task Plan

Task ID: task-0009
Status: planned
Suggested agent: research_librarian
Suggested reviewer: critic_reviewer
Required evidence: NotebookLM/Maru cited research brief

## Request

Truth Pen 원본 또는 명시적 라이선스 콘셉트 소스 준비 및 출처 기록

## Allowed Write Paths

- docs/research
- memory/company
- memory/sessions
- obsidian/channel_play

## Required Deliverable

- Create `docs/research/truth_pen_source_license_brief.md`.
- Prefer an original Channel Play concept; otherwise document an explicitly
  licensed source suitable for commercial game production and modification.
- Do not download, generate, or import source art until the license decision is
  reviewed.

## Acceptance Checklist

- Record source URL or provider, creator, license name, retrieval date, and a
  citation to the controlling terms.
- State commercial-use, derivative-work, redistribution, attribution, and
  generative-provider restrictions separately.
- Reject sources with unknown provenance, watermarks, trademarked branding, or
  terms that cannot be verified.
- Name one approved source strategy or explicitly report that no safe source
  was found.
- Include a handoff note for `asset_factory`; this task does not write to
  `asset_pipeline`.

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
