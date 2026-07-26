"""Project brain and standards registry helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .state import CompanyPaths, read_json, read_text
from .timeutil import now_iso

MAX_EXCERPT_CHARS = 1800

STANDARD_DEFINITIONS: dict[str, dict[str, str]] = {
    "unity_scripts": {
        "title": "Unity Scripts Standard",
        "body": """# Unity Scripts Standard

- Keep gameplay scripts under the task's allowed Unity script folder.
- Prefer small MonoBehaviour boundaries with explicit serialized fields.
- Do not introduce broad Unity package churn without a separate task.
- Every script change needs compile or playtest evidence.
""",
    },
    "unity_scene_prefab_ownership": {
        "title": "Unity Scene And Prefab Ownership Standard",
        "body": """# Unity Scene And Prefab Ownership Standard

- One active owner per scene, prefab folder, or script system.
- Do not edit unrelated scenes or prefabs while implementing script-only tasks.
- Record ownership assumptions in the work order when touching Unity assets.
""",
    },
    "evidence": {
        "title": "Evidence Standard",
        "body": """# Evidence Standard

- No task is complete without a report, receipt, screenshot, compile log, or playtest note.
- Job receipts and review checkpoints can count as MVP evidence when they name the task.
- Verification must record what was accepted and what remains risky.
""",
    },
    "asset_import": {
        "title": "Asset Import Standard",
        "body": """# Asset Import Standard

- Track source, license, import path, preview, and acceptance status for every asset.
- Keep Blender/2D-to-3D outputs in the asset pipeline until accepted.
- Imported assets need a short readability and scale check.
""",
    },
    "gdx_worker": {
        "title": "GDX Worker Standard",
        "body": """# GDX Worker Standard

- Treat gdx1 as an optional worker until SSH health is confirmed.
- Remote sync, server runs, bots, and log collection must leave run receipts.
- Do not assume gdx1 availability when planning critical local work.
""",
    },
}


def ensure_brain_files(root: Path) -> dict[str, Any]:
    paths = CompanyPaths(root)
    memory = paths.memory_dir
    memory.mkdir(parents=True, exist_ok=True)
    project_brain = memory / "project_brain.md"
    user_profile = memory / "user_profile.md"
    agent_memory = memory / "agent_memory"
    standards_dir = memory / "standards"
    agent_memory.mkdir(parents=True, exist_ok=True)
    standards_dir.mkdir(parents=True, exist_ok=True)

    if not project_brain.exists():
        project_brain.write_text(_default_project_brain(root), encoding="utf-8")
    if not user_profile.exists():
        user_profile.write_text(_default_user_profile(), encoding="utf-8")
    for name, definition in STANDARD_DEFINITIONS.items():
        path = standards_dir / f"{name}.md"
        if not path.exists():
            path.write_text(definition["body"], encoding="utf-8")

    standards = []
    for path in sorted(standards_dir.glob("*.md")):
        standards.append(
            {
                "id": path.stem,
                "title": _title_for(path),
                "path": path.relative_to(root).as_posix(),
                "excerpt": _excerpt(read_text(path), 420),
            }
        )

    return {
        "projectBrainPath": project_brain.relative_to(root).as_posix(),
        "userProfilePath": user_profile.relative_to(root).as_posix(),
        "agentMemoryPath": agent_memory.relative_to(root).as_posix(),
        "standardsPath": standards_dir.relative_to(root).as_posix(),
        "projectBrain": read_text(project_brain),
        "userProfile": read_text(user_profile),
        "standards": standards,
    }


def project_brain_excerpt(root: Path, limit: int = MAX_EXCERPT_CHARS) -> str:
    snapshot = ensure_brain_files(root)
    return _excerpt(snapshot["projectBrain"], limit)


def standards_for_task(root: Path, task: dict[str, Any], limit: int = 900) -> list[dict[str, str]]:
    ensure_brain_files(root)
    ids = _standard_ids_for_task(task)
    rows = []
    for standard_id in ids:
        path = CompanyPaths(root).memory_dir / "standards" / f"{standard_id}.md"
        if not path.exists():
            continue
        text = read_text(path)
        rows.append(
            {
                "id": standard_id,
                "title": _title_for(path),
                "path": path.relative_to(root).as_posix(),
                "excerpt": _excerpt(text, limit),
            }
        )
    return rows


def render_brain_status(root: Path) -> str:
    snapshot = ensure_brain_files(root)
    return "\n".join(
        [
            "Project Brain",
            f"  brain       {snapshot['projectBrainPath']}",
            f"  profile     {snapshot['userProfilePath']}",
            f"  agent mem   {snapshot['agentMemoryPath']}",
            f"  standards   {len(snapshot['standards'])} files",
        ]
    )


def _standard_ids_for_task(task: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(task.get("request") or ""),
            " ".join(str(path) for path in task.get("allowed_write_paths") or []),
            str(task.get("required_evidence") or ""),
            str(task.get("suggested_agent") or task.get("assigned_agent") or ""),
        ]
    ).lower()
    ids = ["evidence"]
    if any(term in text for term in ("unity", "assets/_project/scripts", "gameplay", "player", "ui", "compile", "playtest")):
        ids.extend(["unity_scripts", "unity_scene_prefab_ownership"])
    if any(term in text for term in ("asset", "blender", "2d", "3d", "prop", "preview", "import")):
        ids.append("asset_import")
    if any(term in text for term in ("gdx", "worker", "server", "bot", "soak")):
        ids.append("gdx_worker")
    return _dedupe(ids)


def _default_project_brain(root: Path) -> str:
    state_path = CompanyPaths(root).state_json
    state = read_json(state_path) if state_path.exists() else {}
    goal = state.get("integrated_goal") if isinstance(state.get("integrated_goal"), dict) else {}
    title = goal.get("ko_title") or goal.get("title") or "Channel Play"
    scope = goal.get("mvp_scope") if isinstance(goal.get("mvp_scope"), list) else []
    return "\n".join(
        [
            "# Project Brain",
            "",
            f"Generated: {now_iso()}",
            "",
            "## Current Goal",
            "",
            str(title),
            "",
            "## MVP Scope",
            "",
            *(f"- {item}" for item in scope[:8]),
            *([] if scope else ["- Unity MVP gameplay loop with visible agent workflow evidence."]),
            "",
            "## Style",
            "",
            "- Korean-first planning and status language.",
            "- Quiet production UI, visible evidence, no hidden automation.",
            "- Every agent output should name the task, changed files, evidence, and next risk.",
            "",
            "## Constraints",
            "",
            "- Studio owns orchestration state; external AI tools are adapters.",
            "- gdx1 is optional until health is verified.",
            "- Unity work needs compile, playtest, screenshot, or receipt evidence.",
            "",
            "## Forbidden Actions",
            "",
            "- Do not mark done without evidence or receipt.",
            "- Do not edit broad unrelated Unity folders.",
            "- Do not re-enable Claude as a default adapter unless the user requests it.",
            "- Do not use non-loopback Studio execution APIs without an explicit trusted-network setting.",
            "",
        ]
    )


def _default_user_profile() -> str:
    return "\n".join(
        [
            "# User Profile",
            "",
            "- Prefers Korean status and concise evidence-backed implementation reports.",
            "- Wants visible progress, artifacts, next action, and blocked reasons in the Studio UI.",
            "- Does not want optimistic completion claims without runtime validation.",
            "",
        ]
    )


def _title_for(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return path.stem.replace("_", " ").title()


def _excerpt(text: str, limit: int) -> str:
    clean = text.strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "\n\n[truncated]"


def _dedupe(values: list[str]) -> list[str]:
    rows: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        rows.append(value)
    return rows
