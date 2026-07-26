"""Agent report creation."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError
from .sessions import active_session_dir
from .tasks import find_task, update_task
from .timeutil import now_iso

VALID_STATUSES = {"done", "blocked", "needs_review"}


def create_report(root: Path, task_id: str, agent_id: str, status: str) -> Path:
    if status not in VALID_STATUSES:
        raise CompanyError(f"Invalid report status: {status}")
    task = find_task(root, task_id)
    session_dir = active_session_dir(root)
    report_dir = session_dir / "agent_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{task_id}-{agent_id}.md"
    evidence = "TBD"
    path.write_text(
        "\n".join(
            [
                "# Agent Report",
                "",
                f"Task ID: {task_id}",
                f"Role: {agent_id}",
                f"Status: {status}",
                f"Created: {now_iso()}",
                "",
                "## Summary",
                "",
                f"Task request: {task.get('request')}",
                "",
                "## Files Read",
                "",
                "TBD",
                "",
                "## Files Changed",
                "",
                "TBD",
                "",
                "## Decisions",
                "",
                "TBD",
                "",
                "## Evidence",
                "",
                evidence,
                "",
                "## Risks",
                "",
                "TBD",
                "",
                "## Handoff",
                "",
                "chief_orchestrator",
                "",
            ]
        ),
        encoding="utf-8",
    )
    next_status = "needs_evidence" if status == "done" and evidence == "TBD" else status
    update_task(root, task_id, {"status": next_status, "report": path.relative_to(root).as_posix()})
    return path


def create_review_checkpoint(root: Path, task_id: str, reviewer_id: str = "critic_reviewer") -> Path:
    task = find_task(root, task_id)
    review_dir = root / "memory" / "company" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"{task_id}-review.md"
    path.write_text(
        "\n".join(
            [
                "# Review Checkpoint",
                "",
                f"Task ID: {task_id}",
                f"Reviewer: {reviewer_id}",
                f"Status: reviewed",
                f"Created: {now_iso()}",
                "",
                "## Summary",
                "",
                "Studio review checkpoint accepted. Move the task to evidence collection.",
                "",
                "## Task",
                "",
                str(task.get("request") or ""),
                "",
            ]
        ),
        encoding="utf-8",
    )
    runs = list(task.get("agent_runs") or [])
    runs.append(
        {
            "tool": "studio",
            "mode": "review",
            "status": "reviewed",
            "path": path.relative_to(root).as_posix(),
            "created_at": now_iso(),
        }
    )
    update_task(
        root,
        task_id,
        {
            "status": "needs_evidence",
            "review_status": "reviewed",
            "reviewer": reviewer_id,
            "report": path.relative_to(root).as_posix(),
            "agent_runs": runs,
            "agent_status": "reviewed",
            "last_tool": "studio",
            "last_agent_run": path.relative_to(root).as_posix(),
        },
    )
    return path
