"""Feedback record creation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .brief import write_brief
from .capture import _is_png
from .errors import CompanyError
from .paths import rel
from .planner import assign_task, plan_task
from .sessions import end_session, start_session
from .unity import unity_check


def feedback_new(
    root: Path,
    capture_path: Path | None = None,
) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    base = root / "reviews" / day
    base.mkdir(parents=True, exist_ok=True)
    existing = sorted(path for path in base.glob("feedback-*") if path.is_dir())
    number = len(existing) + 1
    folder = base / f"feedback-{number:04d}"
    folder.mkdir()
    if capture_path is not None and not _is_png(capture_path):
        raise CompanyError(
            f"Feedback capture is not a valid PNG: {capture_path}"
        )
    latest_capture = (
        capture_path
        if capture_path is not None
        else _latest_capture(root)
    )
    latest_run = _latest_agent_run(root)
    latest_frame = _latest_frame(root, latest_run)
    latest_action = _latest_action(root, latest_run)
    screenshot_text = latest_capture.relative_to(root).as_posix() if latest_capture else "TBD"
    note = folder / "feedback.md"
    note.write_text(
        "\n".join(
            [
                f"# Feedback {number:04d}",
                "",
                "Scene: TBD",
                f"Screenshot: {screenshot_text}",
                f"Run: {latest_run.relative_to(root).as_posix() if latest_run else 'TBD'}",
                f"Frame: {latest_frame.relative_to(root).as_posix() if latest_frame else 'TBD'}",
                f"Action: {latest_action}",
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
    try:
        write_brief(root)
        text = feedback.read_text(encoding="utf-8", errors="replace")
        profile = _feedback_profile(text)
        tasks = _route_feedback(root, feedback, profile)
        baseline = unity_check(root, [])
        receipt = _write_routing_receipt(root, feedback, profile, tasks, baseline)
        _mark_feedback_routed(root, feedback, receipt, tasks, baseline)
    finally:
        end_session(root)
    return feedback


def _latest_capture(root: Path) -> Path | None:
    captures = sorted(
        (
            path
            for path in (root / "reviews" / "captures").glob("*.png")
            if _is_png(path)
        ),
        key=lambda path: path.stat().st_mtime,
    )
    return captures[-1] if captures else None


def _latest_agent_run(root: Path) -> Path | None:
    runs = sorted(
        (root / "runs").glob("agent-playtest-*"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
    )
    return runs[-1] if runs else None


def _latest_frame(root: Path, run: Path | None) -> Path | None:
    if not run:
        return None
    frames = sorted((run / "observations").glob("frame_*_rgb.png"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return frames[-1] if frames else None


def _latest_action(root: Path, run: Path | None) -> str:
    if not run:
        return "TBD"
    path = run / "actions.jsonl"
    if not path.exists():
        return "TBD"
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    return lines[-1][:240] if lines else "TBD"


def _task_id_from_plan(path: Path) -> str:
    name = path.name
    return name.split("-plan.md", 1)[0]


def _feedback_profile(text: str) -> dict[str, str]:
    observation = _section(text, "Observation")
    requested = _section(text, "Requested Change")
    haystack = f"{observation}\n{requested}".lower()
    summary = _clean_summary(requested) or _clean_summary(observation) or "피드백 상세가 비어 있습니다. 캡처를 기준으로 재현하고 필요한 변경을 구체화하세요."
    if any(term in haystack for term in ("asset", "prop", "3d", "2d", "blender", "mesh", "material", "collider", "에셋", "소품", "프롭", "블렌더", "메시", "머티리얼", "콜라이더")):
        return {"kind": "asset", "agent": "asset_factory", "summary": summary}
    if any(term in haystack for term in ("server", "multiplayer", "netcode", "bot", "join", "sync", "서버", "멀티", "접속", "봇", "동기화")):
        return {"kind": "multiplayer", "agent": "multiplayer_server", "summary": summary}
    if any(
        term in haystack
        for term in (
            "camera",
            "framing",
            "composition",
            "overview",
            "field of view",
        )
    ):
        return {
            "kind": "camera",
            "agent": "unity_gameplay",
            "summary": summary,
        }
    if any(term in haystack for term in ("frame", "fps", "build", "compile", "lag", "performance", "프레임", "성능", "빌드", "컴파일", "렉")):
        return {"kind": "performance", "agent": "performance_build", "summary": summary}
    if any(term in haystack for term in ("ui", "hud", "score", "point", "button", "text", "점수", "포인트", "버튼", "텍스트")):
        return {"kind": "ui", "agent": "unity_gameplay", "summary": summary}
    return {"kind": "gameplay", "agent": "unity_gameplay", "summary": summary}


def _route_feedback(root: Path, feedback: Path, profile: dict[str, str]) -> list[dict[str, str]]:
    feedback_rel = rel(root, feedback)
    summary = profile["summary"]
    routes = [
        ("qa_playtest", f"캡처 피드백 재현 및 영향 범위 기록: {summary} ({feedback_rel})"),
        (profile["agent"], f"피드백 수정 작업 수행: {summary} ({feedback_rel})"),
        ("critic_reviewer", f"피드백 수정 리스크 리뷰: {summary} ({feedback_rel})"),
    ]
    tasks: list[dict[str, str]] = []
    seen_agents: set[str] = set()
    for agent, request in routes:
        if agent in seen_agents:
            continue
        seen_agents.add(agent)
        paths, evidence = _feedback_route_contract(agent)
        plan = plan_task(
            root,
            request,
            preferred_agent=agent,
            allowed_write_paths=paths,
            required_evidence=evidence,
        )
        task_id = _task_id_from_plan(plan)
        work_order = assign_task(root, task_id, agent)
        tasks.append(
            {
                "task_id": task_id,
                "agent": agent,
                "plan": rel(root, plan),
                "work_order": rel(root, work_order),
            }
        )
    return tasks


def _feedback_route_contract(
    agent: str,
) -> tuple[list[str], str]:
    contracts = {
        "qa_playtest": (
            ["reviews", "runs"],
            "reproduction note linked to screenshot or Unity log",
        ),
        "unity_gameplay": (
            [
                "Assets/_Project/Scenes",
                "Assets/_Project/Scripts/Gameplay",
                "Assets/_Project/Scripts/Player",
                "Assets/_Project/Scripts/UI",
                "Assets/_Project/Scripts/Editor",
            ],
            "Unity compile, playtest, and refreshed capture evidence",
        ),
        "asset_factory": (
            [
                "asset_pipeline",
                "Assets/_Project/Art",
                "Assets/_Project/Materials",
                "Assets/_Project/Prefabs",
            ],
            "asset receipt, Unity import evidence, and screenshot",
        ),
        "multiplayer_server": (
            ["Assets/_Project/Scripts/Multiplayer", "scripts", "runs"],
            "server test or architecture evidence",
        ),
        "performance_build": (
            ["tools", "scripts", "runs"],
            "compile, build, or performance evidence",
        ),
        "critic_reviewer": (
            ["reviews", "docs"],
            "findings-first review linked to implementation evidence",
        ),
    }
    return contracts.get(
        agent,
        (
            ["reviews", "docs"],
            "changed files and explicit verification evidence",
        ),
    )


def _write_routing_receipt(root: Path, feedback: Path, profile: dict[str, str], tasks: list[dict[str, str]], baseline: Path) -> Path:
    receipt = feedback.parent / "routing_receipt.md"
    receipt.write_text(
        "\n".join(
            [
                "# Feedback Routing Receipt",
                "",
                f"Feedback: {rel(root, feedback)}",
                f"Kind: {profile['kind']}",
                f"Summary: {profile['summary']}",
                f"Baseline evidence: {rel(root, baseline)}",
                "Status: routed",
                "",
                "## Routed Tasks",
                "",
                *[
                    f"- {task['task_id']} -> {task['agent']} | plan: {task['plan']} | work order: {task['work_order']}"
                    for task in tasks
                ],
                "",
                "## Next Action",
                "",
                "- Run the assigned implementation agent, then review and verify with Unity evidence.",
                "- Do not mark these tasks complete until changed files or explicit report evidence exists.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return receipt


def _mark_feedback_routed(root: Path, path: Path, receipt: Path, tasks: list[dict[str, str]], baseline: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("Status: open", "Status: routed")
    text += "\n## Routing Receipt\n\n"
    text += f"- {rel(root, receipt)}\n"
    text += f"- Baseline evidence: {rel(root, baseline)}\n"
    text += "\n## Routed Tasks\n\n"
    for task in tasks:
        text += f"- {task['task_id']} -> {task['agent']} ({task['work_order']})\n"
    path.write_text(text, encoding="utf-8")


def _section(text: str, title: str) -> str:
    marker = f"## {title}"
    if marker not in text:
        return ""
    tail = text.split(marker, 1)[1]
    if "\n## " in tail:
        tail = tail.split("\n## ", 1)[0]
    return tail.strip()


def _clean_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = " ".join(line for line in lines if line.upper() != "TBD").strip()
    return cleaned[:240]
