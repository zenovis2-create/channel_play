# Session Context

Session ID: 20260727-175137-cross-platform-linux-server-build-prefli
Goal: Cross-platform Linux server build preflight and current handoff evidence
Started: 2026-07-27T17:51:37+09:00

## Starting State

- Created by `channelctl company session start`.

## Scope

- Correct Unity Linux Build Support path resolution across supported editor
  layouts.
- Make missing-editor and missing-module receipts accurate and actionable.
- Run only the local preflight; do not install modules or alter the host.
- Refresh x86_64 handoff evidence to bind the current result.
- Keep handoff and Production Cockpit in build-blocked state until the latest
  Linux server receipt proves a successful output.

## Selected Agents

- coding_specialist: implementation and automated evidence
- critic_reviewer: findings-first reliability review

## Required Evidence

- Cross-platform path and blocked-receipt tests
- Real local linux-server preflight receipt
- Refreshed x86_64 handoff referencing that receipt
- Focused/full suites, syntax and diff checks
- Runtime receipt and findings-first review
