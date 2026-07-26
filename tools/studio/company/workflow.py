"""One-shot orchestrator workflow for the Studio command center."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_runner import run_agent_task
from .errors import CompanyError
from .planner import plan_task
from .reports import create_review_checkpoint
from .state import CompanyPaths, load_task_board
from .timeutil import now_iso
from .verify import verify_task


def run_orchestrator_workflow(root: Path, request: str, *, dry_run: bool = True) -> Path:
    clean_request = request.strip()
    if not clean_request:
        raise CompanyError("Workflow request is required.")

    plan_path = plan_task(root, clean_request)
    task_id = _task_id_from_plan(plan_path)
    run_report = run_agent_task(root, task_id, dry_run=dry_run)
    review_report = create_review_checkpoint(root, task_id)
    verification = verify_task(root, task_id)
    task = _task(root, task_id)

    summary_dir = CompanyPaths(root).memory_dir / "workflows"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"{task_id}-workflow.md"
    summary_path.write_text(
        "\n".join(
            [
                "# Orchestrator Workflow",
                "",
                f"Task ID: {task_id}",
                f"Status: {task.get('status')}",
                f"Verification: {task.get('verification_status')}",
                f"Mode: {'quick' if dry_run else 'real'}",
                f"Created: {now_iso()}",
                "",
                "## Request",
                "",
                clean_request,
                "",
                "## Steps",
                "",
                f"- Plan: {plan_path.relative_to(root).as_posix()}",
                f"- Agent run: {run_report.relative_to(root).as_posix()}",
                f"- Review checkpoint: {review_report.relative_to(root).as_posix()}",
                f"- Verification: {verification.relative_to(root).as_posix()}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary_path


def _task_id_from_plan(plan_path: Path) -> str:
    name = plan_path.name
    if not name.startswith("task-") or not name.endswith("-plan.md"):
        raise CompanyError(f"Unexpected plan path: {plan_path}")
    return name.removesuffix("-plan.md")


def _task(root: Path, task_id: str) -> dict[str, Any]:
    for task in load_task_board(root).get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise CompanyError(f"Unknown task after workflow: {task_id}")
