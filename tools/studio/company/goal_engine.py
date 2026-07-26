"""Goal-driven orchestration loop for Channel Play Studio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .advance import advance_task
from .agent_runner import run_agent_task
from .errors import CompanyError
from .planner import assign_task, plan_task
from .sessions import start_session
from .state import CompanyPaths, load_company_state, load_task_board, read_json, write_json
from .tasks import find_task, update_task
from .timeutil import now_iso, slugify

GOAL_VERSION = 1
DONE_STATUSES = {"closed", "closed_blocked"}


def goal_state(root: Path) -> dict[str, Any]:
    data = _load_goals(root)
    active = _active_goal(data)
    if active:
        active = _hydrate_goal(root, active)
    return {
        "version": data.get("version", GOAL_VERSION),
        "activeGoalId": data.get("active_goal_id", ""),
        "activeGoal": active,
        "goals": [_hydrate_goal(root, goal) for goal in data.get("goals", [])],
        "path": CompanyPaths(root).goals_json.relative_to(root).as_posix(),
    }


def render_goal_status(root: Path) -> str:
    state = goal_state(root)
    goal = state.get("activeGoal") or {}
    if not goal:
        return "No active goal."
    checks = goal.get("completion", {}).get("checks", [])
    lines = [
        "Goal Engine",
        f"Active: {goal.get('id')}",
        f"Status: {goal.get('status')}",
        f"Objective: {goal.get('objective')}",
        f"Progress: {goal.get('completion', {}).get('passed', 0)}/{goal.get('completion', {}).get('total', 0)}",
        f"Answer: {goal.get('answer', '')}",
        "",
        "Checks:",
    ]
    lines.extend(f"  {check.get('label'):<18} {check.get('status'):<10} {check.get('detail', '')}" for check in checks)
    if goal.get("lastReceipt"):
        lines.extend(["", f"Receipt: {goal['lastReceipt']}"])
    return "\n".join(lines)


def set_goal(root: Path, objective: str, *, max_iterations: int = 12) -> Path:
    clean = objective.strip()
    if not clean:
        raise CompanyError("Goal objective is required.")
    data = _load_goals(root)
    goal_id = _goal_id(data, clean)
    goal = {
        "id": goal_id,
        "objective": clean,
        "status": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "max_iterations": max(1, max_iterations),
        "iterations": 0,
        "task_ids": [],
        "events": [
            {
                "time": now_iso(),
                "type": "goal_set",
                "message": "Goal accepted by chief_orchestrator.",
            }
        ],
        "last_receipt": "",
        "answer": "목표가 설정됐습니다. `company goal run`으로 오케스트라를 실행하세요.",
    }
    data["active_goal_id"] = goal_id
    data.setdefault("goals", []).append(goal)
    _save_goals(root, data)
    receipt = _write_goal_receipt(root, goal, ["goal_set"], "Goal set. Run the orchestra to start execution.")
    goal["last_receipt"] = receipt.relative_to(root).as_posix()
    _replace_goal(data, goal)
    _save_goals(root, data)
    return receipt


def run_goal(root: Path, *, dry_run: bool = True, max_iterations: int | None = None) -> Path:
    data = _load_goals(root)
    goal = _active_goal(data)
    if not goal:
        raise CompanyError("No active goal. Run `company goal set <objective>` first.")
    if goal.get("status") == "complete":
        return _write_goal_receipt(root, _hydrate_goal(root, goal), ["already_complete"], "Goal is already complete.")

    _ensure_goal_session(root, goal)
    _ensure_goal_tasks(root, goal)

    limit = max(1, int(max_iterations or goal.get("max_iterations") or 12))
    actions: list[str] = []
    for _ in range(limit):
        goal["iterations"] = int(goal.get("iterations") or 0) + 1
        task = _next_goal_task(root, goal)
        if not task:
            break
        before = str(task.get("status") or "pending")
        action = _advance_goal_task(root, task, dry_run=dry_run)
        actions.append(action)
        goal.setdefault("events", []).append(
            {
                "time": now_iso(),
                "type": "iteration",
                "message": f"{task['id']} {before} -> {action}",
            }
        )
        task_after = find_task(root, str(task["id"]))
        if _task_blocked(task_after):
            goal["status"] = "blocked"
            goal["answer"] = f"목표 진행이 {task['id']}에서 막혔습니다. 답변 보기/receipt를 확인하세요."
            break
        if not _task_done(task_after) and action.startswith("wait:"):
            break

    hydrated = _hydrate_goal(root, goal)
    completion = hydrated["completion"]
    if completion["total"] > 0 and completion["passed"] == completion["total"]:
        goal["status"] = "complete"
        goal["answer"] = "완벽하게 됐습니다. 목표에 연결된 모든 작업이 검증 통과했습니다."
    elif goal.get("status") != "blocked":
        goal["status"] = "active"
        goal["answer"] = "목표 진행 중입니다. 남은 작업은 Goal panel과 작업판에서 계속 진행할 수 있습니다."

    goal["updated_at"] = now_iso()
    _replace_goal(data, goal)
    _save_goals(root, data)
    receipt = _write_goal_receipt(root, _hydrate_goal(root, goal), actions or ["no_action"], goal["answer"])
    goal["last_receipt"] = receipt.relative_to(root).as_posix()
    _replace_goal(data, goal)
    _save_goals(root, data)
    return receipt


def _advance_goal_task(root: Path, task: dict[str, Any], *, dry_run: bool) -> str:
    task_id = str(task["id"])
    status = str(task.get("status") or "")
    if status in {"planned", "needs_scope"}:
        if not task.get("assigned_agent"):
            assign_task(root, task_id, str(task.get("suggested_agent") or "production_planner"))
            return "assigned"
    task = find_task(root, task_id)
    if status in {"planned", "assigned", "needs_scope"} or not task.get("last_agent_run"):
        report = run_agent_task(root, task_id, dry_run=dry_run)
        return f"agent_run:{report.relative_to(root).as_posix()}"
    if status in {"needs_review", "needs_evidence", "evidence_attached"} or task.get("last_agent_run"):
        report = advance_task(root, task_id)
        return f"advance:{report.relative_to(root).as_posix()}"
    return f"wait:{status or 'pending'}"


def _ensure_goal_tasks(root: Path, goal: dict[str, Any]) -> None:
    existing = [task for task in _goal_tasks(root, goal) if task.get("id")]
    if existing:
        return
    requests = _seed_requests(str(goal.get("objective") or ""))
    for stage, request in requests:
        plan_path = plan_task(root, request)
        task_id = plan_path.name.removesuffix("-plan.md")
        update_task(
            root,
            task_id,
            {
                "goal_id": goal["id"],
                "goal_stage": stage,
                "orchestrated_by": "chief_orchestrator",
            },
        )
        goal.setdefault("task_ids", []).append(task_id)


def _seed_requests(objective: str) -> list[tuple[str, str]]:
    lowered = objective.lower()
    rows = [("planning", f"목표 작업 설계와 의존성 계획 수립: {objective}")]
    needs_research = any(
        token in lowered
        for token in (
            "research",
            "source",
            "citation",
            "notebooklm",
            "latest",
            "benchmark",
            "unity",
            "game",
            "mvp",
            "player",
            "ui",
            "리서치",
            "조사",
            "자료",
            "근거",
            "최신",
            "벤치마크",
            "게임",
            "구현",
            "플레이어",
            "포인트",
            "상점",
            "운영자",
        )
    )
    if needs_research:
        rows.append(("research", f"NotebookLM/Maru 근거 조사와 구현 시사점 정리: {objective}"))
    if any(token in lowered for token in ("codex sdk", "docker", "host-runner", "host runner", "hermes", "agy", "openclaw", "toolchain", "워크스테이션", "연동")):
        rows.append(("toolchain", f"툴체인 연동과 런타임 검증: {objective}"))
    if any(token in lowered for token in ("code", "coding", "python", "javascript", "typescript", "c#", "코드", "코딩", "리팩토링")):
        rows.append(("coding", f"코드 구현과 테스트 증거 생성: {objective}"))
    if any(token in lowered for token in ("obs", "broadcast", "pilot", "capture", "방송", "파일럿", "촬영", "운영자 화면")):
        rows.append(("broadcast", f"OBS/운영자/파일럿 흐름 설계: {objective}"))
    if any(token in lowered for token in ("unity", "game", "mvp", "player", "ui", "게임", "구현", "플레이어", "포인트", "상점", "운영자")):
        rows.append(("implementation", f"Unity MVP 구현 작업: {objective}"))
    if len(rows) == 1 and not any(token in lowered for token in ("계획", "plan", "설계", "구조화")):
        rows.append(("implementation", f"목표 구현 작업: {objective}"))
    return rows


def _ensure_goal_session(root: Path, goal: dict[str, Any]) -> None:
    state = load_company_state(root)["state"]
    if state.get("active_session"):
        return
    start_session(root, f"goal {goal['id']}")


def _goal_tasks(root: Path, goal: dict[str, Any]) -> list[dict[str, Any]]:
    ids = set(str(item) for item in goal.get("task_ids") or [])
    return [
        task
        for task in load_task_board(root).get("tasks", [])
        if task.get("goal_id") == goal.get("id") or str(task.get("id")) in ids
    ]


def _next_goal_task(root: Path, goal: dict[str, Any]) -> dict[str, Any] | None:
    for task in _goal_tasks(root, goal):
        if not _task_done(task):
            return task
    return None


def _hydrate_goal(root: Path, goal: dict[str, Any]) -> dict[str, Any]:
    tasks = _goal_tasks(root, goal)
    checks = [
        {
            "label": str(task.get("goal_stage") or task.get("suggested_agent") or task.get("id")),
            "taskId": str(task.get("id") or ""),
            "status": "passed" if _task_done(task) else "blocked" if _task_blocked(task) else "pending",
            "detail": str(task.get("request") or ""),
            "answerPath": str(task.get("last_agent_run") or task.get("report") or ""),
        }
        for task in tasks
    ]
    passed = sum(1 for check in checks if check["status"] == "passed")
    return {
        **goal,
        "taskIds": [str(task.get("id") or "") for task in tasks],
        "tasks": [
            {
                "id": str(task.get("id") or ""),
                "stage": str(task.get("goal_stage") or ""),
                "status": str(task.get("status") or ""),
                "agent": str(task.get("assigned_agent") or task.get("suggested_agent") or ""),
                "answerPath": str(task.get("last_agent_run") or task.get("report") or ""),
            }
            for task in tasks
        ],
        "lastReceipt": str(goal.get("last_receipt") or ""),
        "completion": {
            "passed": passed,
            "total": len(checks),
            "status": "complete" if checks and passed == len(checks) else str(goal.get("status") or "active"),
            "checks": checks,
        },
    }


def _task_done(task: dict[str, Any]) -> bool:
    return bool(task.get("closed_at")) or task.get("status") in DONE_STATUSES or task.get("verification_status") == "passed"


def _task_blocked(task: dict[str, Any]) -> bool:
    return task.get("status") in {"blocked", "closed_blocked"} or task.get("agent_status") in {"failed", "timeout", "blocked", "auth_missing"}


def _load_goals(root: Path) -> dict[str, Any]:
    path = CompanyPaths(root).goals_json
    if not path.exists():
        return {"version": GOAL_VERSION, "active_goal_id": "", "goals": []}
    data = read_json(path)
    data.setdefault("version", GOAL_VERSION)
    data.setdefault("active_goal_id", "")
    data.setdefault("goals", [])
    return data


def _save_goals(root: Path, data: dict[str, Any]) -> None:
    write_json(CompanyPaths(root).goals_json, data)


def _active_goal(data: dict[str, Any]) -> dict[str, Any] | None:
    active_id = str(data.get("active_goal_id") or "")
    for goal in data.get("goals", []):
        if goal.get("id") == active_id:
            return goal
    return None


def _replace_goal(data: dict[str, Any], goal: dict[str, Any]) -> None:
    goals = data.setdefault("goals", [])
    for index, existing in enumerate(goals):
        if existing.get("id") == goal.get("id"):
            goals[index] = goal
            return
    goals.append(goal)


def _goal_id(data: dict[str, Any], objective: str) -> str:
    base = f"goal-{slugify(objective)[:36] or 'objective'}"
    existing = {str(goal.get("id")) for goal in data.get("goals", [])}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _write_goal_receipt(root: Path, goal: dict[str, Any], actions: list[str], result: str) -> Path:
    directory = CompanyPaths(root).memory_dir / "goals"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{goal['id']}-{slugify(now_iso())}.md"
    completion = goal.get("completion") or {}
    lines = [
        "# Goal Engine Receipt",
        "",
        f"Goal ID: {goal.get('id')}",
        f"Status: {goal.get('status')}",
        f"Created: {now_iso()}",
        "",
        "## Objective",
        "",
        str(goal.get("objective") or ""),
        "",
        "## Result",
        "",
        result,
        "",
        "## Progress",
        "",
        f"{completion.get('passed', 0)}/{completion.get('total', 0)} checks passed",
        "",
        "## Actions",
        "",
        *(f"- {action}" for action in actions),
        "",
        "## Tasks",
        "",
        *(
            f"- {task.get('id')} · {task.get('stage')} · {task.get('status')} · {task.get('agent')} · {task.get('answerPath')}"
            for task in goal.get("tasks", [])
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
