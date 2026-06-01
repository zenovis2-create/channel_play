# channel_play Workstation Plan

Updated: 2026-06-01

## 0. Goal

Build a project-specific workstation for `channel_play`.

This should not become another large platform.
It should be a thin control plane inside this repository that coordinates:

- Mac Studio local Unity production
- gdx1 / ASUS GX10 remote server and test worker
- Codex
- Claude
- Antigravity / `agy`
- Hermes
- OpenClaw
- GitHub
- Unity
- OBS
- Blender

## 1. Current Assets

### 1.1 Mac Studio

Role: main production machine.

Verified:

- Apple M2 Ultra
- 64GB memory
- macOS
- Unity Hub installed
- Unity Editor `6000.0.76f1`
- OBS installed
- Blender installed
- GitHub repo connected
- Codex, Claude, agy, antigravity, Hermes, OpenClaw CLIs present

Use Mac Studio for:

- Unity Editor work
- gameplay implementation
- scene/prefab editing
- local play testing
- OBS capture
- asset prep
- Git/GitHub source of truth

### 1.2 gdx1 / ASUS GX10

Role: remote execution worker.

Verified:

- Tailscale sees `gdx1`
- OS reported as Linux
- SSH auth is not yet configured

Planned use:

- Unity headless server
- bot/load test
- soak test
- log collection
- AI/agent background jobs
- local inference or analysis jobs

Blocker:

- `zenovis1@gdx1`: SSH permission denied

## 2. Design Principle

Use a repo-owned control plane:

```text
channel_play/
  tools/channelctl/
  config/workstation/
  runs/
  artifacts/
  logs/
  docs/
```

`channelctl` should be the single entry point.

Examples:

```bash
./tools/channelctl status
./tools/channelctl open unity
./tools/channelctl run unity-check
./tools/channelctl agent codex "Implement point system"
./tools/channelctl agent claude "Review networking design"
./tools/channelctl gdx probe
./tools/channelctl gdx run-server
./tools/channelctl capture obs-check
```

## 3. Tool Shape

### 3.1 `channelctl`

Recommended first implementation:

- Bash frontend
- small command modules
- JSON status files
- no server required

Reason:

- fastest to build
- easy to inspect
- works with Codex/Claude/agy/openclaw
- safe before gdx1 SSH is stable

Later upgrade:

- local web dashboard
- task queue
- SQLite run database
- background workers

### 3.2 Directory Layout

```text
tools/
  channelctl
  channelctl.d/
    status.sh
    unity.sh
    gdx.sh
    agent.sh
    capture.sh
    github.sh

config/
  workstation/
    machines.json
    agents.json
    workflows.json
    env.example

runs/
  .gitkeep

artifacts/
  .gitkeep

logs/
  .gitkeep
```

Git policy:

- commit `tools/` and `config/`
- do not commit `runs/`, `artifacts/`, `logs/` contents
- keep `.gitkeep` only

## 4. Machine Registry

Create `config/workstation/machines.json`.

It should track:

```json
{
  "mac_studio": {
    "role": "unity_editor_primary",
    "host": "localhost",
    "os": "macOS",
    "unity": "/Applications/Unity/Hub/Editor/6000.0.76f1/Unity.app/Contents/MacOS/Unity",
    "responsibilities": ["editor", "client_build", "obs", "git"]
  },
  "gdx1": {
    "role": "linux_worker",
    "host": "gdx1",
    "user": "zenovis1",
    "os": "Ubuntu Linux",
    "status": "ssh_blocked",
    "responsibilities": ["headless_server", "bot_test", "soak_test", "log_collection"]
  }
}
```

## 5. Agent Registry

Create `config/workstation/agents.json`.

Recommended roles:

```json
{
  "codex": {
    "role": "primary_implementer",
    "command": "codex",
    "use_for": ["code_changes", "repo_ops", "unity_scripts", "tests"]
  },
  "claude": {
    "role": "reviewer_architect",
    "command": "claude",
    "use_for": ["code_review", "design_critique", "risk_analysis"]
  },
  "agy": {
    "role": "ui_and_browser_operator",
    "command": "agy",
    "use_for": ["browser_flows", "ui_checks", "parallel_research"]
  },
  "hermes": {
    "role": "background_recovery_and_research",
    "command": "hermes",
    "use_for": ["long_jobs", "topic_research", "status_loops"]
  },
  "openclaw": {
    "role": "local_agent_runtime",
    "command": "openclaw",
    "use_for": ["agent_orchestration", "tool_routing", "local_gateway"]
  }
}
```

## 6. Workflow Registry

Create `config/workstation/workflows.json`.

Initial workflows:

```json
{
  "unity-check": {
    "owner": "codex",
    "steps": [
      "./scripts/check_local_env.sh",
      "Unity batchmode open project",
      "grep compiler errors"
    ]
  },
  "first-playable": {
    "owner": "codex",
    "reviewer": "claude",
    "steps": [
      "implement gameplay slice",
      "run Unity batchmode compile",
      "open Unity for manual play check",
      "commit and push"
    ]
  },
  "gdx-server-smoke": {
    "owner": "codex",
    "worker": "gdx1",
    "blocked_by": "gdx1_ssh",
    "steps": [
      "sync server build",
      "run headless server",
      "connect Mac client",
      "collect logs"
    ]
  }
}
```

## 7. Dashboard

Build a static local dashboard first.

File:

```text
tools/dashboard/index.html
```

It should display:

- repo status
- current commit
- Unity version
- gdx1 status
- next workflow
- last run result
- links to `real_plan.html`, GitHub, Unity project, logs

Later, make it dynamic from JSON:

```text
runs/latest/status.json
```

## 8. First Build Order

### Step 1: Control files

Create:

- `tools/channelctl`
- `config/workstation/machines.json`
- `config/workstation/agents.json`
- `config/workstation/workflows.json`
- `runs/.gitkeep`
- `artifacts/.gitkeep`
- `logs/.gitkeep`

### Step 2: Status commands

Implement:

```bash
./tools/channelctl status
./tools/channelctl env
./tools/channelctl gdx probe
./tools/channelctl unity check
```

### Step 3: Agent commands

Implement wrappers only.

No magic routing yet.

```bash
./tools/channelctl agent list
./tools/channelctl agent check
```

### Step 4: Workflow commands

Implement:

```bash
./tools/channelctl workflow list
./tools/channelctl workflow next
./tools/channelctl workflow run unity-check
```

### Step 5: Dashboard

Generate:

```bash
./tools/channelctl dashboard
```

This writes:

```text
runs/latest/status.json
tools/dashboard/index.html
```

## 9. What Not To Build Yet

Do not build these now:

- full web app
- Kubernetes
- cloud CI
- custom agent scheduler
- account system
- database-backed dashboard
- automatic code modification by multiple agents at once

Reason:

- Unity MVP is the product.
- workstation tooling must reduce friction, not become the product.

## 10. Recommended Operating Model

Use this loop:

1. `channelctl status`
2. choose one workflow
3. Codex implements
4. Unity batchmode verifies compile/import
5. Claude reviews only important architecture/risk changes
6. push to GitHub
7. update dashboard

For gdx1:

1. keep it optional until SSH is fixed
2. then use it only for server/test/log jobs
3. do not move Unity Editor work there

## 11. Next Action

Build Step 1 and Step 2 now.

That gives us a real project-specific workstation without overbuilding:

- one command
- one config set
- one status view
- clean room for future agent orchestration
