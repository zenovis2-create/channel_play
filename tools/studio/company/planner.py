"""Rule-based task planning and assignment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .brain import project_brain_excerpt, standards_for_task
from .errors import CompanyError
from .locks import assert_no_conflict
from .sessions import active_session_dir
from .state import CompanyPaths, load_task_board, read_json, save_task_board
from .tasks import find_task, next_task_id, update_task
from .timeutil import now_iso


ROUTES: list[tuple[tuple[str, ...], str, list[str], str]] = [
    (("plan", "planning", "roadmap", "milestone", "dependency", "sequence", "scope", "breakdown", "작업 설계", "계획", "수립", "로드맵", "마일스톤", "의존성", "순서", "구조화"), "production_planner", ["memory/company", "memory/sessions", "docs"], "production plan with dependency map and evidence checklist"),
    (("research", "source", "citation", "notebooklm", "notebook", "nlm", "benchmark", "latest", "docs search", "리서치", "조사", "자료", "근거", "출처", "인용", "노트북lm", "노트북", "최신", "벤치마크"), "research_librarian", ["docs/research", "memory/company", "memory/sessions", "obsidian/channel_play"], "NotebookLM/Maru cited research brief"),
    (("toolchain", "adapter", "docker", "host-runner", "host runner", "codex sdk", "hermes", "agy", "openclaw", "obsidian", "blender pipeline", "툴체인", "어댑터", "도커", "호스트러너", "호스트 러너", "연동", "연결", "워크스테이션"), "toolchain_integrator", ["tools", "scripts", "docker", "docs", "memory/company"], "adapter/runtime integration receipt"),
    (("code", "coding", "refactor", "api", "python", "javascript", "typescript", "c#", "csharp", "코딩", "코드", "리팩토링", "파이썬", "자바스크립트", "타입스크립트"), "coding_specialist", ["tools", "Assets/_Project/Scripts", "docs"], "code diff with tests or runtime evidence"),
    (("obs", "broadcast", "operator flow", "operator screen", "pilot", "show-control", "stream", "capture", "운영자 화면", "운영 흐름", "방송", "방송용", "파일럿", "촬영", "캡처", "쇼", "진행자"), "operator_broadcast_designer", ["docs", "obsidian/channel_play", "memory/company"], "operator flow and OBS capture checklist"),
    (("movement", "mission", "item", "operator", "ui", "player", "gameplay", "mvp", "game", "unity", "게임", "구현", "플레이어", "이동", "미션", "아이템", "운영자", "포인트", "상점"), "unity_gameplay", ["Assets/_Project/Scripts/Gameplay"], "Unity compile or playtest evidence"),
    (("architecture", "scriptableobject", "scene structure", "prefab", "구조", "아키텍처", "스크립터블", "프리팹", "씬"), "unity_architect", ["Assets/_Project/Scripts"], "Unity compile evidence"),
    (("server", "netcode", "multiplayer", "bot", "서버", "멀티", "접속", "봇", "동기화"), "multiplayer_server", ["Assets/_Project/Scripts"], "server or design evidence"),
    (("blender", "mesh", "pivot", "collider", "material", "블렌더", "메시", "콜라이더", "머티리얼"), "technical_artist_blender", ["asset_pipeline/blender_work"], "Blender cleanup report"),
    (("2d", "3d", "asset", "prop", "generation", "에셋", "소품", "프롭", "생성"), "asset_factory", ["asset_pipeline"], "asset metadata and preview/import note"),
    (("sound", "sfx", "music", "audio", "사운드", "효과음", "음악", "오디오"), "sound_designer", ["obsidian/channel_play/04_Sound"], "sound brief"),
    (("bug", "screenshot", "feedback", "reproduce", "버그", "스크린샷", "피드백", "재현"), "qa_playtest", ["reviews"], "reproduction note"),
    (("build", "compile", "performance", "frame", "빌드", "컴파일", "성능", "프레임", "최적화"), "performance_build", ["runs", "tools"], "build or performance log"),
    (("gdx1", "soak", "worker", "소크", "워커"), "gdx_ops", ["runs", "logs"], "gdx probe or run log"),
    (("docs", "memory", "decision", "session", "문서", "기억", "결정", "세션"), "librarian", ["docs", "memory/company", "obsidian/channel_play"], "doc diff"),
    (("review", "risk", "critique", "리뷰", "위험", "검토"), "critic_reviewer", ["reviews"], "review note"),
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
    text = _work_order_text(root, task, agent_id)
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
                "## Project Brain Excerpt",
                "",
                project_brain_excerpt(root),
                "",
                "## Standards Excerpts",
                "",
                *_format_standards(standards_for_task(root, task)),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _work_order_text(root: Path, task: dict[str, Any], agent_id: str) -> str:
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
            "",
            "## Project Brain Excerpt",
            "",
            project_brain_excerpt(root),
            "",
            "## Standards Excerpts",
            "",
            *_format_standards(standards_for_task(root, task)),
            "",
            "Handoff target: chief_orchestrator",
            "Timeout: current session",
            "",
        ]
    )


def _format_standards(standards: list[dict[str, str]]) -> list[str]:
    if not standards:
        return ["- none"]
    lines: list[str] = []
    for standard in standards:
        lines.extend(
            [
                f"### {standard['title']}",
                "",
                f"Path: {standard['path']}",
                "",
                standard["excerpt"],
                "",
            ]
        )
    return lines


def _reviewer_for(request: str) -> str | None:
    haystack = request.lower()
    risky = ("architecture", "server", "multiplayer", "gdx1", "performance", "refactor", "security")
    return "critic_reviewer" if any(word in haystack for word in risky) else None


def _unclear_scope(request: str) -> bool:
    words = [word for word in request.split() if word.strip()]
    haystack = request.lower()
    return len(words) < 2 or any(marker in haystack for marker in ("tbd", "unclear", "unknown scope"))
