"""Rule-based task planning and assignment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import CompanyError
from .locks import assert_no_conflict
from .sessions import active_session_dir
from .state import CompanyPaths, load_task_board, read_json, save_task_board
from .tasks import find_task, next_task_id, update_task
from .timeutil import now_iso


ROUTES: list[tuple[tuple[str, ...], str, list[str], str]] = [
    (("movement", "mission", "item", "operator", "ui", "player", "gameplay"), "unity_gameplay", ["Assets/_Project/Scripts/Gameplay"], "Unity compile or playtest evidence"),
    (("architecture", "scriptableobject", "scene structure", "prefab"), "unity_architect", ["Assets/_Project/Scripts"], "Unity compile evidence"),
    (("server", "netcode", "multiplayer", "bot"), "multiplayer_server", ["Assets/_Project/Scripts"], "server or design evidence"),
    (("blender", "mesh", "pivot", "collider", "material"), "technical_artist_blender", ["asset_pipeline/blender_work"], "Blender cleanup report"),
    (("2d", "3d", "asset", "prop", "generation"), "asset_factory", ["asset_pipeline"], "asset metadata and preview/import note"),
    (("sound", "sfx", "music", "audio"), "sound_designer", ["obsidian/channel_play/04_Sound"], "sound brief"),
    (("bug", "screenshot", "feedback", "reproduce"), "qa_playtest", ["reviews"], "reproduction note"),
    (("build", "compile", "performance", "frame"), "performance_build", ["runs", "tools"], "build or performance log"),
    (("gdx1", "soak", "worker"), "gdx_ops", ["runs", "logs"], "gdx probe or run log"),
    (("docs", "memory", "decision", "session"), "librarian", ["docs", "memory/company", "obsidian/channel_play"], "doc diff"),
    (("review", "risk", "critique"), "critic_reviewer", ["reviews"], "review note"),
]


def _route(request: str) -> tuple[str, list[str], str]:
    haystack = request.lower()
    for keywords, agent, paths, evidence in ROUTES:
        if any(keyword in haystack for keyword in keywords):
            return agent, paths, evidence
    return "librarian", ["memory/company"], "session or decision note"


def _agent_ids(root: Path) -> set[str]:
    registry = read_json(CompanyPaths(root).agent_registry_json)
    return {str(agent.get("id")) for agent in registry.get("agents", [])}


def plan_task(root: Path, request: str) -> Path:
    if not request:
        raise CompanyError("Plan request is required.")
    agent, paths, evidence = _route(request)
    reviewer = _reviewer_for(request)
    scope_status = "needs_scope" if _unclear_scope(request) else "planned"
    board = load_task_board(root)
    tasks = board.setdefault("tasks", [])
    task_id = next_task_id(tasks)
    task = {
        "id": task_id,
        "request": request,
        "status": scope_status,
        "suggested_agent": agent,
        "suggested_reviewer": reviewer,
        "assigned_agent": None,
        "allowed_write_paths": paths,
        "required_evidence": evidence,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "work_order": None,
        "report": None,
        "verification": None,
    }
    tasks.append(task)
    save_task_board(root, board)
    return _write_plan(root, task)


def assign_task(root: Path, task_id: str, agent_id: str) -> Path:
    if agent_id not in _agent_ids(root):
        raise CompanyError(f"Unknown agent: {agent_id}")
    task = find_task(root, task_id)
    paths = [str(path) for path in task.get("allowed_write_paths", [])]
    assert_no_conflict(root, paths)
    session_dir = active_session_dir(root)
    work_orders = session_dir / "work_orders"
    work_orders.mkdir(parents=True, exist_ok=True)
    path = work_orders / f"{task_id}-{agent_id}.md"
    text = _work_order_text(task, agent_id)
    path.write_text(text, encoding="utf-8")
    update_task(
        root,
        task_id,
        {
            "status": "assigned",
            "assigned_agent": agent_id,
            "session": session_dir.name,
            "work_order": path.relative_to(root).as_posix(),
        },
    )
    return path


def _write_plan(root: Path, task: dict[str, Any]) -> Path:
    path = CompanyPaths(root).memory_dir / f"{task['id']}-plan.md"
    path.write_text(
        "\n".join(
            [
                "# Task Plan",
                "",
                f"Task ID: {task['id']}",
                f"Status: {task['status']}",
                f"Suggested agent: {task['suggested_agent']}",
                f"Suggested reviewer: {task.get('suggested_reviewer') or 'none'}",
                f"Required evidence: {task['required_evidence']}",
                "",
                "## Request",
                "",
                str(task["request"]),
                "",
                "## Allowed Write Paths",
                "",
                *[f"- {path}" for path in task.get("allowed_write_paths", [])],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _work_order_text(task: dict[str, Any], agent_id: str) -> str:
    return "\n".join(
        [
            "# Work Order",
            "",
            f"Task ID: {task['id']}",
            f"Role: {agent_id}",
            f"Goal: {task['request']}",
            "Read first: agents/company.md, agents/memory_policy.md, memory/company/current_brief.md",
            "Allowed write paths:",
            *[f"- {path}" for path in task.get("allowed_write_paths", [])],
            "Forbidden paths: any locked path not assigned to this task",
            "Inputs: see task request and current brief",
            "Expected output: changed files or report matching role contract",
            f"Verification required: {task.get('required_evidence')}",
            f"Suggested reviewer: {task.get('suggested_reviewer') or 'none'}",
            "Handoff target: chief_orchestrator",
            "Timeout: current session",
            "",
        ]
    )


def _reviewer_for(request: str) -> str | None:
    haystack = request.lower()
    risky = ("architecture", "server", "multiplayer", "gdx1", "performance", "refactor", "security")
    return "critic_reviewer" if any(word in haystack for word in risky) else None


def _unclear_scope(request: str) -> bool:
    words = [word for word in request.split() if word.strip()]
    haystack = request.lower()
    return len(words) < 2 or any(marker in haystack for marker in ("tbd", "unclear", "unknown scope"))
