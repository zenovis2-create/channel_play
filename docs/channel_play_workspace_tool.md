# Channel Play Workspace Tool

Updated: 2026-06-01

## What Exists Now

`Channel Play Studio` now has an integrated local workspace cockpit.

Run:

```bash
./tools/channelctl studio open
```

Default URL:

```text
http://127.0.0.1:8766/
```

## What It Does

The cockpit provides one UI for:

- Agent Company status
- registered agent roles
- task board
- write locks
- shared memory preview
- feedback records
- asset pipeline records
- recent runs/evidence
- gdx1 worker controls
- Codex, Claude, agy, Hermes, and OpenClaw adapter status
- AI agent dry-run/run/review controls
- common `channelctl` commands

## Architecture

```text
tools/channelctl
  -> studio open/serve
  -> tools/studio/workspace_server.py
      -> static app under tools/studio/app/
      -> JSON APIs over repo state files
      -> allowlisted channelctl command execution
      -> tools/studio/company/agent_runner.py
          -> memory/company/tool_adapters.json
          -> external AI CLIs through argv-only subprocess calls
```

The web server binds to localhost and uses Python standard library only.

## Safety Rules

- No arbitrary shell command endpoint.
- Commands are allowlisted in `tools/studio/workspace_server.py`.
- Subprocess calls avoid shell string execution.
- External AI tools use `memory/company/tool_adapters.json` argv templates.
- Agent execution supports `--dry-run` before real tool invocation.
- File preview is read-only.
- File preview is restricted to project memory, docs, agents, reviews, runs, and asset folders.

## Current Limits

- This is a local cockpit, not a multi-user web service.
- It does not directly edit Obsidian notes yet.
- It does not stream long-running command output yet.
- It triggers Codex/Claude/agy/Hermes/OpenClaw synchronously through `channelctl agent`.
- It currently launches command workflows synchronously and returns the final result.

## Agent Commands

```bash
./tools/channelctl agent adapters
./tools/channelctl agent run task-0001 --tool codex --dry-run
./tools/channelctl agent run task-0001 --tool codex
./tools/channelctl agent review task-0001 --tool claude --dry-run
```

Outputs are written under `runs/agent-*` and linked back to `memory/company/task_board.json`.

## Next Upgrade

Add a persistent job queue:

```text
command request -> queued job -> running log stream -> result evidence -> task update
```
