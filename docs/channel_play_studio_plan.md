# Channel Play Studio Plan

Updated: 2026-06-01

## 0. What This Is

`Channel Play Studio` is the project-specific production tool for building the `channel_play` Unity game with AI.

It is not just a launcher.
It should manage the full game-production loop:

- design knowledge
- Unity implementation
- Blender asset work
- AI-generated 2D/3D asset pipeline
- sound/effect notes
- physics/gameplay experiments
- optimization notes
- screenshots and visual feedback
- AI agent sessions
- build/test/run logs
- gdx1 worker jobs
- GitHub source control

## 1. Current Reality

### 1.1 gdx1 Status

Current check:

- Tailscale sees `gdx1`
- `gdx1` is online
- SSH port 22 is open
- SSH authentication still fails for `daehan` and `zenovis1`

Meaning:

- network path is restored
- remote worker is not usable yet
- next fix is SSH key/account setup, not network recovery

### 1.2 Available Local Tools

Verified CLIs/apps:

- Unity Editor `6000.0.76f1`
- Unity Hub
- OBS
- Blender
- Obsidian
- `obsidian`
- `blender`
- `obs`
- `ffmpeg`
- `screencapture`
- `codex`
- `claude`
- `agy`
- `antigravity`
- `hermes`
- `openclaw`
- `gh`
- `git`
- `git-lfs`
- `docker`
- `tailscale`

This is enough to build a serious local production control plane.

## 2. Correct Shape

Build this as a repo-owned production OS:

```text
channel_play/
  tools/channelctl
  tools/studio/
  config/studio/
  docs/
  obsidian/
  reviews/
  asset_pipeline/
  runs/
  artifacts/
  logs/
```

One command should coordinate it:

```bash
./tools/channelctl
```

The first version should be boring and reliable:

- Bash/Python scripts
- JSON metadata
- Markdown notes
- static HTML dashboard
- no database yet
- no always-on server yet

## 3. Core System Modules

### 3.1 Knowledge Base: Obsidian

Obsidian should be the design memory and production notebook.

Recommended repo folder:

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
  templates/
```

Why inside repo:

- versioned with GitHub
- AI agents can read/write it safely
- project knowledge travels with code
- avoids scattering production notes across chat history

Obsidian should hold:

- game design decisions
- mission rules
- item specs
- operator-panel specs
- scene notes
- asset briefs
- sound/effect briefs
- optimization notes
- agent session summaries
- feedback records
- implementation decisions

### 3.2 Command Center: `channelctl`

`channelctl` should be the entrypoint for all work.

Initial commands:

```bash
./tools/channelctl status
./tools/channelctl open unity
./tools/channelctl open obsidian
./tools/channelctl open dashboard
./tools/channelctl capture screen
./tools/channelctl feedback new
./tools/channelctl unity check
./tools/channelctl unity playlog
./tools/channelctl blender check
./tools/channelctl asset new
./tools/channelctl agent check
./tools/channelctl session start
./tools/channelctl session end
./tools/channelctl gdx probe
```

Later commands:

```bash
./tools/channelctl agent codex <task-id>
./tools/channelctl agent claude-review <task-id>
./tools/channelctl asset generate-3d <asset-id>
./tools/channelctl asset blender-cleanup <asset-id>
./tools/channelctl unity import-asset <asset-id>
./tools/channelctl gdx run-server
./tools/channelctl gdx run-bots
```

### 3.3 Studio Dashboard

Create a local static dashboard first.

Path:

```text
tools/studio/dashboard.html
```

It should show:

- current Git commit
- Unity version
- gdx1 state
- current session
- latest screenshots
- open feedback items
- active asset briefs
- Unity compile status
- Blender availability
- AI agent availability
- next recommended workflow

The dashboard should read:

```text
runs/latest/status.json
reviews/index.json
asset_pipeline/index.json
obsidian/channel_play/00_Index.md
```

### 3.4 Feedback Loop

This is the most important UX feature.

Target flow:

1. User plays or views `School_MVP` in Unity.
2. User captures screen.
3. `channelctl feedback new` creates a feedback record.
4. User adds notes or rough annotation.
5. Codex converts feedback into tasks.
6. Unity change is implemented.
7. Screenshot before/after is linked.
8. Feedback is closed.

Storage:

```text
reviews/
  2026-06-01/
    feedback-0001/
      screenshot.png
      annotation.png
      feedback.md
      task.json
```

Feedback note format:

```markdown
# Feedback 0001

Scene: School_MVP
Screenshot: screenshot.png
Priority: P1
Status: open

## Observation

## Requested Change

## Agent Interpretation

## Files Changed

## Verification
```

Later, make a small annotation UI:

- static HTML canvas
- load screenshot
- draw boxes/arrows
- save `annotation.json`
- export annotated PNG

### 3.5 AI Agent Lanes

Do not let every agent edit everything.
Use lanes.

| Agent | Lane | Writes Code? | Main Use |
|---|---|---:|---|
| Codex | implementation | yes | Unity code, scripts, repo ops |
| Claude | review/design critique | no by default | architecture, bug risk, gameplay logic review |
| agy / Antigravity | browser/UI operator | limited | visual checks, browser flows, reference gathering |
| Hermes | background loops | limited | long-running status, research, summaries |
| OpenClaw | local orchestration/runtime | limited | agent routing, local gateway, delegated jobs |

Rule:

- one writer at a time per branch
- reviewers produce notes/tasks
- Codex applies changes unless explicitly delegated
- all changes go through Git commits

### 3.5.1 Agent Company Layer

The lane table is only the first level.
`channel_play` also needs a company-style orchestration layer with shared memory and explicit work orders.

Create:

```text
agents/
  company.md
  memory_policy.md
  orchestrator.agent.md
  roles/

memory/company/
  state.json
  agent_registry.json
  task_board.json
  locks.json
  current_context.md
  decision_log.md
  handoff_log.md
```

Operating rule:

- one orchestrator AI chooses the needed specialists
- each agent has its own role file, skill/soul assumptions, write scope, and output contract
- every non-trivial task becomes a work order before implementation
- all agents read the same current context before working
- every result returns as an agent report with evidence
- Unity scenes, prefab folders, and script systems use locks before writes
- the orchestrator integrates results and updates Obsidian/shared memory

Detailed plan:

- `docs/channel_play_agent_company_plan.md`

### 3.6 Asset Factory

Asset work needs its own pipeline.

Recommended structure:

```text
asset_pipeline/
  briefs/
  incoming_2d/
  generated_3d/
  blender_work/
  unity_ready/
  rejected/
  index.json
```

Asset lifecycle:

```text
brief -> 2D concept -> 3D generation -> Blender cleanup -> Unity import -> scene test -> accepted
```

Each asset gets:

```text
asset_pipeline/briefs/asset_school_desk.md
asset_pipeline/generated_3d/asset_school_desk/
asset_pipeline/blender_work/asset_school_desk/
asset_pipeline/unity_ready/asset_school_desk/
```

Asset metadata:

```json
{
  "id": "asset_school_desk",
  "status": "briefed",
  "source": "2d_concept",
  "target": "Unity prefab",
  "scale_reference": "player height 2m",
  "poly_budget": "low",
  "texture_style": "readable broadcast prop",
  "owner": "codex",
  "reviewer": "human"
}
```

2D-to-3D tools such as Pixel3D/Meshy-like generators should be wrapped behind the same asset metadata.
The exact vendor can change.
The pipeline should not depend on one vendor's UI.

### 3.7 Blender AI Use

Blender should be controlled with scripts first.

Use Blender for:

- cleanup generated meshes
- scale normalization
- origin/pivot fixing
- collider proxy generation
- decimation
- material slot cleanup
- export to FBX/GLB

Recommended command pattern:

```bash
blender --background <file.blend> --python tools/studio/blender/cleanup_asset.py -- <asset-id>
```

AI should produce:

- Blender Python scripts
- cleanup reports
- before/after preview renders
- Unity import notes

### 3.8 Unity Integration

Unity should be controlled through repeatable checks.

Commands:

```bash
./tools/channelctl unity check
./tools/channelctl unity open School_MVP
./tools/channelctl unity compile
./tools/channelctl unity screenshot School_MVP
./tools/channelctl unity build mac
./tools/channelctl unity build linux-server
```

Near-term priority:

1. compile check
2. scene open check
3. screenshot capture
4. play-mode smoke test
5. server build

### 3.9 Session Records

Every work session should leave a trace.

Structure:

```text
obsidian/channel_play/07_Sessions/
  2026-06-01-session-001.md
runs/
  2026-06-01-session-001/
    status.json
    commands.log
    screenshots/
    artifacts/
```

Session note template:

```markdown
# Session 2026-06-01 001

## Goal

## Starting State

## Decisions

## Changes

## Screenshots

## Verification

## Next Actions
```

## 4. Main Workflows

### 4.1 Implement Gameplay Feature

```text
Obsidian feature spec
-> Codex implementation
-> Unity compile
-> user visual check
-> screenshot feedback
-> fix
-> commit/push
-> session summary
```

### 4.2 Create Asset

```text
Obsidian asset brief
-> 2D reference/concept
-> AI 3D generation
-> Blender cleanup
-> Unity import
-> scene placement
-> screenshot review
-> accept/rework
```

### 4.3 Review Build

```text
Unity scene open
-> capture screenshot/video
-> feedback note
-> Claude/Codex interpretation
-> task list
-> implementation pass
```

### 4.4 gdx1 Server Test

Blocked until SSH auth is fixed.

```text
Mac builds Linux server
-> sync to gdx1
-> run headless server
-> Mac client connects
-> logs collected
-> session note updated
```

## 5. Minimum Useful Version

Do this first.

### Step A: Project Studio Skeleton

Create:

- `obsidian/channel_play/`
- `config/studio/`
- `tools/channelctl`
- `tools/studio/dashboard.html`
- `reviews/.gitkeep`
- `asset_pipeline/.gitkeep`
- `runs/.gitkeep`
- `artifacts/.gitkeep`

### Step B: Working Commands

Implement:

```bash
./tools/channelctl status
./tools/channelctl open obsidian
./tools/channelctl open unity
./tools/channelctl capture screen
./tools/channelctl feedback new
./tools/channelctl unity check
./tools/channelctl agent check
./tools/channelctl gdx probe
```

### Step C: Obsidian Templates

Create templates:

- game feature spec
- asset brief
- feedback item
- session summary
- design decision
- sound brief
- optimization note

### Step D: Dashboard

Generate a static dashboard from JSON and Markdown indexes.

## 6. What To Avoid

Avoid:

- multi-agent auto-editing the same Unity files
- storing all production memory only in chat
- untracked screenshots and generated assets
- vendor-specific asset pipeline assumptions
- making a large web app before command-line workflows work
- moving Unity Editor work to gdx1

## 7. Recommendation

Build `Channel Play Studio` in this order:

1. `channelctl`
2. Agent Company role files and shared memory policy
3. Obsidian vault structure and templates
4. screenshot feedback loop
5. session logging
6. Unity compile/open checks
7. asset pipeline folders and metadata
8. Blender automation scripts
9. dashboard
10. gdx1 worker integration after SSH auth is fixed

This gives the project a real production cockpit while keeping Unity game development as the main product.
