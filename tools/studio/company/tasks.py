"""Task board helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import CompanyError
from .state import load_task_board, save_task_board
from .timeutil import now_iso


def next_task_id(tasks: list[dict[str, Any]]) -> str:
    max_seen = 0
    for task in tasks:
        task_id = str(task.get("id", ""))
        if task_id.startswith("task-"):
            try:
                max_seen = max(max_seen, int(task_id.split("-", 1)[1]))
            except ValueError:
                continue
    return f"task-{max_seen + 1:04d}"


def find_task(root: Path, task_id: str) -> dict[str, Any]:
    board = load_task_board(root)
    for task in board.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise CompanyError(f"Unknown task: {task_id}")


def update_task(root: Path, task_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    board = load_task_board(root)
    for task in board.get("tasks", []):
        if task.get("id") == task_id:
            task.update(updates)
            task["updated_at"] = now_iso()
            save_task_board(root, board)
            return task
    raise CompanyError(f"Unknown task: {task_id}")
