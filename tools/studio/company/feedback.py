"""Feedback record creation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .brief import write_brief
from .errors import CompanyError
from .locks import lock_path, unlock_path
from .planner import assign_task, plan_task
from .reports import create_report
from .sessions import end_session, start_session
from .unity import unity_check
from .verify import attach_evidence, close_task, verify_task


def feedback_new(root: Path) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    base = root / "reviews" / day
    base.mkdir(parents=True, exist_ok=True)
    existing = sorted(path for path in base.glob("feedback-*") if path.is_dir())
    number = len(existing) + 1
    folder = base / f"feedback-{number:04d}"
    folder.mkdir()
    latest_capture = _latest_capture(root)
    screenshot_text = latest_capture.relative_to(root).as_posix() if latest_capture else "TBD"
    note = folder / "feedback.md"
    note.write_text(
        "\n".join(
            [
                f"# Feedback {number:04d}",
                "",
                "Scene: TBD",
                f"Screenshot: {screenshot_text}",
                "Priority: P2",
                "Status: open",
                "",
                "## Observation",
                "",
                "TBD",
                "",
                "## Requested Change",
                "",
                "TBD",
                "",
                "## Agent Interpretation",
                "",
                "TBD",
                "",
                "## Files Changed",
                "",
                "TBD",
                "",
                "## Verification",
                "",
                "TBD",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return note


def feedback_process(root: Path, feedback_path: str) -> Path:
    feedback = (root / feedback_path).resolve() if not Path(feedback_path).is_absolute() else Path(feedback_path)
    if not feedback.exists():
        raise CompanyError(f"Feedback file not found: {feedback_path}")

    start_session(root, f"process {feedback.name}")
    locked = False
    try:
        write_brief(root)
        qa_task = _task_id_from_plan(plan_task(root, f"reproduce screenshot feedback {feedback}"))
        unity_task = _task_id_from_plan(plan_task(root, f"fix player movement feedback {feedback}"))
        review_task = _task_id_from_plan(plan_task(root, f"review risk feedback {feedback}"))
        assign_task(root, qa_task, "qa_playtest")
        assign_task(root, unity_task, "unity_gameplay")
        assign_task(root, review_task, "critic_reviewer")
        lock_path(root, "Assets/_Project/Scripts/Gameplay", "unity_gameplay", unity_task)
        locked = True
        unity_evidence = unity_check(root, [])
        for task_id, agent in ((qa_task, "qa_playtest"), (unity_task, "unity_gameplay"), (review_task, "critic_reviewer")):
            create_report(root, task_id, agent, "needs_review")
            attach_evidence(root, task_id, unity_evidence.relative_to(root).as_posix(), "feedback workflow evidence")
            verify_task(root, task_id)
            close_task(root, task_id)
        _close_feedback(feedback, unity_evidence.relative_to(root).as_posix())
    finally:
        if locked:
            unlock_path(root, "Assets/_Project/Scripts/Gameplay")
        end_session(root)
    return feedback


def _latest_capture(root: Path) -> Path | None:
    captures = sorted((root / "reviews" / "captures").glob("screen-*"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return captures[-1] if captures else None


def _task_id_from_plan(path: Path) -> str:
    name = path.name
    return name.split("-plan.md", 1)[0]


def _close_feedback(path: Path, evidence: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("Status: open", "Status: closed")
    text += f"\n## Closure Evidence\n\n- {evidence}\n"
    path.write_text(text, encoding="utf-8")
