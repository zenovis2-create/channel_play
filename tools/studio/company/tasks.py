"""Task board helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import CompanyError
from .state import CompanyPaths, load_task_board, read_json, save_task_board, write_json
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


def archive_tasks(root: Path, task_ids: list[str], reason: str = "") -> Path:
    if not task_ids:
        raise CompanyError("Usage: company archive <task-id...> [--reason reason]")

    board = load_task_board(root)
    requested = set(task_ids)
    remaining: list[dict[str, Any]] = []
    archived: list[dict[str, Any]] = []
    archived_at = now_iso()

    for task in board.get("tasks", []):
        if task.get("id") in requested:
            item = dict(task)
            item["archived_at"] = archived_at
            item["archive_reason"] = reason or "manual cleanup"
            archived.append(item)
        else:
            remaining.append(task)

    found = {task.get("id") for task in archived}
    missing = sorted(requested - found)
    if missing:
        raise CompanyError(f"Unknown task: {', '.join(missing)}")

    paths = CompanyPaths(root)
    archive_path = paths.memory_dir / "task_archive.json"
    archive = read_json(archive_path) if archive_path.exists() else {"tasks": []}
    existing = [task for task in archive.get("tasks", []) if task.get("id") not in found]
    archive["tasks"] = [*existing, *archived]
    board["tasks"] = remaining

    save_task_board(root, board)
    write_json(archive_path, archive)
    return archive_path
