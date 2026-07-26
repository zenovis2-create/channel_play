"""Verification gate for task closure."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError
from .state import CompanyPaths
from .tasks import find_task, update_task
from .timeutil import now_iso
from tools.studio.jobs import list_jobs


def verify_task(root: Path, task_id: str) -> Path:
    task = find_task(root, task_id)
    task = {**task, "jobs": _matching_jobs(root, task)}
    session_dir = _task_session_dir(root, task)
    verification_dir = session_dir / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)
    path = verification_dir / f"{task_id}-verification.md"
    evidence = _effective_evidence(task)
    task_for_check = {**task, "evidence": evidence}
    ok, reason = _evidence_satisfies(task_for_check)
    status = "passed" if ok else "pending"
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
    updates = {
        "verification": path.relative_to(root).as_posix(),
        "verification_status": status,
        "evidence": evidence,
    }
    if ok:
        updates["status"] = "closed"
        updates["closed_at"] = now_iso()
    update_task(root, task_id, updates)
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
    if any(
        term in haystack
        for term in ("agent_run", "review checkpoint", "studio checkpoint", "memory/company/reviews", "memory/company/jobs", "receipt")
    ):
        return True, "Studio report, review checkpoint, or job receipt accepted for MVP workflow."
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


def _effective_evidence(task: dict) -> list[dict]:
    evidence = list(task.get("evidence") or [])
    seen = {str(item.get("path") or "") for item in evidence}
    for key, note in (
        ("last_agent_run", "Studio checkpoint from latest run"),
        ("report", "Studio checkpoint from task report"),
    ):
        path = str(task.get(key) or "")
        if path and path not in seen:
            evidence.append({"path": path, "note": note, "attached_at": now_iso()})
            seen.add(path)
    for job in task.get("jobs") or []:
        receipt = job.get("receipt") or {}
        path = str(receipt.get("path") or "")
        if path and path not in seen:
            evidence.append({"path": path, "note": "Job receipt accepted as Studio evidence", "attached_at": now_iso()})
            seen.add(path)
    return evidence


def _matching_jobs(root: Path, task: dict) -> list[dict]:
    task_id = str(task.get("id") or "")
    if not task_id:
        return []
    rows = []
    for job in list_jobs(root, limit=200):
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        job_task_id = str(job.get("taskId") or payload.get("taskId") or payload.get("task_id") or "")
        if job_task_id == task_id:
            rows.append(job)
    return rows
