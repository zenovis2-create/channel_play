# Channel Play Agent Company Plan

Updated: 2026-06-01

## 0. Decision

`Channel Play Studio` needs an agent-company layer.

The right model is not "many AI tools in one launcher." It is a small production company:

- one orchestrator AI that decides who should work
- role-specific agents with different skills, soul, constraints, and write scopes
- shared project memory that every agent reads from and writes back to
- explicit work orders, handoff contracts, review gates, and verification evidence
- a human executive producer who gives taste, priority, final acceptance, and visual feedback

For `channel_play`, this layer should be called:

```text
Channel Play Agent Company
```

It sits between the human, Unity, Obsidian, AI tools, Blender, asset generators, gdx1, and GitHub.

## 1. Why This Is Needed

The current `Channel Play Studio` plan already separates tools and lanes, but that is not enough.

Without an agent-company layer, the risks are:

- every agent reads a different memory
- multiple agents edit the same Unity scene or script
- generated assets lose their source, license, scale, or review history
- feedback from screenshots turns into vague chat instead of actionable tasks
- Claude/Codex/agy/Hermes/OpenClaw duplicate work
- gdx1 background work becomes disconnected from Mac Studio Unity work
- decisions stay in chat and disappear from future sessions

The paperclip lesson to reuse is concrete: orchestration rules must live in the actual execution path, not only in prompts or docs. Scope must be confirmed before fanout, and non-scout agents should not run broad work until the target root and task boundary are clear.

## 2. Company Structure

```text
Daehan
  -> Chief Orchestrator AI
      -> Game Director Agent
      -> Unity Architecture Agent
      -> Unity Gameplay Agent
      -> Multiplayer/Server Agent
      -> Technical Artist / Blender Agent
      -> Asset Factory Agent
      -> Sound Agent
      -> QA Playtest Agent
      -> Performance/Build Agent
      -> gdx1 Ops Agent
      -> Librarian / Memory Agent
      -> Critic / Review Agent
```

The orchestrator is not the best coder. Its job is to prevent chaos.

It decides:

- what memory is relevant
- which agent roles are needed
- which agent is allowed to write
- what each agent must produce
- what evidence is required before the task is done
- when to ask the human for taste or priority

## 3. Shared Memory Model

Use three memory layers.

### 3.1 Canonical Memory

Stored in Obsidian and committed to Git.

```text
obsidian/channel_play/
  00_Index.md
  01_Game_Design/
  02_Implementation/
  03_Assets/
  04_Sound/
  05_AI/
  06_Feedback/
  07_Sessions/
  08_Decisions/
  09_References/
```

Use this for:

- design decisions
- gameplay rules
- scene specs
- UX notes
- visual taste notes
- accepted/rejected asset notes
- sound direction
- long-term architecture decisions

### 3.2 Operational Memory

Stored as machine-readable files.

```text
memory/company/
  state.json
  agent_registry.json
  task_board.json
  locks.json
  current_context.md
  decision_log.md
  handoff_log.md

memory/sessions/
  2026-06-01-session-001/
    context.md
    work_orders/
    agent_reports/
    verification/
```

Use this for:

- active task state
- current session context
- agent assignments
- locks and write scopes
- work order status
- verification status
- latest known gdx1 state

### 3.3 Evidence Memory

Stored in the repo but separated from canonical design notes.

```text
runs/
reviews/
artifacts/
logs/
asset_pipeline/
```

Use this for:

- screenshots
- annotated feedback
- Unity compile logs
- build logs
- playtest recordings
- Blender cleanup reports
- asset generation outputs
- gdx1 server/bot test logs

## 4. Agent File Layout

Create actual role files so the orchestrator can load them consistently.

```text
agents/
  company.md
  memory_policy.md
  orchestrator.agent.md
  roles/
    game_director.agent.md
    unity_architect.agent.md
    unity_gameplay.agent.md
    multiplayer_server.agent.md
    technical_artist_blender.agent.md
    asset_factory.agent.md
    sound_designer.agent.md
    qa_playtest.agent.md
    performance_build.agent.md
    gdx_ops.agent.md
    librarian.agent.md
    critic_reviewer.agent.md
  skills/
  souls/
```

Each role file should define:

- mission
- allowed tools
- required memory reads
- allowed write scope
- forbidden actions
- input contract
- output contract
- done criteria
- handoff target

## 5. Orchestrator Workflow

Every non-trivial task should pass through this workflow.

```text
Human request
-> Orchestrator intake
-> Target scope check
-> Shared memory brief
-> Agent selection
-> Work orders
-> Agent execution
-> Review/critique
-> Integration
-> Unity or asset verification
-> Human feedback
-> Memory update
-> Git commit/push
```

### 5.1 Intake

The orchestrator creates:

```text
memory/sessions/<session-id>/context.md
memory/sessions/<session-id>/work_orders/
```

It records:

- user goal
- target area
- expected output
- known blockers
- files likely to change
- needed agents
- verification method

### 5.2 Scope Check

Before fanout:

- confirm repo root is `/Volumes/AI2/channel_play`
- confirm target Unity scene, system, asset, or doc area
- check `git status`
- check active locks
- decide whether this is a scout task or writer task

If target scope is unclear, only a scout/librarian agent may run.

### 5.3 Agent Selection

Default rule:

- 1 writer max
- 1 reviewer max
- 1 specialist max

Only increase team size if the work has separate domains, such as Unity code plus Blender cleanup plus QA.

### 5.4 Work Order Contract

Each agent receives a work order:

```markdown
# Work Order

Task ID:
Role:
Goal:
Read first:
Allowed write paths:
Forbidden paths:
Inputs:
Expected output:
Verification required:
Handoff target:
Timeout:
```

### 5.5 Agent Report Contract

Each agent returns:

```markdown
# Agent Report

Task ID:
Role:
Status: done | blocked | needs_review

## Summary

## Files Read

## Files Changed

## Decisions

## Evidence

## Risks

## Handoff
```

## 6. Write Locks

Unity projects are collision-prone.

Use path-level locks:

```json
{
  "locks": [
    {
      "path": "Assets/_Project/Scenes/School_MVP.unity",
      "owner": "unity_gameplay",
      "task_id": "task-0007",
      "expires_at": "2026-06-01T18:00:00+09:00"
    }
  ]
}
```

Lock rules:

- one writer per Unity scene
- one writer per prefab folder
- one writer per C# system folder
- reviewers never edit locked paths
- asset generators write only under `asset_pipeline/`
- Blender cleanup writes only under the assigned asset folder
- orchestrator owns lock release after verification

## 7. Agent Roles

| Role | Main Job | Writes? | Default Tool |
|---|---|---:|---|
| Chief Orchestrator | break down work, assign agents, enforce memory/locks | limited | Codex/OpenClaw |
| Game Director | gameplay feel, user-facing rules, show format | no by default | Claude/Codex |
| Unity Architecture | data-driven Unity structure, ScriptableObjects, scene hygiene | yes when assigned | Codex |
| Unity Gameplay | movement, missions, items, UI, operator tools | yes | Codex |
| Multiplayer/Server | Netcode, headless server, gdx1 tests | yes | Codex/gdx1 |
| Technical Artist | Blender cleanup, scale, materials, collider proxies | yes in asset paths | Blender |
| Asset Factory | 2D/3D generation briefs, metadata, vendor wrapping | yes in asset paths | AI asset tools |
| Sound Designer | effect/sound briefs, cues, mix notes | limited | AI/audio tools |
| QA Playtest | screenshot/video review, bug reports, regression notes | no | agy/Codex |
| Performance/Build | compile/build/profiling, package size, frame checks | yes in tooling | Codex/gdx1 |
| gdx1 Ops | remote server, bot load, logs, soak test | yes on gdx1 | SSH/Tailscale |
| Librarian | Obsidian memory, decisions, session summaries | yes in docs/memory | Codex/Hermes |
| Critic/Reviewer | design/code risk review, second opinion | no by default | Claude |

## 8. `channelctl` Commands

Add a company namespace.

```bash
./tools/channelctl company status
./tools/channelctl company brief
./tools/channelctl company plan "<request>"
./tools/channelctl company assign <task-id> <role>
./tools/channelctl company lock <path> <owner>
./tools/channelctl company unlock <path>
./tools/channelctl company report <task-id>
./tools/channelctl company memory sync
./tools/channelctl company review <task-id>
```

MVP behavior:

- `status`: show active session, locks, agents, open tasks
- `brief`: generate current context packet from docs, memory, git status, and latest run
- `plan`: convert human request into work orders
- `assign`: create a role-specific prompt/work order file
- `memory sync`: update Obsidian session and decision files
- `review`: collect reports and determine whether verification is enough

## 9. Dashboard Additions

The Studio dashboard should show:

- current orchestrator task
- active team
- write locks
- latest agent reports
- memory freshness
- open decisions
- blocked tasks
- verification status
- gdx1 worker availability

Do not show chat transcripts as the primary memory.
Show structured state, evidence, and decisions.

## 10. MVP Build Order

Build in this order:

1. Create `agents/` role files and memory policy.
2. Create `memory/company/` state files.
3. Add `channelctl company status`.
4. Add `channelctl company brief`.
5. Add work order and report templates.
6. Add lock file management.
7. Add dashboard panel for agent company state.
8. Add Obsidian session sync.
9. Add first real workflow: screenshot feedback -> work order -> Codex implementation -> Claude review -> Unity check -> memory update.
10. Add gdx1 workflow after SSH authentication is fixed.

## 11. First Practical Team

For the next real `channel_play` implementation phase, start with this team:

```text
Chief Orchestrator
Unity Gameplay Agent
Unity Architecture Agent
QA Playtest Agent
Librarian Agent
Critic/Reviewer Agent
```

Add Technical Artist and Asset Factory when we start the first generated 3D prop.

Add gdx1 Ops only after SSH auth works.

## 12. Research Basis

This plan follows two practical principles from current multi-agent system guidance:

- orchestration must handle planning, policy, state management, and quality operations, not just agent routing
- shared memory needs boundaries, retention rules, and retrieval discipline, otherwise it becomes either noisy or fragmented

References checked on 2026-06-01:

- https://arxiv.org/html/2601.13671v1
- https://hindsight.vectorize.io/guides/2026/04/21/guide-building-multi-agent-systems-with-shared-memory
- https://github.com/microsoft/agent-framework

## 13. Bottom Line

`Channel Play Agent Company` should become the operating layer for the project.

The Unity game remains the product.
The Studio tool remains the cockpit.
The Agent Company is the team system that turns human feedback, shared memory, and specialized AI tools into controlled production work.

Implementation detail:

- `docs/channel_play_agent_company_implementation_plan.md`
- `docs/channel_play_agent_company_checklist.md`
