# Channel Play Agent Team Structure

Updated: 2026-06-03

This is the working company structure for building the Channel Play Unity MVP.

## Command Chain

1. `chief_orchestrator` owns the active objective, routing, job state, and user-facing completion.
2. `production_planner` turns rough intent into ordered work packets.
3. `research_librarian` gathers cited internal/external evidence before risky implementation.
4. `coding_specialist` implements scoped code changes.
5. Domain agents handle game design, Unity, assets, audio, QA, performance, and operations.
6. `critic_reviewer` checks risk and missing evidence before closure.
7. `librarian` records decisions, session notes, and durable memory.

## New Structural Roles

| Agent | Purpose | Default Tool | Primary Evidence |
|---|---|---:|---|
| `production_planner` | Work breakdown, sequencing, agent assignment, evidence design | Codex SDK | production plan + assignment matrix |
| `research_librarian` | NotebookLM/Maru/project-memory research before implementation | NotebookLM | cited research brief + uncertainty list |
| `coding_specialist` | Scoped implementation in Studio, Unity C#, CLI, Docker, SDK glue | Codex SDK | code diff + tests/runtime evidence |
| `toolchain_integrator` | Adapter, Docker, host-runner, SDK, Obsidian, Unity/Blender wiring | Codex SDK | adapter/runtime receipt |
| `operator_broadcast_designer` | OBS/operator/player show flow for pilot video | Hermes | operator flow + capture checklist |

## Routing Rules

- Planning/process/dependency/roadmap requests route to `production_planner`.
- Research/source/citation/NotebookLM/latest/benchmark requests route to `research_librarian`.
- Code/fix/refactor/SDK/API/UI implementation requests route to `coding_specialist`.
- Docker/host-runner/Codex SDK/Hermes/agy/OpenClaw/Unity-Blender pipeline requests route to `toolchain_integrator`.
- OBS/operator/broadcast/pilot show-control requests route to `operator_broadcast_designer`.

## Completion Contract

Every agent result must answer:

- What was requested?
- What did this agent do?
- Where is the answer or artifact?
- What evidence proves it?
- What is the next command or next agent?

The Studio task card must expose the answer path directly through `답변 보기`.
