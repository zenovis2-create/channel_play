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
- common `channelctl` commands

## Architecture

```text
tools/channelctl
  -> studio open/serve
  -> tools/studio/workspace_server.py
      -> static app under tools/studio/app/
      -> JSON APIs over repo state files
      -> allowlisted channelctl command execution
```

The web server binds to localhost and uses Python standard library only.

## Safety Rules

- No arbitrary shell command endpoint.
- Commands are allowlisted in `tools/studio/workspace_server.py`.
- Subprocess calls avoid shell string execution.
- File preview is read-only.
- File preview is restricted to project memory, docs, agents, reviews, runs, and asset folders.

## Current Limits

- This is a local cockpit, not a multi-user web service.
- It does not directly edit Obsidian notes yet.
- It does not stream long-running command output yet.
- It triggers agent workflows through `channelctl`, not direct Codex/Claude/Hermes process orchestration yet.
- It currently launches command workflows synchronously and returns the final result.

## Next Upgrade

Add a persistent job queue:

```text
command request -> queued job -> running log stream -> result evidence -> task update
```
