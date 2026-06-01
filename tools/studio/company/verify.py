"""Verification gate for task closure."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError
from .state import CompanyPaths
from .tasks import find_task, update_task
from .timeutil import now_iso


def verify_task(root: Path, task_id: str) -> Path:
    task = find_task(root, task_id)
    session_dir = _task_session_dir(root, task)
    verification_dir = session_dir / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)
    path = verification_dir / f"{task_id}-verification.md"
    status = "pending"
    reason = "Evidence must be attached by the assigned agent or command-specific check."
    ok, evidence_reason = _evidence_satisfies(task)
    if ok:
        status = "passed"
        reason = evidence_reason
    elif task.get("report") and task.get("status") not in {"done", "closed"}:
        status = "pending"
        reason = f"Report exists but task status is {task.get('status')}; evidence still required."
    path.write_text(
        "\n".join(
            [
                "# Verification",
                "",
                f"Task ID: {task_id}",
                f"Status: {status}",
                f"Checked: {now_iso()}",
                f"Required evidence: {task.get('required_evidence')}",
                "",
                "## Result",
                "",
                reason,
                "",
            ]
        ),
        encoding="utf-8",
    )
    update_task(root, task_id, {"verification": path.relative_to(root).as_posix(), "verification_status": status})
    return path


def attach_evidence(root: Path, task_id: str, evidence_path: str, note: str = "") -> None:
    task = find_task(root, task_id)
    evidence = list(task.get("evidence", []))
    evidence.append({"path": evidence_path, "note": note, "attached_at": now_iso()})
    update_task(root, task_id, {"evidence": evidence, "status": "evidence_attached"})


def close_task(root: Path, task_id: str, blocked_reason: str | None = None) -> None:
    task = find_task(root, task_id)
    if blocked_reason:
        update_task(root, task_id, {"status": "closed_blocked", "blocked_reason": blocked_reason, "closed_at": now_iso()})
        return
    if task.get("verification_status") != "passed":
        raise CompanyError("Task cannot close until verification_status is passed.")
    update_task(root, task_id, {"status": "closed", "closed_at": now_iso()})


def _task_session_dir(root: Path, task: dict) -> Path:
    paths = CompanyPaths(root)
    session = task.get("session")
    if session:
        return paths.sessions_dir / str(session)
    work_order = str(task.get("work_order") or "")
    parts = Path(work_order).parts
    if len(parts) >= 3 and parts[0] == "memory" and parts[1] == "sessions":
        return paths.sessions_dir / parts[2]
    fallback = paths.sessions_dir / "unassigned"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _evidence_satisfies(task: dict) -> tuple[bool, str]:
    evidence = task.get("evidence") or []
    if not evidence:
        return False, "No evidence attached."
    required = str(task.get("required_evidence") or "").lower()
    haystack = " ".join(f"{item.get('path', '')} {item.get('note', '')}" for item in evidence).lower()
    checks = [
        (("unity", "compile", "playtest"), ("unity-check", "unity_check", "screenshot", "playtest")),
        (("blender",), ("blender", "cleanup")),
        (("asset", "metadata", "preview"), ("asset_pipeline", "preview", "import")),
        (("gdx", "server", "bot"), ("gdx", "server", "bot")),
        (("doc", "session", "decision"), ("docs", "memory", "obsidian")),
    ]
    for required_terms, evidence_terms in checks:
        if any(term in required for term in required_terms):
            if any(term in haystack for term in evidence_terms):
                return True, "Typed evidence requirement satisfied."
            return False, f"Evidence does not satisfy required type: {task.get('required_evidence')}"
    return True, "Generic evidence attached."
