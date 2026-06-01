# Channel Play Agent Company Implementation Checklist

Updated: 2026-06-01

## 0. Current Baseline

- [x] Agent Company concept documented
- [x] Agent role profiles created under `agents/`
- [x] Shared memory root created under `memory/company/`
- [x] Initial `channelctl` entrypoint created
- [x] `company status` command works
- [x] `company agents` command works
- [x] `company brief` command works
- [x] `memory/company/current_brief.md` generated
- [x] `company session start/end` command works
- [x] `company plan/assign` command works
- [x] `company lock/unlock/locks` command works
- [x] `company report/evidence/verify/close` command works
- [x] `unity check` quick check works
- [x] `capture screen` and `feedback new` work
- [x] `asset new/status` works
- [x] `gdx` blocked workflow logs work
- [x] static dashboard generated
- [x] Current Agent Company design committed to Git
- [x] GitHub pushed after first implementation milestone

## 1. Phase 0: Freeze Design Baseline

Goal: lock current design before adding more automation.

- [x] Create `docs/channel_play_agent_company_plan.md`
- [x] Create `docs/channel_play_agent_company_implementation_plan.md`
- [x] Create `agents/company.md`
- [x] Create `agents/memory_policy.md`
- [x] Create `agents/orchestrator.agent.md`
- [x] Create role profiles in `agents/roles/`
- [x] Create initial operational memory JSON files
- [x] Update `docs/channel_play_studio_plan.md`
- [x] Update `docs/channel_play_studio_plan.html`
- [x] Validate JSON files
- [x] Run `git diff --check`
- [x] Commit design baseline

Verification:

```bash
git diff --check
python3 -m json.tool memory/company/state.json >/dev/null
python3 -m json.tool memory/company/agent_registry.json >/dev/null
python3 -m json.tool memory/company/task_board.json >/dev/null
python3 -m json.tool memory/company/locks.json >/dev/null
```

## 2. Phase 1: CLI Skeleton

Goal: make one stable command entrypoint.

- [x] Create `tools/channelctl`
- [x] Make `tools/channelctl` executable
- [x] Create `tools/__init__.py`
- [x] Create `tools/studio/__init__.py`
- [x] Create `tools/studio/company/__init__.py`
- [x] Create `tools/studio/company/cli.py`
- [x] Create `tools/studio/company/paths.py`
- [x] Create `tools/studio/company/errors.py`
- [x] Create `tools/studio/company/README.md`
- [x] Keep `tools/channelctl` as thin dispatcher
- [x] Route `tools/channelctl status` to company status
- [x] Route `tools/channelctl company status`
- [x] Route `tools/channelctl company agents`
- [x] Route `tools/channelctl company brief`

Verification:

```bash
chmod +x tools/channelctl
python3 -m py_compile tools/channelctl tools/studio/company/*.py
./tools/channelctl status
./tools/channelctl company status
./tools/channelctl company agents
./tools/channelctl company brief
```

## 3. Phase 2: State And Brief

Goal: every agent starts from the same current context.

- [x] Create `tools/studio/company/state.py`
- [x] Create `tools/studio/company/status.py`
- [x] Create `tools/studio/company/agents.py`
- [x] Create `tools/studio/company/brief.py`
- [x] Create `tools/studio/company/git_info.py`
- [x] Create `tools/studio/company/render.py`
- [x] Read `memory/company/state.json`
- [x] Read `memory/company/agent_registry.json`
- [x] Read `memory/company/task_board.json`
- [x] Read `memory/company/locks.json`
- [x] Read `memory/company/current_context.md`
- [x] Include Git dirty state in brief
- [x] Include gdx1 state in brief
- [x] Write `memory/company/current_brief.md`
- [x] Add brief size guard
- [x] Add latest session summary to brief
- [x] Add stale-memory warning

Verification:

```bash
./tools/channelctl company brief
test -s memory/company/current_brief.md
```

## 4. Phase 3: Session Lifecycle

Goal: every work block leaves a structured trace.

- [x] Create `tools/studio/company/sessions.py`
- [x] Add `./tools/channelctl company session start "<goal>"`
- [x] Add `./tools/channelctl company session end`
- [x] Generate session ID as `YYYYMMDD-HHMMSS-short-slug`
- [x] Create `memory/sessions/<session-id>/context.md`
- [x] Create `memory/sessions/<session-id>/work_orders/`
- [x] Create `memory/sessions/<session-id>/agent_reports/`
- [x] Create `memory/sessions/<session-id>/verification/`
- [x] Create `memory/sessions/<session-id>/summary.md`
- [x] Update `memory/company/state.json.active_session`
- [x] Prevent starting second session while one is active
- [x] End session clears `active_session`
- [x] End session writes summary stub
- [x] Add tests for start/end failure paths

Verification:

```bash
./tools/channelctl company session start "test session"
./tools/channelctl company status
./tools/channelctl company session end
```

## 5. Phase 4: Work Orders

Goal: convert requests into scoped agent contracts.

- [x] Create `tools/studio/templates/work_order.md`
- [x] Create `tools/studio/company/planner.py`
- [x] Add `./tools/channelctl company plan "<request>"`
- [x] Add `./tools/channelctl company assign <task-id> <agent-id>`
- [x] Generate task IDs as `task-0001`, `task-0002`
- [x] Store tasks in `memory/company/task_board.json`
- [x] Create work order markdown in active session
- [x] Require active session before assign
- [x] Validate agent ID against `agent_registry.json`
- [x] Add routing rules by keyword
- [x] Add allowed write paths to work order
- [x] Add required evidence to work order
- [x] Add reviewer suggestion when risk is high
- [x] Add blocked state for unclear scope

Verification:

```bash
./tools/channelctl company session start "planner smoke"
./tools/channelctl company plan "fix player movement"
./tools/channelctl company assign task-0001 unity_gameplay
```

## 6. Phase 5: Locks

Goal: prevent multiple agents from editing the same target.

- [x] Create `tools/studio/company/locks.py`
- [x] Add `./tools/channelctl company locks`
- [x] Add `./tools/channelctl company lock <path> <owner> <task-id>`
- [x] Add `./tools/channelctl company unlock <path>`
- [x] Store locks in `memory/company/locks.json`
- [x] Detect exact path conflict
- [x] Detect parent-folder conflict
- [x] Detect child-path conflict
- [x] Show expired locks but do not silently remove
- [x] Include active locks in `company status`
- [x] Include active locks in `company brief`
- [x] Block assignment if write path conflicts

Verification:

```bash
./tools/channelctl company lock Assets/_Project/Scenes/School_MVP.unity unity_gameplay task-0001
./tools/channelctl company locks
./tools/channelctl company unlock Assets/_Project/Scenes/School_MVP.unity
```

## 7. Phase 6: Agent Reports

Goal: standardize handoff back to orchestrator.

- [x] Create `tools/studio/templates/agent_report.md`
- [x] Create `tools/studio/company/reports.py`
- [x] Add `./tools/channelctl company report <task-id> <agent-id>`
- [x] Generate report markdown in active session
- [x] Link report to task ID
- [x] Require status: `done`, `blocked`, or `needs_review`
- [x] Require evidence section
- [x] Require risks section
- [x] Update task board when report is created
- [x] Prevent `done` if evidence is empty

Verification:

```bash
./tools/channelctl company report task-0001 unity_gameplay
```

## 8. Phase 7: Verification Gate

Goal: no false "done".

- [x] Create `tools/studio/company/verify.py`
- [x] Add `./tools/channelctl company verify <task-id>`
- [x] Add `./tools/channelctl company close <task-id>`
- [x] Require docs evidence for docs-only tasks
- [x] Require Unity compile evidence for C# tasks
- [x] Require screenshot/playtest note for scene changes
- [x] Require metadata for generated assets
- [x] Require Blender cleanup report for Blender tasks
- [x] Require gdx log for gdx1 tasks
- [x] Store verification files under session
- [x] Update task status only after verification passes
- [x] Allow explicit blocked closure with blocker reason

Verification:

```bash
./tools/channelctl company verify task-0001
./tools/channelctl company close task-0001
```

## 9. Phase 8: Unity Command Bridge

Goal: connect orchestration to real Unity checks.

- [x] Add `./tools/channelctl unity check`
- [x] Add Unity path discovery
- [x] Add Unity project path validation
- [x] Add batchmode compile check
- [x] Capture Unity logs to `runs/`
- [x] Parse compile errors into short summary
- [x] Record compile result as verification evidence
- [x] Keep command safe if Unity license token warning appears

Verification:

```bash
./tools/channelctl unity check
```

## 10. Phase 9: Dashboard Panel

Goal: make company state visible.

- [x] Create `tools/studio/dashboard.html`
- [x] Add `./tools/channelctl open dashboard`
- [x] Add company state panel
- [x] Show active session
- [x] Show open tasks
- [x] Show locks
- [x] Show latest reports
- [x] Show latest verification
- [x] Show gdx1 state
- [x] Show memory freshness
- [x] Validate desktop view
- [x] Validate mobile view
- [x] Check browser console

Verification:

```bash
./tools/channelctl open dashboard
```

## 11. Phase 10: Feedback Workflow

Goal: first real end-to-end company workflow.

- [x] Add `./tools/channelctl capture screen`
- [x] Add `./tools/channelctl feedback new`
- [x] Create feedback folder under `reviews/YYYY-MM-DD/`
- [x] Store screenshot path
- [x] Create feedback markdown
- [x] Start company session from feedback
- [x] Generate brief
- [x] Generate QA work order
- [x] Generate Unity gameplay work order
- [x] Lock target path
- [x] Implement fix
- [x] Run Unity check
- [x] Create agent report
- [x] Create reviewer report
- [x] Close feedback with evidence
- [x] Update memory/session summary

Verification:

```bash
./tools/channelctl capture screen
./tools/channelctl feedback new
```

## 12. Phase 11: Asset Workflow

Goal: first tracked generated asset pipeline.

- [x] Add `./tools/channelctl asset new <asset-id>`
- [x] Create asset brief
- [x] Store source prompt/reference
- [x] Store generation metadata
- [x] Store license/source status
- [x] Create Blender cleanup work order
- [x] Export Unity-ready asset
- [x] Create Unity import note
- [x] Capture scene screenshot
- [x] Mark asset `accepted`, `rework`, or `rejected`

Verification:

```bash
./tools/channelctl asset new asset_school_prop_001
```

## 13. Phase 12: gdx1 Workflow

Goal: use gdx1 after SSH auth is fixed.

- [x] Fix SSH authentication to `gdx1`
- [x] Add `./tools/channelctl gdx probe`
- [x] Add remote workspace path check
- [x] Add gdx1 sync command
- [x] Add gdx1 server run command
- [x] Add gdx1 bot run command
- [x] Add gdx1 log collection
- [x] Store logs under `runs/`
- [x] Create gdx ops report
- [x] Add gdx1 status to dashboard

Verification:

```bash
./tools/channelctl gdx probe
```

## 14. Continuous Checks

Run after every implementation step:

- [x] `git diff --check`
- [x] `python3 -m py_compile tools/channelctl tools/studio/company/*.py`
- [x] `python3 -m json.tool memory/company/state.json >/dev/null`
- [x] `python3 -m json.tool memory/company/agent_registry.json >/dev/null`
- [x] `python3 -m json.tool memory/company/task_board.json >/dev/null`
- [x] `python3 -m json.tool memory/company/locks.json >/dev/null`
- [x] `./tools/channelctl company status`
- [x] `./tools/channelctl company brief`

Run when Unity files change:

- [x] `./tools/channelctl unity check`

Run when HTML/dashboard changes:

- [x] open dashboard locally
- [x] check browser console
- [x] check mobile width

## 15. Commit Milestones

- [x] Commit 1: Agent Company design and memory baseline
- [x] Commit 2: `channelctl company status/agents/brief`
- [x] Commit 3: session start/end
- [x] Commit 4: plan/assign work orders
- [x] Commit 5: locks
- [x] Commit 6: reports and verification gate
- [x] Commit 7: Unity check bridge
- [x] Commit 8: dashboard
- [x] Commit 9: first feedback workflow
- [x] Commit 10: first asset workflow
- [x] Commit 11: gdx1 workflow after SSH auth

## 16. Definition Of Done

MVP is done when:

- [x] A user request becomes a company session
- [x] The orchestrator generates a current brief
- [x] A work order is assigned to a role agent
- [x] A path lock prevents conflicting writes
- [x] An agent report is created
- [x] Verification evidence is attached
- [x] The task closes only after verification
- [x] Session summary updates shared memory
- [x] Dashboard shows session/task/lock/report state
- [x] One real Unity feedback item goes from open to closed
