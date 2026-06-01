"""Path resolution for Channel Play tooling."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError


MARKER_PATHS = (
    "docs/channel_play_agent_company_plan.md",
    "memory/company/state.json",
    "Assets",
)


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and any((candidate / marker).exists() for marker in MARKER_PATHS):
            return candidate
    raise CompanyError("Could not locate channel_play repo root.")


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
