# Channel Play Agent Company CLI

This package implements the repo-local orchestration CLI used by `tools/channelctl`.

Module ownership:

- `cli.py`: command dispatch only
- `paths.py`: repo root and path helpers
- `state.py`: JSON and memory file loading/writing
- `status.py`: `company status`
- `agents.py`: `company agents`
- `brief.py`: `company brief`
- `sessions.py`: session start/end lifecycle
- `planner.py`: rule-based task planning and work orders
- `locks.py`: path-level write locks
- `reports.py`: agent report templates
- `verify.py`: evidence attachment, verification, close gate
- `unity.py`: Unity project check bridge
- `dashboard.py`: static dashboard generation
- `capture.py`: screenshot capture
- `feedback.py`: feedback record creation
- `assets.py`: asset pipeline records
- `gdx.py`: gdx1 probe and blocked workflow logs
- `entrypoints.py`: top-level `unity/open/capture/feedback/asset/gdx` dispatch
- `git_info.py`: small git probes
- `render.py`: terminal formatting helpers
- `errors.py`: user-facing CLI errors

Design rules:

- Keep `tools/channelctl` thin.
- Keep commands small and composable.
- Do not put business logic in `cli.py`.
- Use JSON files under `memory/company/` as operational state.
- Write durable decisions to Obsidian or `memory/company/decision_log.md`.
- Keep default command output short.

Next modules:

- `tests/`
- richer Unity log parsing
- real gdx1 remote execution after SSH auth is fixed
