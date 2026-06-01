"""External AI agent adapter runner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .errors import CompanyError
from .paths import find_repo_root, rel
from .state import CompanyPaths, read_json, read_text, write_json
from .tasks import find_task, update_task
from .timeutil import now_iso, slugify

DEFAULT_ADAPTERS: dict[str, Any] = {
    "version": 1,
    "default_tool": "codex",
    "review_tool": "claude",
    "default_timeout_seconds": 900,
    "role_defaults": {
        "chief_orchestrator": "codex",
        "game_director": "claude",
        "unity_architect": "codex",
        "unity_gameplay": "codex",
        "multiplayer_server": "codex",
        "asset_factory": "hermes",
        "technical_artist_blender": "agy",
        "sound_designer": "hermes",
        "qa_playtest": "agy",
        "performance_build": "codex",
        "gdx_ops": "openclaw",
        "librarian": "hermes",
        "critic_reviewer": "claude",
    },
    "tools": {
        "codex": {
            "enabled": True,
            "description": "Codex CLI non-interactive coding worker",
            "argv": ["codex", "exec", "--cd", "{root}", "--sandbox", "workspace-write", "-"],
            "stdin": "{prompt}",
            "timeout_seconds": 1800,
        },
        "claude": {
            "enabled": True,
            "description": "Claude Code non-interactive reviewer or worker",
            "argv": ["claude", "--print", "--add-dir", "{root}", "{prompt}"],
            "timeout_seconds": 1800,
        },
        "agy": {
            "enabled": True,
            "description": "Antigravity CLI browser/UI worker",
            "argv": ["agy", "--print", "--print-timeout", "10m", "{prompt}"],
            "timeout_seconds": 900,
        },
        "hermes": {
            "enabled": True,
            "description": "Hermes one-shot research and support worker",
            "argv": ["hermes", "-z", "{prompt}"],
            "timeout_seconds": 900,
        },
        "openclaw": {
            "enabled": True,
            "description": "OpenClaw local gateway agent turn",
            "argv": [
                "openclaw",
                "agent",
                "--local",
                "--json",
                "--session-key",
                "agent:{agent_id}:{task_id}",
                "--message",
                "{prompt}",
            ],
            "timeout_seconds": 900,
        },
    },
}


def main(argv: list[str] | None = None) -> int:
    args = list(argv or [])
    root = find_repo_root()
    try:
        if not args or args[0] in {"help", "-h", "--help"}:
            return _help()
        command = args[0]
        if command in {"adapters", "check"}:
            print(render_adapters(root))
            return 0
        if command in {"run", "review"}:
            parsed = _parse_run_args(args[1:])
            path = run_agent_task(
                root,
                parsed["task_id"],
                tool_name=parsed["tool"],
                mode=command,
                dry_run=parsed["dry_run"],
                extra_prompt=parsed["message"],
            )
            print(path.relative_to(root))
            return 0
        print(f"Unknown agent command: {command}", file=os.sys.stderr)
        return 2
    except CompanyError as exc:
        print(f"agent error: {exc}", file=os.sys.stderr)
        return 1


def ensure_tool_adapters(root: Path) -> dict[str, Any]:
    path = CompanyPaths(root).tool_adapters_json
    if not path.exists():
        write_json(path, DEFAULT_ADAPTERS)
        return json.loads(json.dumps(DEFAULT_ADAPTERS))
    data = read_json(path)
    _validate_adapters(data)
    return data


def collect_agent_adapter_state(root: Path) -> dict[str, Any]:
    config = ensure_tool_adapters(root)
    tools = {}
    for name, adapter in sorted(config.get("tools", {}).items()):
        executable = str(adapter.get("argv", [""])[0])
        tools[name] = {
            "enabled": bool(adapter.get("enabled", True)),
            "available": shutil.which(executable) is not None,
            "executable": executable,
            "description": str(adapter.get("description", "")),
        }
    return {
        "defaultTool": config.get("default_tool"),
        "reviewTool": config.get("review_tool"),
        "tools": tools,
        "config": rel(root, CompanyPaths(root).tool_adapters_json),
    }


def render_adapters(root: Path) -> str:
    state = collect_agent_adapter_state(root)
    lines = [
        f"Config        {state['config']}",
        f"Default tool  {state.get('defaultTool')}",
        f"Review tool   {state.get('reviewTool')}",
        "",
        "Tools:",
    ]
    for name, tool in state["tools"].items():
        enabled = "enabled" if tool["enabled"] else "disabled"
        available = "available" if tool["available"] else "missing"
        lines.append(f"  {name:<10} {enabled:<8} {available:<9} {tool['executable']}")
    return "\n".join(lines)


def run_agent_task(
    root: Path,
    task_id: str,
    *,
    tool_name: str = "",
    mode: str = "run",
    dry_run: bool = False,
    extra_prompt: str = "",
) -> Path:
    if mode not in {"run", "review"}:
        raise CompanyError(f"Invalid agent mode: {mode}")

    config = ensure_tool_adapters(root)
    task = find_task(root, task_id)
    agent_id = _task_agent(task, mode)
    tool = _select_tool(config, agent_id, mode, tool_name)
    adapter = _adapter(config, tool)

    run_dir = root / "runs" / f"agent-{tool}-{task_id}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=False)
    prompt = _build_prompt(root, task, agent_id, tool, mode, extra_prompt)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    context = {
        "root": str(root),
        "task_id": task_id,
        "agent_id": agent_id,
        "tool": tool,
        "mode": mode,
        "prompt": prompt,
        "run_dir": str(run_dir),
        "work_order": str(root / str(task.get("work_order") or "")),
    }
    command = [_render_arg(str(arg), context) for arg in adapter.get("argv", [])]
    stdin_template = adapter.get("stdin")
    stdin = _render_arg(str(stdin_template), context) if stdin_template else None
    timeout = int(adapter.get("timeout_seconds") or config.get("default_timeout_seconds") or 900)

    result = _execute(command, root, stdin, timeout, dry_run)
    (run_dir / "command.json").write_text(
        json.dumps({"command": command, "dry_run": dry_run, "timeout_seconds": timeout}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "stdout.txt").write_text(result["stdout"], encoding="utf-8")
    (run_dir / "stderr.txt").write_text(result["stderr"], encoding="utf-8")
    report = _write_run_report(root, run_dir, task, agent_id, tool, mode, result)
    _update_task_after_run(root, task, tool, mode, result, report)
    return run_dir / "agent_run.md"


def _execute(command: list[str], root: Path, stdin: str | None, timeout: int, dry_run: bool) -> dict[str, Any]:
    if not command:
        raise CompanyError("Adapter argv is empty.")
    executable = command[0]
    available = shutil.which(executable) is not None
    if dry_run:
        return {
            "status": "dry_run",
            "exit": 0,
            "stdout": "Dry run only. Agent command was not executed.\n",
            "stderr": "" if available else f"Executable not found: {executable}\n",
        }
    if not available:
        return {
            "status": "blocked",
            "exit": 127,
            "stdout": "",
            "stderr": f"Executable not found: {executable}\n",
        }

    env = os.environ.copy()
    env["CHANNEL_PLAY_ROOT"] = str(root)
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "exit": 124,
            "stdout": _coerce_output(exc.stdout),
            "stderr": _coerce_output(exc.stderr) + f"\nTimed out after {timeout}s.\n",
        }
    status = "ok" if completed.returncode == 0 else "failed"
    return {
        "status": status,
        "exit": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _write_run_report(
    root: Path,
    run_dir: Path,
    task: dict[str, Any],
    agent_id: str,
    tool: str,
    mode: str,
    result: dict[str, Any],
) -> Path:
    lines = [
        "# Agent Run",
        "",
        f"Task ID: {task['id']}",
        f"Role: {agent_id}",
        f"Tool: {tool}",
        f"Mode: {mode}",
        f"Status: {result['status']}",
        f"Exit: {result['exit']}",
        f"Created: {now_iso()}",
        "",
        "## Task",
        "",
        str(task.get("request") or ""),
        "",
        "## Output",
        "",
        _clip(result["stdout"]),
        "",
        "## Errors",
        "",
        _clip(result["stderr"]) or "none",
        "",
    ]
    path = run_dir / "agent_run.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    _write_session_report(root, run_dir, task, agent_id, tool, mode, result)
    return path


def _write_session_report(
    root: Path,
    run_dir: Path,
    task: dict[str, Any],
    agent_id: str,
    tool: str,
    mode: str,
    result: dict[str, Any],
) -> None:
    session_name = task.get("session")
    if not session_name:
        return
    report_dir = CompanyPaths(root).sessions_dir / str(session_name) / "agent_reports"
    if not report_dir.exists():
        return
    report = report_dir / f"{task['id']}-{agent_id}-{tool}.md"
    report.write_text(
        "\n".join(
            [
                "# Agent Report",
                "",
                f"Task ID: {task['id']}",
                f"Role: {agent_id}",
                f"Tool: {tool}",
                f"Mode: {mode}",
                f"Status: {result['status']}",
                f"Created: {now_iso()}",
                "",
                "## Summary",
                "",
                f"External agent `{tool}` completed with status `{result['status']}`.",
                "",
                "## Evidence",
                "",
                rel(root, run_dir / "agent_run.md"),
                "",
                "## Output",
                "",
                _clip(result["stdout"]),
                "",
                "## Errors",
                "",
                _clip(result["stderr"]) or "none",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _update_task_after_run(root: Path, task: dict[str, Any], tool: str, mode: str, result: dict[str, Any], report: Path) -> None:
    runs = list(task.get("agent_runs") or [])
    runs.append(
        {
            "tool": tool,
            "mode": mode,
            "status": result["status"],
            "path": rel(root, report),
            "created_at": now_iso(),
        }
    )
    updates: dict[str, Any] = {
        "agent_runs": runs,
        "last_tool": tool,
        "last_agent_run": rel(root, report),
        "agent_status": result["status"],
    }
    if result["status"] == "ok":
        updates["status"] = "needs_review"
        updates["report"] = rel(root, report)
    elif result["status"] in {"failed", "blocked", "timeout"}:
        updates["status"] = "blocked"
        updates["report"] = rel(root, report)
    update_task(root, str(task["id"]), updates)


def _build_prompt(root: Path, task: dict[str, Any], agent_id: str, tool: str, mode: str, extra_prompt: str) -> str:
    paths = CompanyPaths(root)
    profile_path = _profile_path(root, agent_id)
    work_order = root / str(task.get("work_order") or "")
    work_order_text = read_text(work_order) if task.get("work_order") else "No work order file assigned yet."
    brief = read_text(paths.current_brief_md, read_text(paths.current_context_md))
    role_profile = read_text(profile_path, "No role profile file found.")
    allowed_paths = "\n".join(f"- {path}" for path in task.get("allowed_write_paths", [])) or "- none"
    extra = extra_prompt.strip() or "none"
    review_rule = "For review mode, avoid edits unless explicitly necessary; produce findings and risks first."
    return "\n".join(
        [
            "# Channel Play Agent Task",
            "",
            f"Tool: {tool}",
            f"Mode: {mode}",
            f"Task ID: {task['id']}",
            f"Role: {agent_id}",
            f"Workspace: {root}",
            "",
            "## Contract",
            "",
            "- Follow AGENTS.md, agents/company.md, and agents/memory_policy.md.",
            "- Write only inside the allowed paths unless the user explicitly expands scope.",
            "- Record changed files, decisions, evidence, and blockers.",
            f"- {review_rule}",
            "",
            "## Task Request",
            "",
            str(task.get("request") or ""),
            "",
            "## Allowed Write Paths",
            "",
            allowed_paths,
            "",
            "## Required Evidence",
            "",
            str(task.get("required_evidence") or "session note"),
            "",
            "## Extra Message",
            "",
            extra,
            "",
            "## Role Profile",
            "",
            _clip(role_profile, 8000),
            "",
            "## Work Order",
            "",
            _clip(work_order_text, 12000),
            "",
            "## Current Brief",
            "",
            _clip(brief, 12000),
            "",
        ]
    )


def _parse_run_args(args: list[str]) -> dict[str, Any]:
    if not args:
        raise CompanyError("Usage: agent run <task-id> [--tool name] [--dry-run] [--message text]")
    parsed = {"task_id": args[0], "tool": "", "dry_run": False, "message": ""}
    index = 1
    while index < len(args):
        flag = args[index]
        if flag == "--tool":
            index += 1
            if index >= len(args):
                raise CompanyError("--tool requires a value.")
            parsed["tool"] = args[index]
        elif flag == "--dry-run":
            parsed["dry_run"] = True
        elif flag == "--message":
            index += 1
            if index >= len(args):
                raise CompanyError("--message requires a value.")
            parsed["message"] = args[index]
        else:
            raise CompanyError(f"Unknown agent option: {flag}")
        index += 1
    return parsed


def _validate_adapters(data: dict[str, Any]) -> None:
    tools = data.get("tools")
    if not isinstance(tools, dict) or not tools:
        raise CompanyError("tool_adapters.json must contain a non-empty tools object.")
    for name, adapter in tools.items():
        if not isinstance(adapter, dict):
            raise CompanyError(f"Invalid adapter for {name}.")
        argv = adapter.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise CompanyError(f"Adapter {name} must define argv as a string list.")


def _adapter(config: dict[str, Any], tool: str) -> dict[str, Any]:
    adapter = config.get("tools", {}).get(tool)
    if not adapter:
        raise CompanyError(f"Unknown agent tool: {tool}")
    if not adapter.get("enabled", True):
        raise CompanyError(f"Agent tool disabled: {tool}")
    return adapter


def _select_tool(config: dict[str, Any], agent_id: str, mode: str, explicit: str) -> str:
    if explicit:
        return explicit
    if mode == "review":
        return str(config.get("review_tool") or "claude")
    role_defaults = config.get("role_defaults", {})
    return str(role_defaults.get(agent_id) or config.get("default_tool") or "codex")


def _task_agent(task: dict[str, Any], mode: str) -> str:
    if mode == "review":
        return str(task.get("suggested_reviewer") or "critic_reviewer")
    return str(task.get("assigned_agent") or task.get("suggested_agent") or "chief_orchestrator")


def _profile_path(root: Path, agent_id: str) -> Path:
    registry = read_json(CompanyPaths(root).agent_registry_json)
    for agent in registry.get("agents", []):
        if agent.get("id") == agent_id:
            return root / str(agent.get("profile") or "")
    return root / "agents" / "orchestrator.agent.md"


def _render_arg(template: str, context: dict[str, str]) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        raise CompanyError(f"Unknown adapter placeholder: {exc.args[0]}") from exc


def _coerce_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _clip(text: str, limit: int = 6000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[truncated]\n"


def _help() -> int:
    print(
        "\n".join(
            [
                "channelctl agent",
                "",
                "Commands:",
                "  adapters",
                "  check",
                "  run <task-id> [--tool codex|claude|agy|hermes|openclaw] [--dry-run]",
                "  review <task-id> [--tool codex|claude|agy|hermes|openclaw] [--dry-run]",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
