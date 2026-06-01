"""Company status command."""

from __future__ import annotations

from pathlib import Path

from .git_info import git_head, git_short_status
from .render import table
from .state import load_company_state


def render_status(root: Path) -> str:
    data = load_company_state(root)
    state = data["state"]
    gdx = state.get("gdx1", {})
    open_tasks = [task for task in data["tasks"] if task.get("status") not in {"closed", "closed_blocked"}]
    rows = [
        ("Project", state.get("project", "channel_play")),
        ("Git", git_head(root)),
        ("Dirty files", str(len(git_short_status(root)))),
        ("Session", str(state.get("active_session") or "none")),
        ("Orchestrator", str(state.get("current_orchestrator_task") or "none")),
        ("Open tasks", str(len(open_tasks))),
        ("Locks", str(len(data["locks"]))),
        ("gdx1", f"{gdx.get('network', 'unknown')} / {gdx.get('ssh', 'unknown')}"),
        ("Agents", str(len(data["agents"]))),
    ]
    return table(rows)
