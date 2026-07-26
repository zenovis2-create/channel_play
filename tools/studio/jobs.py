"""Durable command job ledger for the Studio web cockpit."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tools.studio.company.paths import rel

MAX_STREAM_CHARS = 80_000
TERMINAL_STATUSES = {"succeeded", "failed", "timeout", "cancelled"}

_LOCK = threading.RLock()


def create_job(root: Path, command_name: str, command: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    """Create a queued job record and persist it before execution starts."""
    now = _now()
    job = {
        "id": _job_id(),
        "commandName": command_name,
        "command": command,
        "payload": _safe_payload(payload),
        "taskId": _payload_task_id(payload),
        "agentId": str(payload.get("agentId") or payload.get("agent") or ""),
        "tool": str(payload.get("tool") or ""),
        "status": "queued",
        "ok": None,
        "exit": None,
        "stdout": "",
        "stderr": "",
        "createdAt": now,
        "updatedAt": now,
        "startedAt": "",
        "endedAt": "",
        "workflowPath": "",
        "receipt": {},
        "events": [
            {
                "time": now,
                "type": "queued",
                "message": f"{command_name} 명령이 작업 원장에 등록되었습니다.",
            }
        ],
    }
    with _LOCK:
        jobs = _read_jobs(root)
        jobs.append(job)
        _write_jobs(root, jobs)
    return job


def start_job(
    root: Path,
    job_id: str,
    *,
    timeout: int,
    env: dict[str, str],
    task_id_parser: Callable[[str], str] | None = None,
) -> None:
    """Run a persisted job in a daemon thread."""
    thread = threading.Thread(
        target=_run_job,
        args=(root, job_id, timeout, env, task_id_parser),
        name=f"channel-play-job-{job_id}",
        daemon=True,
    )
    thread.start()


def list_jobs(root: Path, limit: int = 12) -> list[dict[str, Any]]:
    with _LOCK:
        jobs = _read_jobs(root)
    return [_public_job(job) for job in sorted(jobs, key=lambda row: row.get("createdAt", ""), reverse=True)[:limit]]


def get_job(root: Path, job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        for job in _read_jobs(root):
            if job.get("id") == job_id:
                return _public_job(job)
    return None


def _run_job(
    root: Path,
    job_id: str,
    timeout: int,
    env: dict[str, str],
    task_id_parser: Callable[[str], str] | None,
) -> None:
    job = _update_job(root, job_id, lambda row: _mark_started(row))
    if not job:
        return

    command = [str(item) for item in job.get("command") or []]
    execution_command = _execution_command(command)
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    process: subprocess.Popen[str] | None = None

    try:
        process = subprocess.Popen(
            execution_command,
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        _append_event(root, job_id, "process", f"PID {process.pid}로 실행을 시작했습니다.")

        readers = [
            threading.Thread(
                target=_read_stream,
                args=(root, job_id, process.stdout, "stdout", stdout_parts),
                daemon=True,
            ),
            threading.Thread(
                target=_read_stream,
                args=(root, job_id, process.stderr, "stderr", stderr_parts),
                daemon=True,
            ),
        ]
        for reader in readers:
            reader.start()

        try:
            exit_code = process.wait(timeout=timeout)
            status = "succeeded" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            process.kill()
            exit_code = process.wait()
            status = "timeout"
            _append_event(root, job_id, "timeout", f"{timeout}초 제한을 초과해 프로세스를 종료했습니다.")

        for reader in readers:
            reader.join(timeout=2)

        stdout = _truncate("".join(stdout_parts))
        stderr = _truncate("".join(stderr_parts))
        task_id = task_id_parser(stdout) if task_id_parser else str(job.get("taskId") or "")
        _finish_job(root, job_id, status, exit_code, stdout, stderr, task_id)
    except Exception as exc:  # pragma: no cover - defensive process boundary
        if process and process.poll() is None:
            process.kill()
        _finish_job(root, job_id, "failed", 1, "".join(stdout_parts), f"{''.join(stderr_parts)}\n{exc}".strip(), "")


def _execution_command(command: list[str]) -> list[str]:
    """Use Python for the extensionless channelctl entrypoint on Windows."""
    if os.name != "nt" or not command:
        return command
    entrypoint = Path(command[0])
    if entrypoint.name == "channelctl" and entrypoint.is_file():
        return [sys.executable, *command]
    return command


def _read_stream(root: Path, job_id: str, stream, kind: str, sink: list[str]) -> None:
    if stream is None:
        return
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            sink.append(line)
            text = line.rstrip()
            if text:
                _append_event(root, job_id, kind, text)
    finally:
        stream.close()


def _mark_started(job: dict[str, Any]) -> None:
    now = _now()
    job["status"] = "running"
    job["startedAt"] = now
    job["updatedAt"] = now
    job.setdefault("events", []).append(
        {
            "time": now,
            "type": "started",
            "message": "허용된 명령 실행을 시작했습니다.",
        }
    )


def _finish_job(root: Path, job_id: str, status: str, exit_code: int, stdout: str, stderr: str, task_id: str) -> None:
    def mutate(job: dict[str, Any]) -> None:
        now = _now()
        job["status"] = status
        job["ok"] = status == "succeeded"
        job["exit"] = exit_code
        job["stdout"] = _truncate(stdout)
        job["stderr"] = _truncate(stderr)
        job["taskId"] = task_id or str(job.get("taskId") or "")
        if job["taskId"]:
            job["workflowPath"] = f"memory/company/workflows/{job['taskId']}-workflow.md"
        job["endedAt"] = now
        job["updatedAt"] = now
        job.setdefault("events", []).append(
            {
                "time": now,
                "type": "completed" if status == "succeeded" else status,
                "message": _completion_message(status, exit_code),
            }
        )
        job["receipt"] = _write_receipt(root, job)

    _update_job(root, job_id, mutate)


def _append_event(root: Path, job_id: str, event_type: str, message: str) -> None:
    def mutate(job: dict[str, Any]) -> None:
        now = _now()
        events = job.setdefault("events", [])
        events.append({"time": now, "type": event_type, "message": message[:2000]})
        job["updatedAt"] = now
        if len(events) > 240:
            job["events"] = events[-240:]

    _update_job(root, job_id, mutate)


def _update_job(root: Path, job_id: str, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any] | None:
    with _LOCK:
        jobs = _read_jobs(root)
        target: dict[str, Any] | None = None
        for job in jobs:
            if job.get("id") == job_id:
                mutate(job)
                target = job
                break
        if target is not None:
            _write_jobs(root, jobs)
        return target


def _write_receipt(root: Path, job: dict[str, Any]) -> dict[str, Any]:
    jobs_dir = _jobs_dir(root)
    path = jobs_dir / f"{job['id']}-receipt.md"
    status = str(job.get("status") or "unknown")
    task_id = str(job.get("taskId") or "")
    artifacts = _receipt_artifacts(root, job)
    operation = _operation_report(root, artifacts)
    outcome = _receipt_outcome(status, operation)
    summary = _receipt_summary(job, operation)
    verification_status = _receipt_verification_status(status, outcome)
    if task_id:
        workflow_path = f"memory/company/workflows/{task_id}-workflow.md"
        if workflow_path not in artifacts:
            artifacts.append(workflow_path)
    lines = [
        f"# Job Receipt: {job['id']}",
        "",
        f"- Command: {job.get('commandName', '')}",
        f"- Status: {status}",
        f"- Exit: {job.get('exit')}",
        f"- Started: {job.get('startedAt') or 'not-started'}",
        f"- Ended: {job.get('endedAt') or 'not-ended'}",
        f"- Task: {task_id or 'none'}",
        "",
        "## Summary",
        summary,
        "",
        "## Changed Files",
        *["- not tracked by this command"],
        "",
        "## Artifacts",
        *(f"- {artifact}" for artifact in artifacts),
        *([] if artifacts else ["- none"]),
        "",
        "## Verification",
        f"- Status: {verification_status}",
        f"- Command: {job.get('commandName', '')}",
        "",
        "## Next Action",
        _next_action(status, outcome, operation),
        "",
        "## Recent Events",
        *[
            f"- {event.get('time', '')} [{event.get('type', '')}] {event.get('message', '')}"
            for event in (job.get("events") or [])[-24:]
        ],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "path": rel(root, path),
        "outcome": outcome,
        "summary": summary,
        "changedFiles": [],
        "artifacts": artifacts,
        "verification": {
            "status": verification_status,
            "commands": [str(job.get("commandName") or "")],
            "notes": _completion_message(status, int(job.get("exit") or 0)),
        },
        "nextAction": _next_action(status, outcome, operation),
    }


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    events = list(job.get("events") or [])
    return {
        **job,
        "events": events[-80:],
        "isTerminal": job.get("status") in TERMINAL_STATUSES,
    }


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        if any(marker in key_text.lower() for marker in ("token", "secret", "password", "key")):
            safe[key_text] = "[redacted]"
        else:
            safe[key_text] = value
    return safe


def _payload_task_id(payload: dict[str, Any]) -> str:
    for key in ("taskId", "task_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _receipt_artifacts(root: Path, job: dict[str, Any]) -> list[str]:
    artifacts: list[str] = []
    for key in ("workflowPath",):
        value = str(job.get(key) or "").strip()
        if value:
            artifacts.append(value)
    for event in job.get("events") or []:
        message = str(event.get("message") or "")
        for marker in ("memory/", "runs/", "reviews/", "docs/"):
            if marker not in message:
                continue
            path = message[message.find(marker) :].split()[0].strip().rstrip(".,")
            if path and (root / path).exists() and path not in artifacts:
                artifacts.append(path)
    return artifacts


def _receipt_summary(job: dict[str, Any], operation: dict[str, Any] | None = None) -> str:
    if operation and operation.get("_operation_type") == "simworld_route_plan":
        route = _simworld_route(operation)
        route_status = str(route.get("status") or "")
        if route_status in {"needs_worker", "blocked"}:
            reason = str(route.get("reason") or route_status)
            return f"SimWorld UE 경로가 아직 준비되지 않았습니다. status={route_status}; reason={reason}"
    if operation and _is_blocked_operation(operation):
        reason = str(operation.get("reason") or "blocked")
        action = str(operation.get("action") or "")
        return f"하위 실행 결과가 차단 상태입니다. action={action}; reason={reason}"
    status = str(job.get("status") or "unknown")
    if status == "succeeded":
        return "명령이 완료되었고 stdout/stderr, 이벤트, 결과물이 원장에 저장되었습니다."
    if status == "timeout":
        return "명령이 제한 시간을 초과해 종료되었습니다. 이벤트와 stderr를 확인해야 합니다."
    if status == "cancelled":
        return "명령이 취소되었습니다."
    return "명령이 실패했습니다. stderr와 최근 이벤트를 기준으로 다음 조치를 결정해야 합니다."


def _completion_message(status: str, exit_code: int) -> str:
    if status == "succeeded":
        return f"명령이 정상 종료되었습니다. exit={exit_code}"
    if status == "timeout":
        return f"명령이 시간 초과로 종료되었습니다. exit={exit_code}"
    return f"명령이 실패했습니다. exit={exit_code}"


def _receipt_outcome(status: str, operation: dict[str, Any] | None = None) -> str:
    if operation and operation.get("_operation_type") == "simworld_route_plan":
        route_status = str(_simworld_route(operation).get("status") or "")
        if route_status == "needs_worker":
            return "worker_blocked"
        if route_status == "blocked":
            return "blocked"
    if operation and _is_blocked_operation(operation):
        return "blocked"
    return "completed" if status == "succeeded" else status


def _receipt_verification_status(status: str, outcome: str) -> str:
    if outcome in {"blocked", "worker_blocked"}:
        return "blocked"
    return "passed" if status == "succeeded" else "pending"


def _next_action(status: str, outcome: str | None = None, operation: dict[str, Any] | None = None) -> str:
    if outcome in {"blocked", "worker_blocked"}:
        target = str(operation.get("targetWorker") or "compatible worker") if operation else "compatible worker"
        if operation and operation.get("_operation_type") == "simworld_route_plan":
            target = str(_simworld_route(operation).get("worker") or target)
        return f"{target} 준비 또는 호환 빌드 확보 전까지 재실행하지 않습니다."
    if status == "succeeded":
        return "결과 receipt와 연결된 작업/산출물을 확인한 뒤 다음 제작 단계로 진행합니다."
    if status == "timeout":
        return "장시간 실행 원인을 확인하고 더 작은 작업 단위로 재시도합니다."
    return "stderr와 이벤트를 확인하고 실패한 명령을 수정한 뒤 재실행합니다."


def _operation_report(root: Path, artifacts: list[str]) -> dict[str, Any] | None:
    for artifact in artifacts:
        path = root / artifact
        if "simworld-start-server-" not in artifact:
            if "simworld-route-plan-" not in artifact:
                continue
            run_dir = path.parent if path.name == "receipt.md" else path
            report_path = run_dir / "route_plan.json"
            operation_type = "simworld_route_plan"
        else:
            run_dir = path.parent if path.name == "receipt.md" else path
            report_path = run_dir / "start_server.json"
            operation_type = "simworld_start_server"
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            data["_operation_type"] = operation_type
            return data
    return None


def _is_blocked_operation(operation: dict[str, Any]) -> bool:
    values = {
        str(operation.get("status") or ""),
        str(operation.get("action") or ""),
        str(operation.get("routeStatus") or ""),
    }
    return any(value in {"blocked", "simworld_start_blocked", "not_started", "needs_worker"} for value in values)


def _simworld_route(operation: dict[str, Any]) -> dict[str, Any]:
    routes = operation.get("routes") if isinstance(operation.get("routes"), dict) else {}
    route = routes.get("simworldUeServer") if isinstance(routes.get("simworldUeServer"), dict) else {}
    return route


def _read_jobs(root: Path) -> list[dict[str, Any]]:
    path = _jobs_json(root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    jobs = data.get("jobs", [])
    return jobs if isinstance(jobs, list) else []


def _write_jobs(root: Path, jobs: list[dict[str, Any]]) -> None:
    path = _jobs_json(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"jobs": jobs[-200:]}
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _jobs_json(root: Path) -> Path:
    return _jobs_dir(root) / "jobs.json"


def _jobs_dir(root: Path) -> Path:
    path = root / "memory" / "company" / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"job-{stamp}-{secrets.token_hex(3)}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _truncate(text: str) -> str:
    if len(text) <= MAX_STREAM_CHARS:
        return text
    return text[-MAX_STREAM_CHARS:]
