# Channel Play Agent Company Implementation Plan

Updated: 2026-06-01

## 0. Goal

Build the first working version of `Channel Play Agent Company`.

This is not a full autonomous company yet.
MVP means:

- shared memory exists
- agents have stable role files
- orchestrator can create a current brief
- orchestrator can create work orders
- path locks prevent conflicting writers
- agents return structured reports
- evidence is required before done
- dashboard can show company state

The Unity game remains the product.
The company layer exists only to make production faster and safer.

## 1. Current State

Already created:

```text
docs/channel_play_agent_company_plan.md
agents/
memory/company/
docs/channel_play_studio_plan.md
docs/channel_play_studio_plan.html
```

Known blocker:

```text
gdx1: network visible, SSH auth blocked
```

Immediate rule:

```text
Do not depend on gdx1 for MVP.
Design gdx1 as optional worker until SSH auth is fixed.
```

## 2. Implementation Principles

Use a boring stack first:

- Python 3 standard library
- JSON state files
- Markdown work orders and reports
- static HTML dashboard
- no database
- no always-on daemon
- no concurrent auto-editing

Hard rules:

- one writer per locked path
- no broad agent fanout before scope check
- no done state without evidence
- no chat-only decisions
- no generated asset without metadata
- no gdx1 job unless auth probe passes

## 3. Target File Layout

```text
tools/
  channelctl
  studio/
    company/
      __init__.py
      cli.py
      paths.py
      state.py
      brief.py
      planner.py
      locks.py
      reports.py
      dashboard.py
    templates/
      work_order.md
      agent_report.md
      session_context.md

memory/company/
  state.json
  agent_registry.json
  task_board.json
  locks.json
  current_context.md
  decision_log.md
  handoff_log.md

memory/sessions/
  <session-id>/
    context.md
    work_orders/
    agent_reports/
    verification/
    summary.md

agents/
  company.md
  memory_policy.md
  orchestrator.agent.md
  roles/
  skills/
  souls/
```

## 4. Phase 0: Freeze Current Design

Purpose: preserve the design baseline before CLI work.

Actions:

1. Review current diff.
2. Validate JSON.
3. Confirm HTML opens.
4. Commit current design files.

Done criteria:

- `git diff --check` passes
- `memory/company/*.json` parses
- `docs/channel_play_studio_plan.html` opens
- commit exists with agent-company design

## 5. Phase 1: `channelctl` Skeleton

Purpose: create one command entrypoint.

Commands:

```bash
./tools/channelctl status
./tools/channelctl company status
./tools/channelctl company brief
./tools/channelctl company agents
```

Implementation:

- `tools/channelctl` dispatches to Python modules.
- It locates repo root.
- It reads `memory/company/*.json`.
- It prints short human-readable status.
- It exits non-zero on corrupted JSON.

`company status` output:

```text
Project: channel_play
Session: none
Orchestrator task: none
Open tasks: 0
Locks: 0
gdx1: ssh auth blocked
Agents: 13 registered
```

Done criteria:

- command works from repo root
- command works from subdirectory
- broken JSON produces clear error
- no output over 20 lines by default

## 6. Phase 2: Brief Generator

Purpose: give every agent the same starting context.

Command:

```bash
./tools/channelctl company brief
```

Reads:

- `agents/company.md`
- `agents/memory_policy.md`
- `memory/company/current_context.md`
- `memory/company/state.json`
- `memory/company/task_board.json`
- `memory/company/locks.json`
- `git status --short`
- latest session summary if present

Writes:

```text
memory/company/current_brief.md
```

Brief format:

```markdown
# Current Brief

Generated:
Repo:
Git state:
Current session:
Open tasks:
Active locks:
gdx1 state:

## Current Context

## Relevant Agents

## Required Rules

## Next Recommended Action
```

Done criteria:

- brief is deterministic
- dirty git state is visible
- locks are visible
- gdx1 blocked state is visible
- brief stays below practical size

## 7. Phase 3: Session Start/End

Purpose: every work block leaves memory.

Commands:

```bash
./tools/channelctl company session start "<goal>"
./tools/channelctl company session end
```

Writes:

```text
memory/sessions/<session-id>/context.md
memory/sessions/<session-id>/work_orders/
memory/sessions/<session-id>/agent_reports/
memory/sessions/<session-id>/verification/
memory/sessions/<session-id>/summary.md
```

Updates:

```text
memory/company/state.json
```

Session ID:

```text
YYYYMMDD-HHMMSS-short-slug
```

Done criteria:

- start creates folders
- state points to active session
- end writes summary stub
- end clears active session
- starting twice without ending fails clearly

## 8. Phase 4: Work Orders

Purpose: turn human requests into executable agent contracts.

Commands:

```bash
./tools/channelctl company plan "<request>"
./tools/channelctl company assign <task-id> <agent-id>
```

MVP planner is rule-based.
No LLM automation required yet.

Routing rules:

| Request contains | Suggested agent |
|---|---|
| movement, mission, item, UI, operator | `unity_gameplay` |
| architecture, ScriptableObject, scene structure | `unity_architect` |
| server, netcode, multiplayer, bot | `multiplayer_server` |
| blender, mesh, pivot, collider, material | `technical_artist_blender` |
| 2D, 3D generation, asset brief | `asset_factory` |
| sound, sfx, music | `sound_designer` |
| bug, screenshot, reproduce, feedback | `qa_playtest` |
| build, compile, performance, frame | `performance_build` |
| gdx1, server worker, soak | `gdx_ops` |
| docs, memory, decision, session | `librarian` |
| review, risk, critique | `critic_reviewer` |

Work order file:

```text
memory/sessions/<session-id>/work_orders/<task-id>-<agent-id>.md
```

Done criteria:

- plan creates task in `task_board.json`
- assign creates work order markdown
- invalid agent id fails
- no writer assigned if locked path conflict exists

## 9. Phase 5: Locks

Purpose: stop agents from overwriting each other.

Commands:

```bash
./tools/channelctl company lock <path> <owner> <task-id>
./tools/channelctl company unlock <path>
./tools/channelctl company locks
```

Lock schema:

```json
{
  "path": "Assets/_Project/Scenes/School_MVP.unity",
  "owner": "unity_gameplay",
  "task_id": "task-0001",
  "created_at": "2026-06-01T14:00:00+09:00",
  "expires_at": "2026-06-01T18:00:00+09:00"
}
```

Conflict rules:

- exact path conflicts
- parent folder lock conflicts with child path
- child lock conflicts with parent folder lock
- expired lock must be shown but not silently removed

Done criteria:

- duplicate lock fails
- unlock requires exact path
- locks listed in status
- work order includes active lock info

## 10. Phase 6: Agent Reports

Purpose: standardize handoff back to orchestrator.

Command:

```bash
./tools/channelctl company report <task-id> <agent-id>
```

Writes:

```text
memory/sessions/<session-id>/agent_reports/<task-id>-<agent-id>.md
```

Report states:

```text
done
blocked
needs_review
```

Required fields:

- files read
- files changed
- evidence
- risks
- handoff

Done criteria:

- report template generated
- missing evidence keeps task out of `done`
- report links back to task board

## 11. Phase 7: Verification Gate

Purpose: prevent false done.

Commands:

```bash
./tools/channelctl company verify <task-id>
./tools/channelctl unity check
./tools/channelctl company close <task-id>
```

Verification evidence types:

| Work type | Minimum evidence |
|---|---|
| docs/memory | file diff + link |
| Unity C# | compile check |
| Unity scene/prefab | screenshot or playtest note |
| asset | metadata + preview/import note |
| Blender | cleanup report + exported file |
| gdx1 | probe/run log |
| feedback fix | before/after screenshot or note |

Close rule:

```text
task can close only if required evidence exists or blocker is explicitly recorded
```

Done criteria:

- close blocked without evidence
- verification files stored under session
- task board state updates

## 12. Phase 8: Dashboard Panel

Purpose: make company state visible.

Update:

```text
docs/channel_play_studio_plan.html
```

Later:

```text
tools/studio/dashboard.html
```

Show:

- active session
- orchestrator task
- active team
- open tasks
- active locks
- latest reports
- latest verification
- gdx1 state

Done criteria:

- dashboard opens locally
- no console errors
- readable at desktop and mobile widths

## 13. Phase 9: First Real Workflow

Use feedback loop as first practical workflow.

```text
play/view Unity
-> capture screenshot
-> create feedback note
-> company session start
-> company brief
-> company plan
-> assign qa_playtest + unity_gameplay + critic_reviewer
-> lock target path
-> implement
-> Unity check
-> report
-> review
-> close
-> memory sync
-> commit
```

MVP target:

```text
School_MVP visual or player-control feedback fix
```

Done criteria:

- one real feedback item goes from open to closed
- work order exists
- report exists
- evidence exists
- memory updated
- git commit created

## 14. Phase 10: Asset Workflow

Start only after Phase 9 works.

```text
asset brief
-> asset_factory work order
-> generated source stored
-> technical_artist_blender cleanup
-> Unity import note
-> scene screenshot
-> accept/rework/reject
```

Done criteria:

- one simple prop completes full metadata path
- source prompt/reference recorded
- generated asset not imported without metadata

## 15. Phase 11: gdx1 Workflow

Start only after SSH auth is fixed.

Commands:

```bash
./tools/channelctl gdx probe
./tools/channelctl company assign <task-id> gdx_ops
./tools/channelctl gdx run-server
./tools/channelctl gdx collect-logs
```

Done criteria:

- SSH probe passes
- server command runs remotely
- logs copied back to `runs/`
- gdx report written

## 16. Test Plan

Minimum checks per phase:

```bash
git diff --check
python3 -m json.tool memory/company/state.json
python3 -m json.tool memory/company/agent_registry.json
python3 -m json.tool memory/company/task_board.json
python3 -m json.tool memory/company/locks.json
./tools/channelctl company status
./tools/channelctl company brief
```

Unity checks when code changes:

```bash
./tools/channelctl unity check
```

HTML checks when dashboard changes:

```text
open local dashboard
check console
check Agent Company panel visible
```

## 17. Build Order Summary

| Order | Deliverable | File area |
|---:|---|---|
| 0 | commit current design | git |
| 1 | `channelctl` skeleton | `tools/channelctl`, `tools/studio/company/` |
| 2 | status/agents commands | `memory/company/*.json` |
| 3 | brief generator | `memory/company/current_brief.md` |
| 4 | session start/end | `memory/sessions/` |
| 5 | work order planner | `task_board.json`, templates |
| 6 | lock manager | `locks.json` |
| 7 | report generator | `agent_reports/` |
| 8 | verification gate | `verification/` |
| 9 | dashboard company panel | `tools/studio/dashboard.html` |
| 10 | first feedback workflow | `reviews/`, Unity check |
| 11 | asset workflow | `asset_pipeline/` |
| 12 | gdx1 workflow | gdx scripts, `runs/` |

## 18. Next Action

Next implementation step:

```text
Create `tools/channelctl` and `tools/studio/company/` with `company status`, `company agents`, and `company brief`.
```

This gives the orchestrator a real execution path.
After that, work orders and locks can be added without changing the architecture.

## 19. Implementation Progress

### 2026-06-01

Created initial maintainable CLI structure:

```text
tools/channelctl
tools/studio/company/
tools/studio/templates/
```

Implemented:

- `tools/channelctl status`
- `tools/channelctl company status`
- `tools/channelctl company agents`
- `tools/channelctl company brief`

Next implementation step:

```text
Add `company session start/end`, then `company plan/assign`.
```

### 2026-06-01 Full Checklist Pass

Implemented:

- `company session start/end`
- `company plan/assign`
- `company locks/lock/unlock`
- `company report/evidence/verify/close`
- `unity check`
- `capture screen`
- `feedback new/process`
- `asset new/status/screenshot`
- `gdx probe/sync/run-server/run-bots/collect-logs`
- static `tools/studio/dashboard.html`
- failure-path unit tests

### 2026-06-01 gdx1 SSH Recovery

Verified:

- `ssh -o BatchMode=yes gdx1 hostname` returns `gdx1`
- gdx1 has `git`, `docker`, and `python3`
- `./tools/channelctl gdx sync` creates/updates `~/channel_play` on gdx1
- `./tools/channelctl gdx probe` updates shared state to `online_via_tailscale / ok`

Current remote execution state:

- real SSH transport works
- remote workspace sync works
- server and bot run commands execute remotely but report blocked until runner scripts or Linux server builds exist
