"""Automatic task state advancement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import CompanyError
from .reports import create_review_checkpoint
from .tasks import find_task, update_task
from .timeutil import now_iso, slugify
from .verify import verify_task


def advance_task(root: Path, task_id: str) -> Path:
    """Advance a task through every safe transition available right now."""
    task = find_task(root, task_id)
    actions: list[str] = []

    if _is_done(task):
        if task.get("status") not in {"closed", "closed_blocked"}:
            task = update_task(root, task_id, {"status": "closed", "closed_at": now_iso()})
        actions.append("already_complete")
        return _write_advance_report(root, task_id, actions, "Task is already complete.")

    if _needs_review(task) and not _has_review(task):
        review = create_review_checkpoint(root, task_id, str(task.get("suggested_reviewer") or "critic_reviewer"))
        actions.append(f"review:{review.relative_to(root).as_posix()}")
        task = find_task(root, task_id)

    if _can_verify(task):
        verification = verify_task(root, task_id)
        actions.append(f"verify:{verification.relative_to(root).as_posix()}")
        task = find_task(root, task_id)

    if _is_done(task):
        actions.append("closed")
        return _write_advance_report(root, task_id, actions, "Task advanced to completion.")

    if not actions:
        actions.append("blocked:no_safe_transition")
        return _write_advance_report(root, task_id, actions, _blocked_reason(task))

    return _write_advance_report(root, task_id, actions, _blocked_reason(task))


def _is_done(task: dict[str, Any]) -> bool:
    return bool(task.get("closed_at")) or task.get("status") in {"closed", "closed_blocked"} or task.get("verification_status") == "passed"


def _needs_review(task: dict[str, Any]) -> bool:
    return task.get("status") == "needs_review" or bool(task.get("last_agent_run") or task.get("report"))


def _has_review(task: dict[str, Any]) -> bool:
    if task.get("review_status") == "reviewed":
        return True
    for run in task.get("agent_runs") or []:
        if run.get("mode") == "review":
            return True
    report = str(task.get("report") or "")
    return report.startswith("memory/company/reviews/")


def _can_verify(task: dict[str, Any]) -> bool:
    if task.get("verification_status") == "passed":
        return False
    if task.get("status") in {"needs_evidence", "evidence_attached"}:
        return True
    return bool(task.get("evidence") or task.get("last_agent_run") or task.get("report"))


def _blocked_reason(task: dict[str, Any]) -> str:
    status = str(task.get("status") or "unknown")
    if status in {"planned", "assigned", "pending"} or not task.get("last_agent_run"):
        return "No run, report, receipt, or evidence exists yet. Run an agent first."
    return f"No safe auto-advance transition from status {status}."


def _write_advance_report(root: Path, task_id: str, actions: list[str], result: str) -> Path:
    directory = root / "memory" / "company" / "advances"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{task_id}-{slugify(now_iso())}.md"
    lines = [
        "# Auto Advance",
        "",
        f"Task ID: {task_id}",
        f"Created: {now_iso()}",
        "",
        "## Result",
        "",
        result,
        "",
        "## Actions",
        "",
        *(f"- {action}" for action in actions),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    if actions and actions[0].startswith("blocked:"):
        raise CompanyError(result)
    return path
