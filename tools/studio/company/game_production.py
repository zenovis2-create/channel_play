"""Game production status and checks for Channel Play."""

from __future__ import annotations

import json
from pathlib import Path

from .capture import _is_png, capture_screen
from .gdx import gdx_probe
from .paths import rel
from .timeutil import now_iso, slugify
from .unity import unity_build, unity_check, unity_playtest
from tools.studio.jobs import list_jobs


def game_production_state(root: Path) -> dict:
    unity_compile = _latest_run_matching(root, "unity-check-", "unity_check.md", ("Compile errors: 0", "Exit code: 0"))
    unity_play = _latest_run(root, "unity-playtest-", "unity_playtest.md")
    development_build = _latest_development_build(root)
    linux_server_build = _latest_run(root, "unity-build-linux-server-", "unity_build.md")
    gdx = _latest_gdx_probe(root)
    gdx_server = _latest_gdx_action(root, "run-server")
    gdx_bots = _latest_gdx_action(root, "run-bots")
    capture = _latest_capture(root)
    feedback = _latest_feedback(root)
    feedback_loop = _latest_run(root, "game-feedback-loop-", "game_feedback_loop.md")
    server_handoff = _latest_run(root, "game-server-handoff-", "server_handoff.md")
    assets = _asset_pipeline_state(root)
    task_flow = _task_flow_state(root)
    jobs = list_jobs(root, limit=10)
    scenes = sorted((root / "Assets" / "_Project" / "Scenes").glob("*.unity"))
    gameplay_scripts = sorted((root / "Assets" / "_Project" / "Scripts" / "Gameplay").glob("*.cs"))
    player_scripts = sorted((root / "Assets" / "_Project" / "Scripts" / "Player").glob("*.cs"))
    prefabs = sorted((root / "Assets" / "_Project" / "Prefabs").glob("*.prefab"))
    mvp_spec = root / "Assets" / "_Project" / "Scripts" / "Gameplay" / "TraitorEscapeMvpSpec.md"

    checks = [
        _check("Unity compile", _status_passed(unity_compile, ("Compile errors: 0", "Exit code: 0")), unity_compile.get("path", "")),
        _check("Playtest smoke", _status_passed(unity_play, ("Playtest smoke: passed", "Exit code: 0")), unity_play.get("path", "")),
        _check("Development build", _status_passed(development_build, ("Build status: passed", "Build output exists: True")), development_build.get("path", "")),
        _check(
            "gdx1 probe evidence",
            _gdx_probe_recorded(gdx),
            gdx.get("path", ""),
        ),
        _check("Capture evidence", bool(capture), capture.get("path", "")),
        _check("MVP spec", mvp_spec.exists(), rel(root, mvp_spec) if mvp_spec.exists() else ""),
    ]
    passed = sum(1 for check in checks if check["passed"])

    optimization_loops = _optimization_loops(feedback_loop, capture, feedback, assets, linux_server_build, server_handoff, task_flow, jobs)
    next_best_action = _next_best_action(passed, len(checks), optimization_loops, feedback, server_handoff, task_flow)
    perfection_gate = _perfection_gate(checks, optimization_loops, next_best_action, server_handoff, jobs)
    return {
        "updatedAt": now_iso(),
        "readiness": {
            "passed": passed,
            "total": len(checks),
            "status": "ready" if passed == len(checks) else "needs_work",
        },
        "checks": checks,
        "unity": {
            "compile": unity_compile,
            "playtest": unity_play,
            "build": development_build,
            "linuxServerBuild": linux_server_build,
            "scenes": len(scenes),
            "gameplayScripts": len(gameplay_scripts),
            "playerScripts": len(player_scripts),
            "prefabs": len(prefabs),
        },
        "gdx": gdx,
        "remote": {
            "linuxServerBuild": linux_server_build,
            "server": gdx_server,
            "bots": gdx_bots,
            "status": "ready" if _status_passed(gdx_server, ("Status: ok",)) and _status_passed(gdx_bots, ("Status: ok",)) else "server_blocked",
        },
        "capture": capture,
        "optimizationLoops": optimization_loops,
        "nextBestAction": next_best_action,
        "perfectionGate": perfection_gate,
        "taskFlow": task_flow,
        "mvp": {
            "spec": rel(root, mvp_spec) if mvp_spec.exists() else "",
            "scene": "Assets/_Project/Scenes/School_MVP.unity",
            "runtime": "Assets/_Project/Scripts/Gameplay/TraitorEscapeMvpSession.cs",
        },
    }


def render_game_production_status(root: Path) -> str:
    state = game_production_state(root)
    readiness = state["readiness"]
    lines = [
        "Game Production Cockpit",
        f"Updated: {state['updatedAt']}",
            f"Readiness: {readiness['passed']}/{readiness['total']} ({readiness['status']})",
            f"Perfection gate: {state['perfectionGate']['passed']}/{state['perfectionGate']['total']} ({state['perfectionGate']['status']})",
            f"Answer: {state['perfectionGate']['answer']}",
            "",
            "Checks:",
    ]
    for check in state["checks"]:
        lines.append(f"  {check['label']:<18} {'passed' if check['passed'] else 'pending':<8} {check['path'] or '-'}")
    lines.extend(
        [
            "",
            f"Scenes: {state['unity']['scenes']}",
            f"Gameplay scripts: {state['unity']['gameplayScripts']}",
            f"Player scripts: {state['unity']['playerScripts']}",
            f"Prefabs: {state['unity']['prefabs']}",
            "",
            f"gdx server: {state['remote']['server'].get('summary', 'not run')} {state['remote']['server'].get('path', '')}",
            f"gdx bots: {state['remote']['bots'].get('summary', 'not run')} {state['remote']['bots'].get('path', '')}",
            f"Linux server build: {state['remote']['linuxServerBuild'].get('summary', 'not run')} {state['remote']['linuxServerBuild'].get('path', '')}",
            "",
            "Next best action:",
            f"  {state['nextBestAction'].get('label', 'none')} -> {state['nextBestAction'].get('command', 'none')}",
            f"  {state['nextBestAction'].get('reason', '')}",
            "",
            "Optimization loops:",
        ]
    )
    for loop in state["optimizationLoops"]:
        lines.append(f"  {loop['label']:<24} {loop['status']:<16} {loop.get('evidence') or loop.get('nextAction')}")
    lines.extend(["", "Perfection gate checks:"])
    for check in state["perfectionGate"]["checks"]:
        lines.append(f"  {check['label']:<28} {'passed' if check['passed'] else 'pending':<8} {check.get('detail', '')}")
    return "\n".join(lines)


def game_production_check(root: Path, args: list[str]) -> Path:
    run_dir = root / "runs" / f"game-production-check-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "game_production_check.md"
    include_capture = "--capture" in args
    include_build = "--build" in args

    compile_path = unity_check(root, ["--batch"])
    playtest_path = unity_playtest(root, [])
    build_path = unity_build(root, []) if include_build else None
    gdx_path = gdx_probe(root)
    capture_path = capture_screen(root) if include_capture else None
    state = game_production_state(root)

    lines = [
        "# Game Production Check",
        "",
        f"Checked: {now_iso()}",
        f"Readiness: {state['readiness']['passed']}/{state['readiness']['total']} ({state['readiness']['status']})",
        "",
        "## Artifacts",
        "",
        f"- Unity compile: {rel(root, compile_path)}",
        f"- Unity playtest smoke: {rel(root, playtest_path)}",
        f"- Development build: {rel(root, build_path) if build_path else 'skipped; use --build or unity build'}",
        f"- gdx1 probe: {rel(root, gdx_path)}",
    ]
    if capture_path:
        lines.append(f"- Capture: {rel(root, capture_path)}")
    lines.extend(["", "## Checks", ""])
    for check in state["checks"]:
        lines.append(f"- [{'x' if check['passed'] else ' '}] {check['label']}: {check['path'] or 'missing'}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _latest_run(root: Path, prefix: str, filename: str) -> dict:
    runs = sorted((root / "runs").glob(f"{prefix}*"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    for run in runs:
        path = run / filename
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            return {
                "path": rel(root, path),
                "run": rel(root, run),
                "summary": _first_status_line(text),
                "text": text[:4000],
            }
    return {}


def _latest_run_matching(root: Path, prefix: str, filename: str, markers: tuple[str, ...]) -> dict:
    fallback = {}
    runs = sorted((root / "runs").glob(f"{prefix}*"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    for run in runs:
        path = run / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        row = {
            "path": rel(root, path),
            "run": rel(root, run),
            "summary": _first_status_line(text),
            "text": text[:4000],
        }
        if not fallback:
            fallback = row
        if all(marker in text for marker in markers):
            return row
    return fallback


def _latest_development_build(root: Path) -> dict:
    candidates = [
        _latest_run_matching(
            root,
            prefix,
            "unity_build.md",
            ("Build status: passed", "Build output exists: True"),
        )
        for prefix in (
            "unity-build-windows-dev-",
            "unity-build-mac-dev-",
        )
    ]
    existing = [
        candidate
        for candidate in candidates
        if candidate.get("path")
        and (root / candidate["path"]).is_file()
    ]
    if not existing:
        return {}
    return max(
        existing,
        key=lambda candidate: (root / candidate["path"]).stat().st_mtime,
    )


def _latest_gdx_probe(root: Path) -> dict:
    runs = sorted((root / "runs").glob("gdx-probe-*"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    for run in runs:
        files = sorted(run.glob("gdx_*.md"))
        if files:
            path = files[0]
            text = path.read_text(encoding="utf-8", errors="replace")
            return {
                "path": rel(root, path),
                "run": rel(root, run),
                "summary": _first_status_line(text),
                "text": text[:4000],
            }
    return {}


def _latest_gdx_action(root: Path, action: str) -> dict:
    runs = sorted((root / "runs").glob(f"gdx-{action}-*"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    for run in runs:
        path = run / f"gdx_{action}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            return {
                "path": rel(root, path),
                "run": rel(root, run),
                "summary": _first_status_line(text),
                "text": text[:4000],
            }
    return {}


def _latest_capture(root: Path) -> dict:
    captures = sorted(
        (
            item
            for item in (root / "reviews" / "captures").glob("*.png")
            if _is_png(item)
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not captures:
        return {}
    capture = captures[0]
    return {"path": rel(root, capture), "summary": capture.name}


def _latest_feedback(root: Path) -> dict:
    notes = sorted((root / "reviews").glob("20*/feedback-*/feedback.md"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    for note in notes:
        text = note.read_text(encoding="utf-8", errors="replace")
        return {
            "path": rel(root, note),
            "summary": _first_status_line(text),
            "status": _field(text, "Status") or "open",
            "text": text[:2000],
        }
    return {}


def _asset_pipeline_state(root: Path) -> dict:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        return {"total": 0, "accepted": 0, "unityReady": 0, "latest": {}, "pipelineReady": 0}
    import json

    data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.get("assets", []) if isinstance(data, dict) else []
    latest = sorted(assets, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return {
        "total": len(assets),
        "accepted": sum(1 for item in assets if item.get("status") == "accepted"),
        "unityReady": sum(1 for item in assets if item.get("status") in {"unity_ready", "accepted"}),
        "pipelineReady": sum(1 for item in assets if item.get("pipeline_receipt")),
        "latest": latest[0] if latest else {},
    }


def _optimization_loops(
    feedback_loop: dict,
    capture: dict,
    feedback: dict,
    assets: dict,
    linux_server_build: dict,
    server_handoff: dict,
    task_flow: dict,
    jobs: list[dict],
) -> list[dict]:
    running_jobs = [job for job in jobs if not job.get("isTerminal")]
    latest_job = jobs[0] if jobs else {}
    return [
        {
            "id": "play_feedback",
            "label": "Play → Capture → Feedback",
            "status": "ready" if feedback_loop and feedback else "needs_capture",
            "summary": feedback.get("path") or capture.get("path") or "playtest/capture/feedback receipt 대기",
            "evidence": feedback_loop.get("path") or feedback.get("path") or capture.get("path", ""),
            "nextAction": "game.feedbackLoop 실행 후 feedback.process로 수정 작업 전환",
            "command": "game.feedbackLoop",
        },
        {
            "id": "asset_factory",
            "label": "2D → 3D → Blender → Unity",
            "status": "ready" if assets.get("pipelineReady") else "needs_asset",
            "summary": f"{assets.get('pipelineReady', 0)}/{assets.get('total', 0)} pipeline ready · accepted {assets.get('accepted', 0)}",
            "evidence": assets.get("latest", {}).get("pipeline_receipt", ""),
            "nextAction": "에셋 ID 입력 후 asset.prepare 실행",
            "command": "asset.prepare",
        },
        {
            "id": "server_soak",
            "label": "x86_64 Server Soak",
            "status": "handoff_ready" if server_handoff else "worker_blocked",
            "summary": linux_server_build.get("summary") or "Linux server build 대기",
            "evidence": server_handoff.get("path") or linux_server_build.get("path", ""),
            "nextAction": "x86_64 runner 연결 전까지 handoff receipt 유지",
            "command": "game.serverHandoff",
        },
        {
            "id": "game_work_queue",
            "label": "Game Work Queue",
            "status": "running" if task_flow.get("running") else ("ready" if task_flow.get("open") else "empty"),
            "summary": f"open {task_flow.get('open', 0)} · assigned {task_flow.get('assigned', 0)} · review {task_flow.get('needsReview', 0)}",
            "evidence": task_flow.get("latest", {}).get("work_order", "") or task_flow.get("latest", {}).get("report", ""),
            "nextAction": "할당 작업을 실행/리뷰/검증으로 진행",
            "command": "agent.run",
        },
        {
            "id": "agent_visibility",
            "label": "Agent Progress Visibility",
            "status": "running" if running_jobs else ("ready" if latest_job else "pending"),
            "summary": f"active {len(running_jobs)} · latest {latest_job.get('commandName', 'none')} {latest_job.get('status', '')}".strip(),
            "evidence": latest_job.get("receipt", {}).get("path", ""),
            "nextAction": "작업 추적 카드에서 이벤트, receipt, artifacts 확인",
            "command": "company.brief",
        },
    ]


def _next_best_action(passed: int, total: int, loops: list[dict], feedback: dict, server_handoff: dict, task_flow: dict) -> dict:
    by_id = {loop["id"]: loop for loop in loops}
    if passed < total:
        return {
            "label": "제작 준비도 복구",
            "command": "game.productionCheck",
            "reason": f"검증 체인이 {passed}/{total}입니다. 컴파일, 플레이테스트, 캡처, 빌드 증거를 먼저 갱신해야 합니다.",
            "status": "needs_work",
        }
    play = by_id.get("play_feedback", {})
    if play.get("status") != "ready":
        return {
            "label": "플레이 피드백 루프 생성",
            "command": "game.feedbackLoop",
            "reason": "게임 확인 결과를 캡처와 피드백 파일로 묶어야 에이전트 수정 작업으로 넘길 수 있습니다.",
            "status": "ready",
        }
    if feedback.get("status") == "open" and feedback.get("path"):
        return {
            "label": "피드백을 작업으로 전환",
            "command": "feedback.process",
            "payload": {"path": feedback["path"]},
            "reason": "캡처와 피드백 파일이 준비됐습니다. 이제 QA/구현/리뷰 작업으로 라우팅해야 실제 수정 루프가 시작됩니다.",
            "status": "ready",
        }
    task_action = _task_next_action(task_flow)
    if task_action:
        return task_action
    asset = by_id.get("asset_factory", {})
    if asset.get("status") != "ready":
        return {
            "label": "첫 에셋 파이프라인 준비",
            "command": "asset.prepare",
            "reason": "2D 소스, 3D 생성, Blender 정리, Unity import manifest를 한 패킷으로 만들어야 합니다.",
            "status": "needs_asset",
        }
    server = by_id.get("server_soak", {})
    if server.get("status") == "worker_blocked" and not server_handoff:
        return {
            "label": "서버 소크 핸드오프 유지",
            "command": "game.serverHandoff",
            "reason": "현재 남은 구조적 병목은 x86_64 Linux runner입니다. 연결 전까지 handoff receipt가 기준입니다.",
            "status": "worker_blocked",
        }
    return {
        "label": "에이전트 진행 상황 확인",
        "command": "company.brief",
        "reason": "제작 루프가 준비됐습니다. 작업 원장과 receipt 기준으로 다음 구현 작업을 진행합니다.",
        "status": "ready",
    }


def _task_flow_state(root: Path) -> dict:
    active_session = ""
    state_path = root / "memory" / "company" / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(state, dict):
            active_session = str(state.get("active_session") or "")
    board = root / "memory" / "company" / "task_board.json"
    if not board.exists():
        return {
            "open": 0,
            "assigned": 0,
            "needsReview": 0,
            "needsEvidence": 0,
            "running": 0,
            "activeSession": active_session,
            "latest": {},
        }
    data = json.loads(board.read_text(encoding="utf-8"))
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    open_tasks = [task for task in tasks if task.get("status") not in {"closed", "closed_blocked"}]
    latest = sorted(open_tasks, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return {
        "open": len(open_tasks),
        "assigned": sum(1 for task in open_tasks if task.get("status") == "assigned"),
        "needsReview": sum(1 for task in open_tasks if task.get("status") == "needs_review"),
        "needsEvidence": sum(1 for task in open_tasks if task.get("status") in {"needs_evidence", "evidence_attached"}),
        "running": sum(1 for task in open_tasks if task.get("agent_status") == "running"),
        "activeSession": active_session,
        "latest": latest[0] if latest else {},
    }


def _task_next_action(task_flow: dict) -> dict:
    task = task_flow.get("latest") or {}
    task_id = str(task.get("id") or "")
    if not task_id:
        return {}
    status = str(task.get("status") or "")
    if status == "planned":
        if not task_flow.get("activeSession"):
            return {
                "label": "작업 세션 시작",
                "command": "company.session.start",
                "payload": {
                    "goal": str(task.get("request") or task_id),
                },
                "reason": (
                    f"{task_id}를 할당하기 전에 회사 세션을 시작해야 합니다. "
                    "세션이 작업지시서, 보고서, 검증 증거의 경계를 제공합니다."
                ),
                "status": "ready",
            }
        agent_id = str(task.get("suggested_agent") or "")
        if not agent_id:
            return {}
        return {
            "label": "계획 작업 할당",
            "command": "company.assign",
            "payload": {"taskId": task_id, "agentId": agent_id},
            "reason": (
                f"{task_id} 계획이 준비됐습니다. 제안 역할 {agent_id}에게 "
                "할당해 실행 가능한 작업지시서를 생성합니다."
            ),
            "status": "ready",
        }
    if status == "assigned":
        return {
            "label": "할당 작업 실행",
            "command": "agent.run",
            "payload": {"taskId": task_id},
            "reason": f"{task_id}가 할당됐지만 아직 실행 산출물이 없습니다. 담당 에이전트 실행이 다음 단계입니다.",
            "status": "ready",
        }
    if status == "needs_review":
        return {
            "label": "작업 리뷰 진행",
            "command": "company.review",
            "payload": {"taskId": task_id, "reviewerId": "critic_reviewer"},
            "reason": f"{task_id}는 구현 후 리뷰가 필요합니다. 리뷰 receipt를 먼저 남겨야 합니다.",
            "status": "needs_review",
        }
    if status in {"needs_evidence", "evidence_attached"}:
        return {
            "label": "증거 검증 진행",
            "command": "company.advance",
            "payload": {"taskId": task_id},
            "reason": f"{task_id}는 증거/검증 단계입니다. 자동 진행으로 검증과 종료 조건을 확인합니다.",
            "status": "needs_evidence",
        }
    return {}


def _perfection_gate(checks: list[dict], loops: list[dict], next_action: dict, server_handoff: dict, jobs: list[dict]) -> dict:
    loop_by_id = {loop.get("id"): loop for loop in loops}
    next_command = str(next_action.get("command") or "")
    next_payload = next_action.get("payload") if isinstance(next_action.get("payload"), dict) else {}
    gate_checks = [
        _gate_check(
            "Core readiness",
            all(check.get("passed") for check in checks),
            "Unity/playtest/build/gdx probe evidence/capture/spec",
        ),
        _gate_check("Feedback loop", loop_by_id.get("play_feedback", {}).get("status") == "ready", loop_by_id.get("play_feedback", {}).get("evidence", "")),
        _gate_check("Asset pipeline loop", loop_by_id.get("asset_factory", {}).get("status") == "ready", loop_by_id.get("asset_factory", {}).get("summary", "")),
        _gate_check(
            "Server dependency isolated",
            loop_by_id.get("server_soak", {}).get("status") == "handoff_ready" and bool(server_handoff),
            loop_by_id.get("server_soak", {}).get("evidence", ""),
        ),
        _gate_check(
            "Work queue actionable",
            _next_action_is_actionable(next_command, next_payload),
            f"{next_command} {json.dumps(next_payload, ensure_ascii=False) if next_payload else ''}".strip(),
        ),
        _gate_check("Job ledger healthy", bool(jobs), jobs[0].get("receipt", {}).get("path", "") if jobs else "no jobs"),
    ]
    passed = sum(1 for check in gate_checks if check["passed"])
    total = len(gate_checks)
    status = "perfect" if passed == total else "needs_work"
    return {
        "passed": passed,
        "total": total,
        "status": status,
        "answer": "완벽합니다" if status == "perfect" else "아직 완벽하지 않습니다",
        "scope": "current workstation and Studio workflow, excluding missing external x86_64 runner hardware",
        "checks": gate_checks,
    }


def _next_action_is_actionable(command: str, payload: dict) -> bool:
    if not command:
        return False
    if command == "company.session.start":
        return bool(payload.get("goal"))
    if command == "company.assign":
        return bool(payload.get("taskId")) and bool(payload.get("agentId"))
    if command in {"agent.run", "agent.review", "company.review", "company.verify", "company.advance"}:
        return bool(payload.get("taskId"))
    if command == "feedback.process":
        return bool(payload.get("path"))
    if command == "asset.prepare":
        return False
    return True


def _gate_check(label: str, passed: bool, detail: str) -> dict:
    return {"label": label, "passed": bool(passed), "detail": detail}


def _status_passed(run: dict, markers: tuple[str, ...]) -> bool:
    text = run.get("text", "")
    return bool(text) and all(marker in text for marker in markers)


def _status_any(run: dict, markers: tuple[str, ...]) -> bool:
    text = run.get("text", "")
    return bool(text) and any(marker in text for marker in markers)


def _gdx_probe_recorded(run: dict) -> bool:
    text = run.get("text", "")
    return bool(text) and (
        all(
            marker in text
            for marker in ("# gdx1 Probe", "SSH exit:", "## Result")
        )
        or any(marker in text for marker in ("usable", "Status: ok"))
    )


def _check(label: str, passed: bool, path: str) -> dict:
    return {"label": label, "passed": passed, "path": path}


def _first_status_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    for prefix in ("Playtest smoke:", "Build status:", "Status:", "Result:", "Compile errors:", "Exit code:"):
        for line in lines:
            if line.startswith(prefix):
                return line
    if "usable" in lines:
        return "usable"
    return "recorded"


def _field(text: str, name: str) -> str:
    prefix = f"{name}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""
