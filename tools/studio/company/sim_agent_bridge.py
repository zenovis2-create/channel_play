"""External AI agent bridge for simulation run artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .errors import CompanyError
from .paths import rel
from .timeutil import now_iso, slugify

VALID_ACTIONS = {
    "spawn_at_marker",
    "move_to_marker",
    "look_at_marker",
    "capture_observation",
    "finish_run",
    "wait",
    "interact",
}

DEFAULT_ROUTE = [
    "MazeV2_Entrance_Threshold",
    "MazeV2_Djoser_Gallery",
    "MazeV2_Khufu_GrandGallery",
    "MazeV2_Hawara_Labyrinth_Core",
    "MazeV2_Burial_Chamber",
    "MazeV2_Rear_Service_Exit",
]

AGENTS = {
    "codex": {
        "command": ["codex", "exec", "--cd", "{root}", "--sandbox", "read-only", "-"],
        "timeout": 180,
    },
    "openclaw": {
        "command": ["openclaw", "agent", "--local", "--json", "--agent", "main", "--message", "{prompt}"],
        "timeout": 180,
    },
    "hermes": {
        "command": ["hermes", "-z", "{prompt}"],
        "timeout": 180,
    },
    "agy": {
        "command": ["agy", "--print-timeout", "3m", "--print", "{prompt}"],
        "timeout": 180,
    },
}


def sim_agent_packet(root: Path, args: list[str]) -> Path:
    if len(args) != 1:
        raise CompanyError("Usage: sim-agent packet <agent-run-dir>")
    source = _resolve_run(root, args[0])
    run_dir = _unique_run_dir(root, "external-agent-packet")
    run_dir.mkdir(parents=True, exist_ok=False)
    packet = _build_request_packet(root, source, "packet")
    path = run_dir / "request_packet.json"
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = run_dir / "receipt.md"
    receipt.write_text(_packet_receipt(root, source, path, packet), encoding="utf-8")
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def sim_agent_run(root: Path, args: list[str]) -> Path:
    if len(args) < 2:
        raise CompanyError("Usage: sim-agent run <codex|openclaw|hermes|agy> <agent-run-dir> [--live] [--timeout seconds] [--retries n]")
    agent = args[0].strip().lower()
    if agent not in AGENTS:
        raise CompanyError(f"Unknown simulation agent: {agent}")
    source = _resolve_run(root, args[1])
    live = "--live" in args
    timeout = int(_option(args[2:], "--timeout", str(AGENTS[agent]["timeout"])))
    retries = int(_option(args[2:], "--retries", "1"))
    run_dir = _unique_run_dir(root, f"external-agent-{agent}")
    run_dir.mkdir(parents=True, exist_ok=False)

    packet = _build_request_packet(root, source, agent)
    packet_path = run_dir / "request_packet.json"
    response_path = run_dir / "response.json"
    validation_path = run_dir / "validation.json"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    execution = _execute_agent(root, agent, packet, timeout=timeout, retries=retries, live=live)
    response = execution["response"]
    validation = _validate_response(response)
    status = "external_agent_run_passed" if validation["valid"] else "external_agent_run_failed"
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "stdout.txt").write_text(execution.get("stdout", ""), encoding="utf-8", errors="ignore")
    (run_dir / "stderr.txt").write_text(execution.get("stderr", ""), encoding="utf-8", errors="ignore")

    receipt = run_dir / "receipt.md"
    receipt.write_text(
        _agent_receipt(root, source, agent, live, timeout, retries, status, execution, validation, packet_path, response_path, validation_path),
        encoding="utf-8",
    )
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def sim_agent_compare(root: Path, args: list[str]) -> Path:
    if len(args) != 2:
        raise CompanyError("Usage: sim-agent compare <external-agent-run-a> <external-agent-run-b>")
    first = _resolve_run(root, args[0])
    second = _resolve_run(root, args[1])
    first_response = _read_json(first / "response.json", default={})
    second_response = _read_json(second / "response.json", default={})
    comparison = _compare_agent_responses(root, first, second, first_response, second_response)
    run_dir = _unique_run_dir(root, "external-agent-compare")
    run_dir.mkdir(parents=True, exist_ok=False)
    comparison_path = run_dir / "comparison.json"
    receipt = run_dir / "receipt.md"
    comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_compare_receipt(root, comparison, comparison_path), encoding="utf-8")
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def sim_agent_live_check(root: Path, args: list[str]) -> Path:
    if len(args) < 2:
        raise CompanyError("Usage: sim-agent live-check <codex|openclaw|hermes|agy|all> <agent-run-dir> [--timeout seconds] [--retries n]")
    requested = args[0].strip().lower()
    source = _resolve_run(root, args[1])
    timeout = int(_option(args[2:], "--timeout", "240"))
    retries = int(_option(args[2:], "--retries", "0"))
    agents = ["codex", "openclaw"] if requested == "all" else [requested]
    unknown = [agent for agent in agents if agent not in AGENTS]
    if unknown:
        raise CompanyError(f"Unknown simulation agent: {', '.join(unknown)}")

    run_dir = _unique_run_dir(root, "external-agent-live-check")
    run_dir.mkdir(parents=True, exist_ok=False)
    runs = []
    for agent in agents:
        packet = _build_request_packet(root, source, agent)
        execution = _execute_agent(root, agent, packet, timeout=timeout, retries=retries, live=True)
        validation = _validate_response(execution["response"])
        agent_dir = run_dir / agent
        agent_dir.mkdir(parents=True, exist_ok=False)
        (agent_dir / "request_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (agent_dir / "response.json").write_text(json.dumps(execution["response"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (agent_dir / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (agent_dir / "stdout.txt").write_text(execution.get("stdout", ""), encoding="utf-8", errors="ignore")
        (agent_dir / "stderr.txt").write_text(execution.get("stderr", ""), encoding="utf-8", errors="ignore")
        live_verified = execution.get("status") == "live" and validation.get("valid")
        runs.append(
            {
                "agent": agent,
                "status": "live_verified" if live_verified else "live_not_verified",
                "adapterStatus": execution.get("status"),
                "exit": execution.get("exit"),
                "attempts": execution.get("attempts"),
                "validation": "passed" if validation.get("valid") else "failed",
                "actionCount": validation.get("actionCount", 0),
                "dir": rel(root, agent_dir),
            }
        )
    live_verified_count = sum(1 for run in runs if run["status"] == "live_verified")
    status = "external_agent_live_check_passed" if live_verified_count == len(runs) else "external_agent_live_check_blocked"
    manifest = {
        "schema": "channel_play.external_agent_live_check.v1",
        "checkedAt": now_iso(),
        "status": status,
        "sourceRun": rel(root, source),
        "timeoutSeconds": timeout,
        "retries": retries,
        "liveVerified": live_verified_count,
        "total": len(runs),
        "runs": runs,
    }
    manifest_path = run_dir / "live_check.json"
    receipt = run_dir / "receipt.md"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_live_check_receipt(root, manifest, manifest_path), encoding="utf-8")
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def _build_request_packet(root: Path, source: Path, agent: str) -> dict[str, Any]:
    metrics = _read_jsonl(source / "metrics.jsonl")
    actions = _read_jsonl(source / "actions.jsonl")
    trajectory = _read_json(source / "trajectory.json", default={"points": []})
    scene_state = _read_json(source / "scene_state.json", default={})
    observations = _observation_frames(root, source)
    route = [metric.get("marker", "") for metric in metrics if metric.get("marker")] or DEFAULT_ROUTE
    return {
        "schema": "channel_play.external_agent_request.v1",
        "createdAt": now_iso(),
        "agent": agent,
        "sourceRun": rel(root, source),
        "mode": "read_only_observation_packet",
        "writeScope": "current_external_agent_run_dir_only",
        "allowedActions": sorted(VALID_ACTIONS),
        "route": route,
        "observations": observations,
        "sceneStatePath": rel(root, source / "scene_state.json") if (source / "scene_state.json").exists() else "",
        "semanticLabelsPath": rel(root, source / "semantic_labels.json") if (source / "semantic_labels.json").exists() else "",
        "priorActions": actions,
        "metrics": metrics,
        "trajectory": trajectory,
        "scene": scene_state.get("scene", "School_MVP") if isinstance(scene_state, dict) else "School_MVP",
    }


def _execute_agent(root: Path, agent: str, packet: dict[str, Any], *, timeout: int, retries: int, live: bool) -> dict[str, Any]:
    if not live:
        return {
            "status": "mock_controlled",
            "exit": 0,
            "attempts": 0,
            "stdout": "mock external agent response\n",
            "stderr": "",
            "response": _mock_response(agent, packet),
        }

    config = AGENTS[agent]
    executable = str(config["command"][0])
    if shutil.which(executable) is None:
        return {
            "status": "blocked",
            "exit": 127,
            "attempts": 0,
            "stdout": "",
            "stderr": f"Executable not found: {executable}\n",
            "response": _mock_response(agent, packet, status="adapter_blocked"),
        }
    prompt = _agent_prompt(packet)
    command = [str(part).format(root=str(root), prompt=prompt) for part in config["command"]]
    stdout = ""
    stderr = ""
    exit_code = 1
    attempts = max(1, retries + 1)
    for attempt in range(1, attempts + 1):
        try:
            completed = subprocess.run(command, cwd=root, input=prompt, capture_output=True, text=True, check=False, timeout=timeout)
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
            if completed.returncode == 0:
                break
        except subprocess.TimeoutExpired as exc:
            stdout = _coerce_output(exc.stdout)
            stderr = _coerce_output(exc.stderr) + f"\nTimed out after {timeout}s.\n"
            exit_code = 124
    parsed = _extract_response_json(stdout)
    return {
        "status": "live" if exit_code == 0 and parsed else "live_fallback_mock",
        "exit": exit_code,
        "attempts": attempts,
        "stdout": stdout,
        "stderr": stderr,
        "response": parsed or _mock_response(agent, packet, status="live_response_unparseable"),
    }


def _mock_response(agent: str, packet: dict[str, Any], *, status: str = "ok") -> dict[str, Any]:
    route = packet.get("route") or DEFAULT_ROUTE
    actions = [{"step": 0, "action": "spawn_at_marker", "target": route[0]}]
    for index, marker in enumerate(route[1:], start=1):
        actions.append({"step": index, "action": "move_to_marker", "target": marker})
    actions.append({"step": len(actions), "action": "finish_run", "target": "route_complete"})
    return {
        "schema": "channel_play.external_agent_response.v1",
        "agent": agent,
        "status": status,
        "actions": actions,
        "rationale": "Follow validated route markers from the read-only observation packet.",
        "confidence": 0.82,
    }


def _validate_response(response: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if response.get("schema") != "channel_play.external_agent_response.v1":
        failures.append("invalid response schema")
    actions = response.get("actions")
    if not isinstance(actions, list) or not actions:
        failures.append("actions must be a non-empty list")
        actions = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            failures.append(f"action[{index}] is not an object")
            continue
        if action.get("action") not in VALID_ACTIONS:
            failures.append(f"action[{index}] unknown action: {action.get('action')}")
        if "target" not in action:
            failures.append(f"action[{index}] missing target")
    return {
        "schema": "channel_play.external_agent_validation.v1",
        "valid": not failures,
        "failures": failures,
        "actionCount": len(actions),
        "checkedAt": now_iso(),
    }


def _observation_frames(root: Path, source: Path) -> list[dict[str, Any]]:
    observation_dir = source / "observations"
    if not observation_dir.exists():
        return []
    frames = []
    for rgb in sorted(observation_dir.glob("frame_*_rgb.png")):
        frame = _frame_number(rgb)
        metadata_path = observation_dir / f"frame_{frame:03d}.json"
        metadata = _read_json(metadata_path, default={})
        frames.append(
            {
                "frame": frame,
                "rgb": rel(root, rgb),
                "segmentation": rel(root, observation_dir / f"frame_{frame:03d}_segmentation.png"),
                "depth": rel(root, observation_dir / f"frame_{frame:03d}_depth.png"),
                "metadata": rel(root, metadata_path),
                "routeMarker": metadata.get("routeMarker", "") if isinstance(metadata, dict) else "",
            }
        )
    return frames


def _compare_agent_responses(root: Path, first: Path, second: Path, first_response: dict[str, Any], second_response: dict[str, Any]) -> dict[str, Any]:
    first_actions = first_response.get("actions") if isinstance(first_response.get("actions"), list) else []
    second_actions = second_response.get("actions") if isinstance(second_response.get("actions"), list) else []
    diffs = []
    if len(first_actions) != len(second_actions):
        diffs.append(f"action count changed: {len(first_actions)} -> {len(second_actions)}")
    if [item.get("action") for item in first_actions] != [item.get("action") for item in second_actions]:
        diffs.append("action sequence changed")
    if [item.get("target") for item in first_actions] != [item.get("target") for item in second_actions]:
        diffs.append("target sequence changed")
    return {
        "schema": "channel_play.external_agent_comparison.v1",
        "status": "external_agent_compare_passed" if not diffs else "external_agent_compare_changed",
        "checkedAt": now_iso(),
        "firstRun": rel(root, first),
        "secondRun": rel(root, second),
        "firstAgent": first_response.get("agent", ""),
        "secondAgent": second_response.get("agent", ""),
        "diffs": diffs,
    }


def _agent_prompt(packet: dict[str, Any]) -> str:
    return (
        "Return only JSON matching channel_play.external_agent_response.v1. "
        "Use only allowedActions. Do not write files. Packet:\n"
        + json.dumps(packet, ensure_ascii=False)
    )


def _extract_response_json(stdout: str) -> dict[str, Any] | None:
    stripped = stdout.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
        return _unwrap_response_json(parsed)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(stripped[start : end + 1])
                return _unwrap_response_json(parsed)
            except json.JSONDecodeError:
                return None
    return None


def _unwrap_response_json(parsed: Any) -> dict[str, Any] | None:
    if not isinstance(parsed, dict):
        return None
    if parsed.get("schema") == "channel_play.external_agent_response.v1":
        return parsed
    payloads = parsed.get("payloads")
    if isinstance(payloads, list):
        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            text = payload.get("text") or payload.get("content")
            if isinstance(text, str):
                nested = _extract_response_json(text)
                if nested:
                    return nested
    text = parsed.get("text") or parsed.get("content")
    if isinstance(text, str):
        nested = _extract_response_json(text)
        if nested:
            return nested
    return parsed


def _packet_receipt(root: Path, source: Path, packet_path: Path, packet: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# External Agent Packet Receipt",
            "",
            f"Checked: {now_iso()}",
            "Status: `external_agent_packet_ready`",
            f"Source run: `{rel(root, source)}`",
            f"Packet: `{rel(root, packet_path)}`",
            f"Observations: `{len(packet.get('observations') or [])}`",
            f"Prior actions: `{len(packet.get('priorActions') or [])}`",
            f"Write scope: `{packet.get('writeScope')}`",
            "",
        ]
    )


def _agent_receipt(
    root: Path,
    source: Path,
    agent: str,
    live: bool,
    timeout: int,
    retries: int,
    status: str,
    execution: dict[str, Any],
    validation: dict[str, Any],
    packet_path: Path,
    response_path: Path,
    validation_path: Path,
) -> str:
    failure_lines = [f"- {failure}" for failure in validation.get("failures", [])] if validation.get("failures") else ["none"]
    return "\n".join(
        [
            "# External Agent Bridge Receipt",
            "",
            f"Checked: {now_iso()}",
            f"Status: `{status}`",
            f"Agent: `{agent}`",
            f"Execution: `{'live' if live else 'mock_controlled'}`",
            f"Adapter status: `{execution.get('status')}`",
            f"Source run: `{rel(root, source)}`",
            f"Timeout seconds: `{timeout}`",
            f"Retries: `{retries}`",
            f"Validation: `{'passed' if validation.get('valid') else 'failed'}`",
            f"Action count: `{validation.get('actionCount')}`",
            f"Request packet: `{rel(root, packet_path)}`",
            f"Response: `{rel(root, response_path)}`",
            f"Validation report: `{rel(root, validation_path)}`",
            "",
            "## Failures",
            "",
            *failure_lines,
            "",
        ]
    )


def _compare_receipt(root: Path, comparison: dict[str, Any], comparison_path: Path) -> str:
    diffs = comparison.get("diffs") or []
    diff_lines = [f"- {diff}" for diff in diffs] if diffs else ["none"]
    return "\n".join(
        [
            "# External Agent Comparison Receipt",
            "",
            f"Checked: {now_iso()}",
            f"Status: `{comparison.get('status')}`",
            f"First: `{comparison.get('firstAgent')}` `{comparison.get('firstRun')}`",
            f"Second: `{comparison.get('secondAgent')}` `{comparison.get('secondRun')}`",
            f"Diff count: `{len(diffs)}`",
            f"Comparison: `{rel(root, comparison_path)}`",
            "",
            "## Diffs",
            "",
            *diff_lines,
            "",
        ]
    )


def _live_check_receipt(root: Path, manifest: dict[str, Any], manifest_path: Path) -> str:
    lines = [
        "# External Agent Live Check Receipt",
        "",
        f"Checked: {manifest['checkedAt']}",
        f"Status: `{manifest['status']}`",
        f"Source run: `{manifest['sourceRun']}`",
        f"Live verified: `{manifest['liveVerified']}/{manifest['total']}`",
        f"Timeout seconds: `{manifest['timeoutSeconds']}`",
        f"Retries: `{manifest['retries']}`",
        f"Manifest: `{rel(root, manifest_path)}`",
        "",
        "## Agents",
        "",
    ]
    for run in manifest["runs"]:
        lines.append(
            "- `{agent}` status=`{status}` adapter=`{adapter}` validation=`{validation}` actions=`{actions}` dir=`{dir}`".format(
                agent=run["agent"],
                status=run["status"],
                adapter=run["adapterStatus"],
                validation=run["validation"],
                actions=run["actionCount"],
                dir=run["dir"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _resolve_run(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.exists() or not path.is_dir():
        raise CompanyError(f"Run directory not found: {path}")
    return path


def _unique_run_dir(root: Path, prefix: str) -> Path:
    base = root / "runs" / f"{prefix}-{slugify(now_iso())}"
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = root / "runs" / f"{base.name}-{suffix}"
        suffix += 1
    return candidate


def _option(args: list[str], name: str, default: str) -> str:
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        raise CompanyError(f"Missing value for {name}")
    return args[index + 1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
            rows.append(parsed if isinstance(parsed, dict) else {"value": parsed})
        except json.JSONDecodeError:
            rows.append({"parseError": stripped[:200]})
    return rows


def _read_json(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except json.JSONDecodeError:
        return default


def _frame_number(path: Path) -> int:
    stem = path.name.split("_")
    for part in stem:
        if part.isdigit():
            return int(part)
    return 0


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value
