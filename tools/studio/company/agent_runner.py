"""External AI agent adapter runner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .advance import advance_task
from .codex_sdk import codex_sdk_status, run_codex_sdk_turn
from .errors import CompanyError
from .paths import find_repo_root, rel
from .state import CompanyPaths, read_json, read_text, write_json
from .tasks import find_task, update_task
from .timeutil import now_iso, slugify

DEFAULT_ADAPTERS: dict[str, Any] = {
    "version": 1,
    "default_tool": "codex",
    "review_tool": "codex",
    "default_timeout_seconds": 900,
    "health_ttl_seconds": 300,
    "excluded_tools": {
        "claude": {
            "status": "disabled",
            "disabled_reason": "Removed from Channel Play Studio per user request. Use codex, agy, hermes, or openclaw.",
        }
    },
        "role_defaults": {
            "chief_orchestrator": "codex",
            "production_planner": "codex",
            "coding_specialist": "codex",
            "toolchain_integrator": "codex",
            "research_librarian": "notebooklm",
            "operator_broadcast_designer": "hermes",
            "game_director": "hermes",
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
        "critic_reviewer": "codex",
    },
    "tools": {
        "codex": {
            "enabled": True,
            "description": "Codex Python SDK coding worker with CLI fallback",
            "execution": "codex_auto",
            "sdk_package": "openai_codex",
            "sdk_approval_mode": "auto_review",
            "sdk_sandbox": "workspace_write",
            "fallback_on_sdk_error": True,
            "argv": ["codex", "exec", "--cd", "{root}", "--sandbox", "workspace-write", "-"],
            "stdin": "{prompt}",
            "timeout_seconds": 1800,
            "version_command": ["codex", "--version"],
        },
        "agy": {
            "enabled": True,
            "description": "Antigravity CLI browser/UI worker",
            "argv": ["agy", "--print-timeout", "10m", "--print", "{prompt}"],
            "timeout_seconds": 900,
            "version_timeout_seconds": 10,
            "version_command": ["agy", "--version"],
        },
        "hermes": {
            "enabled": True,
            "description": "Hermes one-shot research and support worker",
            "argv": ["hermes", "-z", "{prompt}"],
            "timeout_seconds": 900,
            "version_command": ["hermes", "--version"],
        },
        "notebooklm": {
            "enabled": True,
            "description": "NotebookLM project-source research worker through nlm CLI",
            "argv": [
                "nlm",
                "notebook",
                "query",
                "--json",
                "--timeout",
                "120",
                "39e71010-ed96-496a-9395-a7fa7901fece",
                "Channel Play research request: {task_request}\nReturn a cited brief, source coverage, uncertainties, implementation implications, and next handoff.",
            ],
            "timeout_seconds": 180,
            "version_command": ["nlm", "--version"],
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
            "version_command": ["openclaw", "--version"],
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
            if parsed["full_approval"]:
                path, advance_path = run_agent_task_full_approval(
                    root,
                    parsed["task_id"],
                    tool_name=parsed["tool"],
                    mode=command,
                    dry_run=parsed["dry_run"],
                    extra_prompt=parsed["message"],
                )
            else:
                path = run_agent_task(
                    root,
                    parsed["task_id"],
                    tool_name=parsed["tool"],
                    mode=command,
                    dry_run=parsed["dry_run"],
                    extra_prompt=parsed["message"],
                )
                advance_path = None
            print(path.relative_to(root))
            if advance_path:
                print(advance_path.relative_to(root))
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
    if _merge_adapter_defaults(data):
        write_json(path, data)
    _validate_adapters(data)
    return data


def _merge_adapter_defaults(data: dict[str, Any]) -> bool:
    changed = False
    for key in ("health_ttl_seconds", "excluded_tools"):
        if key not in data:
            data[key] = json.loads(json.dumps(DEFAULT_ADAPTERS[key]))
            changed = True
    role_defaults = data.setdefault("role_defaults", {})
    if isinstance(role_defaults, dict):
        for role, tool in DEFAULT_ADAPTERS["role_defaults"].items():
            if role not in role_defaults:
                role_defaults[role] = tool
                changed = True
    tools = data.get("tools")
    if not isinstance(tools, dict):
        return changed
    for name, default_adapter in DEFAULT_ADAPTERS["tools"].items():
        adapter = tools.get(name)
        if not isinstance(adapter, dict):
            tools[name] = json.loads(json.dumps(default_adapter))
            changed = True
            continue
        if (
            name == "codex"
            and adapter.get("description") == "Codex CLI non-interactive coding worker"
            and default_adapter.get("description")
        ):
            adapter["description"] = default_adapter["description"]
            changed = True
        if name == "notebooklm" and "{prompt}" in [str(item) for item in adapter.get("argv", [])]:
            adapter["argv"] = json.loads(json.dumps(default_adapter["argv"]))
            changed = True
        for key in (
            "description",
            "timeout_seconds",
            "version_timeout_seconds",
            "version_command",
            "execution",
            "sdk_package",
            "sdk_approval_mode",
            "sdk_sandbox",
            "fallback_on_sdk_error",
        ):
            if key not in adapter and key in default_adapter:
                adapter[key] = json.loads(json.dumps(default_adapter[key]))
                changed = True
    return changed


def collect_agent_adapter_state(root: Path) -> dict[str, Any]:
    config = ensure_tool_adapters(root)
    tools = {}
    config_changed = False
    for name, adapter in sorted(config.get("tools", {}).items()):
        health, changed = _adapter_health(root, config, name, adapter)
        config_changed = config_changed or changed
        tools[name] = health
    if config_changed:
        write_json(CompanyPaths(root).tool_adapters_json, config)
    summary = _adapter_summary(tools)
    return {
        "defaultTool": config.get("default_tool"),
        "reviewTool": config.get("review_tool"),
        "tools": tools,
        "summary": summary,
        "excludedTools": config.get("excluded_tools", {}),
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
        lines.append(
            f"  {name:<10} {enabled:<8} {tool['status']:<22} {tool['executable']} "
            f"{tool.get('version', '')}".rstrip()
        )
        if tool.get("execution") != "cli" or tool.get("sdkPackage"):
            lines.append(
                f"    executor={tool.get('primaryExecutor', 'cli')} "
                f"sdk={tool.get('sdkPackage') or 'none'}:{tool.get('sdkStatus') or 'none'}"
            )
    if state.get("excludedTools"):
        lines.extend(["", "Excluded tools:"])
        for name, item in state["excludedTools"].items():
            lines.append(f"  {name:<10} {item.get('status', 'disabled'):<8} {item.get('disabled_reason', '')}")
    return "\n".join(lines)


def _adapter_health(root: Path, config: dict[str, Any], name: str, adapter: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    argv = adapter.get("argv") or []
    executable = str(argv[0]) if argv else ""
    resolved_path = shutil.which(executable) or ""
    enabled = bool(adapter.get("enabled", True))
    execution = str(adapter.get("execution") or "cli")
    sdk = codex_sdk_status(str(adapter.get("sdk_package") or "openai_codex"), root) if _uses_codex_sdk(adapter) else {}
    cached = adapter.get("last_health") if isinstance(adapter.get("last_health"), dict) else {}
    ttl = int(config.get("health_ttl_seconds") or 300)
    should_probe = enabled and bool(resolved_path) and (
        str(cached.get("status") or "") != "available" or _cache_expired(str(cached.get("last_check") or ""), ttl)
    )
    changed = False

    if not enabled:
        status = "disabled"
        version = str(cached.get("version") or "")
        last_error = str(adapter.get("disabled_reason") or cached.get("last_error") or "Adapter disabled in configuration.")
    elif sdk.get("available") and not resolved_path:
        status = "available"
        version = _sdk_version_label(sdk)
        last_error = ""
    elif not resolved_path:
        status = "missing"
        version = ""
        if sdk:
            last_error = f"Codex SDK unavailable and executable not found: {executable}; {sdk.get('last_error', '')}".strip()
        else:
            last_error = f"Executable not found: {executable}"
    elif should_probe:
        status, version, last_error = _probe_adapter_version(adapter, resolved_path)
        if sdk.get("available") and version:
            version = f"{version}; {_sdk_version_label(sdk)}"
        adapter["last_health"] = {
            "status": status,
            "version": version,
            "last_error": last_error,
            "last_check": _now_utc(),
            "resolved_path": resolved_path,
            "sdk": sdk,
        }
        changed = True
    else:
        status = str(cached.get("status") or "available")
        version = str(cached.get("version") or "")
        last_error = str(cached.get("last_error") or "")

    if sdk:
        last_health = adapter.get("last_health") if isinstance(adapter.get("last_health"), dict) else {}
        if last_health.get("sdk") != sdk:
            last_health["sdk"] = sdk
            last_health["last_check"] = _now_utc()
            adapter["last_health"] = last_health
            changed = True

    health = {
        "enabled": enabled,
        "available": status == "available",
        "status": status,
        "executable": executable,
        "resolvedPath": resolved_path,
        "description": str(adapter.get("description", "")),
        "version": version,
        "lastCheck": str((adapter.get("last_health") or {}).get("last_check") or cached.get("last_check") or ""),
        "lastError": last_error,
        "defaultRoles": _roles_for_tool(config, name),
        "timeoutSeconds": int(adapter.get("timeout_seconds") or config.get("default_timeout_seconds") or 900),
        "versionCommand": _version_command(adapter, resolved_path),
        "commandPreview": " ".join(str(item) for item in argv),
        "disabledReason": str(adapter.get("disabled_reason") or ""),
        "execution": execution,
        "primaryExecutor": _primary_executor(adapter, sdk, bool(resolved_path)),
        "sdkPackage": str(adapter.get("sdk_package") or ""),
        "sdkAvailable": bool(sdk.get("available")),
        "sdkStatus": str(sdk.get("status") or ""),
        "sdkVersion": str(sdk.get("version") or ""),
        "sdkOrigin": str(sdk.get("origin") or ""),
    }
    return health, changed


def _probe_adapter_version(adapter: dict[str, Any], resolved_path: str) -> tuple[str, str, str]:
    command = _version_command(adapter, resolved_path)
    if not command:
        return "available", "", ""
    timeout = int(adapter.get("version_timeout_seconds") or 3)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "configured_but_failed", "", f"Version check timed out after {timeout}s."
    except OSError as exc:
        return "configured_but_failed", "", str(exc)

    output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    if result.returncode == 0:
        return "available", _first_line(output), ""
    status = "auth_missing" if _looks_like_auth_error(output) else "configured_but_failed"
    return status, "", _first_line(output) or f"Version check failed with exit {result.returncode}."


def _version_command(adapter: dict[str, Any], resolved_path: str) -> list[str]:
    command = adapter.get("version_command")
    if not isinstance(command, list) or not command:
        return []
    rendered = [str(item) for item in command]
    if rendered:
        rendered[0] = resolved_path
    return rendered


def _roles_for_tool(config: dict[str, Any], tool: str) -> list[str]:
    return sorted(role for role, default_tool in (config.get("role_defaults") or {}).items() if default_tool == tool)


def _adapter_summary(tools: dict[str, dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(tools), "available": 0, "missing": 0, "disabled": 0, "failed": 0, "authMissing": 0}
    for tool in tools.values():
        status = tool.get("status")
        if status == "available":
            summary["available"] += 1
        elif status == "missing":
            summary["missing"] += 1
        elif status == "disabled":
            summary["disabled"] += 1
        elif status == "auth_missing":
            summary["authMissing"] += 1
        else:
            summary["failed"] += 1
    return summary


def _cache_expired(last_check: str, ttl_seconds: int) -> bool:
    if not last_check:
        return True
    try:
        checked_at = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - checked_at).total_seconds() >= ttl_seconds


def _looks_like_auth_error(output: str) -> bool:
    lowered = output.lower()
    return any(term in lowered for term in ("auth", "login", "token", "credential", "account", "api key", "permission"))


def _first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text.strip() else ""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    tool = _select_tool(root, config, agent_id, mode, tool_name)
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
        "task_request": str(task.get("request") or task_id),
        "run_dir": str(run_dir),
        "work_order": str(root / str(task.get("work_order") or "")),
    }
    command = [_render_arg(str(arg), context) for arg in adapter.get("argv", [])]
    stdin_template = adapter.get("stdin")
    stdin = _render_arg(str(stdin_template), context) if stdin_template else None
    timeout = int(adapter.get("timeout_seconds") or config.get("default_timeout_seconds") or 900)

    result = _execute_adapter(adapter, command, root, stdin, timeout, dry_run)
    (run_dir / "command.json").write_text(
        json.dumps(
            {
                "command": command,
                "dry_run": dry_run,
                "timeout_seconds": timeout,
                "executor": result.get("executor", "cli"),
                "sdk": result.get("sdk", {}),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "stdout.txt").write_text(result["stdout"], encoding="utf-8")
    (run_dir / "stderr.txt").write_text(result["stderr"], encoding="utf-8")
    report = _write_run_report(root, run_dir, task, agent_id, tool, mode, result)
    _update_task_after_run(root, task, tool, mode, result, report)
    return run_dir / "agent_run.md"


def run_agent_task_full_approval(
    root: Path,
    task_id: str,
    *,
    tool_name: str = "",
    mode: str = "run",
    dry_run: bool = False,
    extra_prompt: str = "",
) -> tuple[Path, Path | None]:
    report = run_agent_task(
        root,
        task_id,
        tool_name=tool_name,
        mode=mode,
        dry_run=dry_run,
        extra_prompt=extra_prompt,
    )
    task = find_task(root, task_id)
    if task.get("agent_status") not in {"ok", "dry_run"}:
        return report, None
    if mode == "review" and task.get("agent_status") == "ok" and task.get("review_status") != "approved":
        return report, None
    advance = advance_task(root, task_id)
    return report, advance


def _execute_adapter(
    adapter: dict[str, Any],
    command: list[str],
    root: Path,
    stdin: str | None,
    timeout: int,
    dry_run: bool,
) -> dict[str, Any]:
    if _uses_codex_sdk(adapter):
        return _execute_codex_auto(adapter, command, root, stdin or "", timeout, dry_run)
    return _execute(command, root, stdin, timeout, dry_run)


def _execute_codex_auto(
    adapter: dict[str, Any],
    command: list[str],
    root: Path,
    prompt: str,
    timeout: int,
    dry_run: bool,
) -> dict[str, Any]:
    package = str(adapter.get("sdk_package") or "openai_codex")
    sdk = codex_sdk_status(package, root)
    cli_available = bool(command and shutil.which(command[0]))
    if dry_run:
        executor = "codex_sdk" if sdk.get("available") else "cli_fallback"
        stderr = "" if sdk.get("available") or cli_available else f"Codex SDK unavailable and executable not found: {command[0]}\n"
        return {
            "status": "dry_run",
            "exit": 0,
            "stdout": f"Dry run only. Agent command was not executed. Executor: {executor}.\n",
            "stderr": stderr,
            "executor": executor,
            "sdk": sdk,
        }
    if sdk.get("available"):
        result = run_codex_sdk_turn(
            root,
            prompt,
            timeout_seconds=timeout,
            package=package,
            approval_mode_name=str(adapter.get("sdk_approval_mode") or "auto_review"),
            sandbox_name=str(adapter.get("sdk_sandbox") or "workspace_write"),
            model=str(adapter.get("sdk_model") or ""),
        )
        if result.get("status") == "failed" and _looks_like_auth_error(str(result.get("stderr") or "")):
            result["status"] = "auth_missing"
        if result.get("status") in {"ok", "timeout"} or not adapter.get("fallback_on_sdk_error", True):
            return result
        fallback = _execute(command, root, prompt, timeout, False)
        fallback["executor"] = "cli_fallback"
        fallback["sdk"] = sdk
        fallback["stderr"] = (
            f"Codex SDK failed; CLI fallback used.\n{result.get('stderr', '').strip()}\n\n"
            f"CLI stderr:\n{fallback.get('stderr', '')}"
        )
        return fallback
    fallback = _execute(command, root, prompt, timeout, False)
    fallback["executor"] = "cli_fallback"
    fallback["sdk"] = sdk
    return fallback


def _execute(command: list[str], root: Path, stdin: str | None, timeout: int, dry_run: bool) -> dict[str, Any]:
    if not command:
        raise CompanyError("Adapter argv is empty.")
    executable = command[0]
    resolved_executable = shutil.which(executable)
    available = resolved_executable is not None
    if dry_run:
        return {
            "status": "dry_run",
            "exit": 0,
            "stdout": "Dry run only. Agent command was not executed.\n",
            "stderr": "" if available else f"Executable not found: {executable}\n",
            "executor": "cli",
        }
    if not available:
        return {
            "status": "blocked",
            "exit": 127,
            "stdout": "",
            "stderr": f"Executable not found: {executable}\n",
            "executor": "cli",
        }

    env = os.environ.copy()
    env["CHANNEL_PLAY_ROOT"] = str(root)
    resolved_command = [str(resolved_executable), *command[1:]]
    try:
        completed = subprocess.run(
            resolved_command,
            cwd=root,
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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
            "executor": "cli",
        }
    status = _process_status(completed.returncode, completed.stdout, completed.stderr)
    return {
        "status": status,
        "exit": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "executor": "cli",
    }


def _process_status(returncode: int, stdout: str, stderr: str) -> str:
    if returncode != 0:
        return "failed"
    if stdout.strip():
        return "ok"

    error_text = stderr.casefold()
    no_output_failures = (
        "no output produced",
        "auto-denied",
        "permission denied",
    )
    if any(marker in error_text for marker in no_output_failures):
        return "failed"
    return "ok"


def _review_outcome(stdout: str) -> str:
    verdict_prefixes = ("verdict:", "판정:", "review outcome:")
    for raw_line in stdout.splitlines():
        line = raw_line.strip().casefold()
        if not line.startswith(verdict_prefixes):
            continue
        verdict = line.split(":", 1)[1].replace("*", "").replace("`", "").strip()
        if verdict.startswith(("changes required", "changes requested", "changes_requested", "변경 필요", "수정 필요")):
            return "changes_required"
        if verdict.startswith(("approved", "approve", "승인", "no changes required")):
            return "approved"
    return "unresolved"


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
        f"Executor: {result.get('executor', 'cli')}",
        f"Mode: {mode}",
        f"Status: {result['status']}",
        *(
            [f"Review outcome: {_review_outcome(result['stdout'])}"]
            if mode == "review" and result["status"] == "ok"
            else []
        ),
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
                f"Executor: {result.get('executor', 'cli')}",
                f"Mode: {mode}",
                f"Status: {result['status']}",
                *(
                    [f"Review outcome: {_review_outcome(result['stdout'])}"]
                    if mode == "review" and result["status"] == "ok"
                    else []
                ),
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
    if result["status"] in {"ok", "dry_run"}:
        if mode == "review" and result["status"] == "ok":
            review_outcome = _review_outcome(result["stdout"])
            updates["review_status"] = review_outcome
            updates["reviewer"] = str(task.get("suggested_reviewer") or "critic_reviewer")
            if review_outcome == "approved":
                updates["status"] = "needs_evidence"
            elif review_outcome == "changes_required":
                updates["status"] = "blocked"
                updates["blocked_reason"] = f"Critic review requested changes; see {rel(root, report)}."
            else:
                updates["status"] = "needs_review"
        else:
            updates["status"] = "needs_evidence" if mode == "review" else "needs_review"
        updates["report"] = rel(root, report)
    elif result["status"] in {"failed", "blocked", "timeout", "auth_missing"}:
        updates["status"] = "blocked"
        updates["report"] = rel(root, report)
    update_task(root, str(task["id"]), updates)


def _build_prompt(root: Path, task: dict[str, Any], agent_id: str, tool: str, mode: str, extra_prompt: str) -> str:
    paths = CompanyPaths(root)
    agent_entry = _agent_entry(root, agent_id)
    profile_path = root / str(agent_entry.get("profile") or "agents/orchestrator.agent.md")
    work_order = root / str(task.get("work_order") or "")
    work_order_text = read_text(work_order) if task.get("work_order") else "No work order file assigned yet."
    brief = read_text(paths.current_brief_md, read_text(paths.current_context_md))
    role_profile = read_text(profile_path, "No role profile file found.")
    state = read_json(paths.state_json)
    integrated_goal = state.get("integrated_goal", {})
    agent_setting = agent_entry.get("goal_setting", {})
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
            "## Integrated Goal",
            "",
            json.dumps(integrated_goal, ensure_ascii=False, indent=2),
            "",
            "## Current Agent Setting",
            "",
            json.dumps(agent_setting, ensure_ascii=False, indent=2),
            "",
            "## Contract",
            "",
            "- Follow AGENTS.md, agents/company.md, and agents/memory_policy.md.",
            "- Write only inside the allowed paths unless the user explicitly expands scope.",
            "- Record changed files, decisions, evidence, and blockers.",
            f"- {review_rule}",
            "- Keep every output tied to the integrated goal and the current MVP milestone.",
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
        raise CompanyError("Usage: agent run <task-id> [--tool name] [--dry-run] [--message text] [--full-approval|--manual-review]")
    parsed = {"task_id": args[0], "tool": "", "dry_run": False, "message": "", "full_approval": True}
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
        elif flag in {"--full-approval", "--auto-advance"}:
            parsed["full_approval"] = True
        elif flag in {"--manual-review", "--no-auto-advance"}:
            parsed["full_approval"] = False
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


def _uses_codex_sdk(adapter: dict[str, Any]) -> bool:
    return str(adapter.get("execution") or "") in {"codex_auto", "codex_sdk"}


def _sdk_version_label(sdk: dict[str, Any]) -> str:
    version = str(sdk.get("version") or "unknown")
    return f"{sdk.get('package', 'openai_codex')} {version}".strip()


def _primary_executor(adapter: dict[str, Any], sdk: dict[str, Any], cli_available: bool) -> str:
    if not _uses_codex_sdk(adapter):
        return "cli"
    if sdk.get("available"):
        return "codex_sdk"
    if cli_available:
        return "cli_fallback"
    return "missing"


def _select_tool(root: Path, config: dict[str, Any], agent_id: str, mode: str, explicit: str) -> str:
    if explicit:
        return explicit
    agent_tool = str(_agent_entry(root, agent_id).get("goal_setting", {}).get("tool") or "")
    if agent_tool:
        return agent_tool
    if mode == "review":
        return str(config.get("review_tool") or "codex")
    role_defaults = config.get("role_defaults", {})
    return str(role_defaults.get(agent_id) or config.get("default_tool") or "codex")


def _task_agent(task: dict[str, Any], mode: str) -> str:
    if mode == "review":
        return str(task.get("suggested_reviewer") or "critic_reviewer")
    return str(task.get("assigned_agent") or task.get("suggested_agent") or "chief_orchestrator")


def _agent_entry(root: Path, agent_id: str) -> dict[str, Any]:
    registry = read_json(CompanyPaths(root).agent_registry_json)
    for agent in registry.get("agents", []):
        if agent.get("id") == agent_id:
            return agent
    return {"id": agent_id, "profile": "agents/orchestrator.agent.md"}


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
                "  run <task-id> [--tool codex|agy|hermes|openclaw] [--dry-run]",
                "  review <task-id> [--tool codex|agy|hermes|openclaw] [--dry-run]",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
