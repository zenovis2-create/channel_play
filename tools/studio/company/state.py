"""JSON state loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import CompanyError


@dataclass(frozen=True)
class CompanyPaths:
    root: Path

    @property
    def memory_dir(self) -> Path:
        return self.root / "memory" / "company"

    @property
    def sessions_dir(self) -> Path:
        return self.root / "memory" / "sessions"

    @property
    def state_json(self) -> Path:
        return self.memory_dir / "state.json"

    @property
    def agent_registry_json(self) -> Path:
        return self.memory_dir / "agent_registry.json"

    @property
    def tool_adapters_json(self) -> Path:
        return self.memory_dir / "tool_adapters.json"

    @property
    def task_board_json(self) -> Path:
        return self.memory_dir / "task_board.json"

    @property
    def locks_json(self) -> Path:
        return self.memory_dir / "locks.json"

    @property
    def current_context_md(self) -> Path:
        return self.memory_dir / "current_context.md"

    @property
    def current_brief_md(self) -> Path:
        return self.memory_dir / "current_brief.md"

    @property
    def templates_dir(self) -> Path:
        return self.root / "tools" / "studio" / "templates"

    @property
    def dashboard_html(self) -> Path:
        return self.root / "tools" / "studio" / "dashboard.html"


def read_json(path: Path, expected_type: type = dict) -> Any:
    if not path.exists():
        raise CompanyError(f"Missing required file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CompanyError(f"Invalid JSON: {path}: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(data, expected_type):
        raise CompanyError(f"Invalid JSON shape: {path}: expected {expected_type.__name__}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8").strip()


def load_company_state(root: Path) -> dict[str, Any]:
    paths = CompanyPaths(root)
    return {
        "state": read_json(paths.state_json),
        "agents": read_json(paths.agent_registry_json).get("agents", []),
        "tasks": read_json(paths.task_board_json).get("tasks", []),
        "locks": read_json(paths.locks_json).get("locks", []),
        "context": read_text(paths.current_context_md),
    }


def load_task_board(root: Path) -> dict[str, Any]:
    return read_json(CompanyPaths(root).task_board_json)


def save_task_board(root: Path, board: dict[str, Any]) -> None:
    board.setdefault("tasks", [])
    write_json(CompanyPaths(root).task_board_json, board)


def load_locks(root: Path) -> dict[str, Any]:
    return read_json(CompanyPaths(root).locks_json)


def save_locks(root: Path, locks: dict[str, Any]) -> None:
    locks.setdefault("locks", [])
    write_json(CompanyPaths(root).locks_json, locks)


def load_state_json(root: Path) -> dict[str, Any]:
    return read_json(CompanyPaths(root).state_json)


def save_state_json(root: Path, state: dict[str, Any]) -> None:
    write_json(CompanyPaths(root).state_json, state)
