"""Company session lifecycle."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError
from .state import CompanyPaths, load_state_json, save_state_json
from .timeutil import now_iso, session_id


def active_session_dir(root: Path) -> Path:
    state = load_state_json(root)
    active = state.get("active_session")
    if not active:
        raise CompanyError("No active company session.")
    return CompanyPaths(root).sessions_dir / str(active)


def start_session(root: Path, goal: str) -> Path:
    if not goal:
        raise CompanyError("Session goal is required.")
    paths = CompanyPaths(root)
    state = load_state_json(root)
    if state.get("active_session"):
        raise CompanyError(f"Session already active: {state['active_session']}")

    sid = session_id(goal)
    session_dir = paths.sessions_dir / sid
    for child in ("work_orders", "agent_reports", "verification"):
        (session_dir / child).mkdir(parents=True, exist_ok=False)

    context = session_dir / "context.md"
    context.write_text(
        "\n".join(
            [
                "# Session Context",
                "",
                f"Session ID: {sid}",
                f"Goal: {goal}",
                f"Started: {now_iso()}",
                "",
                "## Starting State",
                "",
                "- Created by `channelctl company session start`.",
                "",
                "## Scope",
                "",
                "TBD",
                "",
                "## Selected Agents",
                "",
                "TBD",
                "",
                "## Required Evidence",
                "",
                "TBD",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (session_dir / "summary.md").write_text("# Session Summary\n\nStatus: active\n", encoding="utf-8")

    state["active_session"] = sid
    state["updated_at"] = now_iso()
    save_state_json(root, state)
    return context


def end_session(root: Path) -> Path:
    state = load_state_json(root)
    active = state.get("active_session")
    if not active:
        raise CompanyError("No active company session.")
    session_dir = CompanyPaths(root).sessions_dir / str(active)
    summary = session_dir / "summary.md"
    summary.write_text(
        "\n".join(
            [
                "# Session Summary",
                "",
                f"Session ID: {active}",
                f"Ended: {now_iso()}",
                "",
                "## Changes",
                "",
                "TBD",
                "",
                "## Evidence",
                "",
                "TBD",
                "",
                "## Next Actions",
                "",
                "TBD",
                "",
            ]
        ),
        encoding="utf-8",
    )
    state["active_session"] = None
    state["current_orchestrator_task"] = None
    state["updated_at"] = now_iso()
    save_state_json(root, state)
    return summary
