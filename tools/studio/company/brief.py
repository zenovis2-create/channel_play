"""Current brief generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .git_info import git_head, git_short_status
from .state import CompanyPaths, load_company_state


def build_brief(root: Path) -> str:
    paths = CompanyPaths(root)
    data = load_company_state(root)
    state = data["state"]
    dirty = git_short_status(root)
    gdx = state.get("gdx1", {})
    open_tasks = [task for task in data["tasks"] if task.get("status") not in {"closed", "closed_blocked"}]
    generated = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = [
        "# Current Brief",
        "",
        f"Generated: {generated}",
        f"Repo: {root}",
        f"Git: {git_head(root)}",
        f"Dirty files: {len(dirty)}",
        f"Current session: {state.get('active_session') or 'none'}",
        f"Open tasks: {len(open_tasks)}",
        f"Active locks: {len(data['locks'])}",
        f"gdx1: {gdx.get('network', 'unknown')} / {gdx.get('ssh', 'unknown')}",
        "",
        "## Current Context",
        "",
        data["context"] or "No current context recorded.",
        "",
        "## Registered Agents",
        "",
    ]

    for agent in data["agents"]:
        lines.append(f"- {agent.get('id', 'unknown')}: {agent.get('profile', '')}")

    lines.extend(
        [
            "",
            "## Active Locks",
            "",
        ]
    )
    if data["locks"]:
        for lock in data["locks"]:
            lines.append(f"- {lock.get('path', 'unknown')} owned by {lock.get('owner', 'unknown')}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Git Working Tree",
            "",
        ]
    )
    if dirty:
        lines.extend(f"- {line}" for line in dirty[:30])
    else:
        lines.append("- clean")

    lines.extend(
        [
            "",
            "## Latest Session",
            "",
            _latest_session_summary(root),
            "",
            "## Memory Freshness",
            "",
            _memory_freshness(paths.current_context_md),
            "",
            "## Required Rules",
            "",
            "- One writer per Unity scene, prefab folder, or script system.",
            "- No broad agent fanout before scope check.",
            "- No done state without evidence.",
            "- Decisions that affect future work go to Obsidian or decision log.",
            "",
            "## Next Recommended Action",
            "",
            "- Implement `company session start/end`, then work orders and locks.",
            "",
        ]
    )

    return _guard_size("\n".join(lines))


def write_brief(root: Path) -> Path:
    paths = CompanyPaths(root)
    paths.current_brief_md.write_text(build_brief(root), encoding="utf-8")
    return paths.current_brief_md


def _latest_session_summary(root: Path) -> str:
    sessions = sorted((root / "memory" / "sessions").glob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    sessions = [path for path in sessions if path.is_dir() and (path / "summary.md").exists()]
    if not sessions:
        return "- none"
    latest = sessions[-1]
    return f"- {latest.name}: {(latest / 'summary.md').relative_to(root).as_posix()}"


def _memory_freshness(path: Path) -> str:
    if not path.exists():
        return "- warning: current context missing"
    age_seconds = datetime.now().timestamp() - path.stat().st_mtime
    if age_seconds > 7 * 24 * 60 * 60:
        return "- warning: current context older than 7 days"
    return "- current context fresh"


def _guard_size(text: str, max_lines: int = 220) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    kept = lines[:max_lines]
    kept.extend(["", "## Truncated", "", f"Brief exceeded {max_lines} lines. Regenerate with narrower scope."])
    return "\n".join(kept)
