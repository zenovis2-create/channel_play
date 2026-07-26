"""Model and runtime cookbook for Channel Play work."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_runner import collect_agent_adapter_state
from .paths import rel
from .state import CompanyPaths, read_json, write_json
from .timeutil import now_iso
from .worker_fleet import ensure_worker_fleet

GPU_BUDGET_GB = 48

USE_CASES: dict[str, dict[str, Any]] = {
    "unity_code": {
        "label": "Unity C# gameplay code",
        "primary": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "fallback": {"runtime": "openclaw", "model": "OpenClaw gateway default", "worker": "mac_studio"},
        "reason": "Code edits need repo context, diff discipline, and test/compile evidence.",
    },
    "game_design": {
        "label": "Game design and mode rules",
        "primary": {"runtime": "hermes", "model": "Hermes Agent default", "worker": "mac_studio"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "Long-form design notes and memory synthesis fit Hermes; Codex remains the implementation fallback.",
    },
    "qa_review": {
        "label": "QA review and risk finding",
        "primary": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "fallback": {"runtime": "agy", "model": "Antigravity default", "worker": "mac_studio"},
        "reason": "Reviews should prioritize code/runtime evidence, with UI/browser review as fallback.",
    },
    "asset_prompt": {
        "label": "Asset prompt and metadata drafting",
        "primary": {"runtime": "hermes", "model": "Hermes Agent default", "worker": "mac_studio"},
        "fallback": {"runtime": "local_ollama", "model": "Ollama local model, model smoke pending", "worker": "mac_studio"},
        "reason": "Asset prompts benefit from memory context; local drafting can be used after model smoke.",
    },
    "blender_python": {
        "label": "Blender Python and technical art",
        "primary": {"runtime": "agy", "model": "Antigravity default", "worker": "mac_studio"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "Technical art tasks often need UI/tool interaction plus script-level edits.",
    },
    "audio_design": {
        "label": "Audio design and sound brief",
        "primary": {"runtime": "hermes", "model": "Hermes Agent default", "worker": "mac_studio"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "Sound direction is mostly brief/synthesis work before asset import.",
    },
    "long_research": {
        "label": "Long research pack",
        "primary": {"runtime": "hermes", "model": "Hermes Agent default", "worker": "mac_studio"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "Hermes is the current long-context/research runtime in this workspace.",
    },
    "gdx_soak": {
        "label": "gdx1 AI ops and long-running worker",
        "primary": {"runtime": "openclaw", "model": "OpenClaw gateway default", "worker": "gdx1"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "gdx1 is ARM/aarch64, so use it for remote AI ops, logs, research, and long-running worker jobs, not Unity x86_64 server execution.",
    },
    "x86_server_soak": {
        "label": "Unity x86_64 server and bot soak",
        "primary": {"runtime": "openclaw", "model": "OpenClaw gateway default", "worker": "x86_linux_runner"},
        "fallback": {"runtime": "codex", "model": "Codex CLI default", "worker": "mac_studio"},
        "reason": "Unity Linux Dedicated Server builds are x86_64; real remote server soak needs an x86_64 Linux runner or cloud host.",
    },
}


def model_cookbook_path(root: Path) -> Path:
    return CompanyPaths(root).memory_dir / "model_cookbook.json"


def ensure_model_cookbook(root: Path) -> dict[str, Any]:
    path = model_cookbook_path(root)
    if not path.exists():
        return refresh_model_cookbook(root)
    data = read_json(path)
    if _needs_refresh(data):
        return refresh_model_cookbook(root)
    return data


def refresh_model_cookbook(root: Path) -> dict[str, Any]:
    workers = ensure_worker_fleet(root)
    adapters = collect_agent_adapter_state(root)
    worker_map = {str(worker.get("id")): worker for worker in workers.get("workers", [])}
    tool_map = adapters.get("tools", {}) if isinstance(adapters.get("tools"), dict) else {}
    data = {
        "version": 1,
        "updated_at": now_iso(),
        "source": {
            "worker_fleet": rel(root, CompanyPaths(root).memory_dir / "worker_fleet.json"),
            "tool_adapters": rel(root, CompanyPaths(root).tool_adapters_json),
        },
        "hardware_profile": _hardware_profile(worker_map),
        "gdx1_probe": _gdx1_probe(worker_map),
        "runtime_status": _runtime_status(tool_map, worker_map),
        "use_cases": [
            _recommendation(use_case, definition, tool_map, worker_map)
            for use_case, definition in USE_CASES.items()
        ],
    }
    data["summary"] = _summary(data["use_cases"])
    write_json(model_cookbook_path(root), data)
    return data


def render_model_cookbook(root: Path, refresh: bool = False) -> str:
    data = refresh_model_cookbook(root) if refresh else ensure_model_cookbook(root)
    hardware = data.get("hardware_profile") or {}
    summary = data.get("summary") or {}
    lines = [
        f"Model Cookbook: {rel(root, model_cookbook_path(root))}",
        f"Updated: {data.get('updated_at') or 'never'}",
        f"Mac: {hardware.get('chip', 'unknown')} / {hardware.get('ram_gb', 'unknown')}GB / {hardware.get('backend', 'unknown')} / GPU budget {hardware.get('gpu_budget_gb', GPU_BUDGET_GB)}GB",
        f"Verified use cases: {summary.get('verified', 0)}/{summary.get('total', 0)}",
        "",
    ]
    for row in data.get("use_cases", []):
        primary = row.get("primary") or {}
        fallback = row.get("fallback") or {}
        lines.extend(
            [
                f"{row.get('use_case'):<15} {row.get('verification_status', 'unknown'):<16} {row.get('label', '')}",
                f"  primary: {primary.get('runtime')} / {primary.get('model')} / {primary.get('worker')} / {primary.get('verification_status')}",
                f"  fallback: {fallback.get('runtime')} / {fallback.get('model')} / {fallback.get('worker')} / {fallback.get('verification_status')}",
                f"  reason: {row.get('reason', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _needs_refresh(data: dict[str, Any]) -> bool:
    use_cases = data.get("use_cases")
    return not isinstance(use_cases, list) or {row.get("use_case") for row in use_cases} != set(USE_CASES)


def _hardware_profile(workers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mac = workers.get("mac_studio", {})
    hardware = mac.get("hardware") if isinstance(mac.get("hardware"), dict) else {}
    return {
        "worker": "mac_studio",
        "machine": hardware.get("machine", "Mac Studio"),
        "chip": hardware.get("chip", "Apple M2 Ultra"),
        "ram_gb": int(hardware.get("ram_gb") or 64),
        "gpu": hardware.get("gpu", "Apple M2 Ultra"),
        "gpu_cores": str(hardware.get("gpu_cores") or ""),
        "backend": hardware.get("backend", "Metal"),
        "gpu_budget_gb": GPU_BUDGET_GB,
        "budget_note": "Keep local model/runtime planning under a 48GB GPU memory budget on the 64GB unified-memory Mac Studio.",
    }


def _gdx1_probe(workers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gdx = workers.get("gdx1", {})
    return {
        "worker": "gdx1",
        "enabled": bool(gdx.get("enabled")),
        "status": str(gdx.get("status") or "unknown"),
        "hardware": gdx.get("hardware") if isinstance(gdx.get("hardware"), dict) else {},
        "last_probe": gdx.get("last_probe") if isinstance(gdx.get("last_probe"), dict) else {},
    }


def _runtime_status(tools: dict[str, Any], workers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for name in ("codex", "agy", "hermes", "openclaw"):
        tool = tools.get(name) if isinstance(tools.get(name), dict) else {}
        status[name] = {
            "kind": "adapter",
            "status": str(tool.get("status") or "missing"),
            "available": bool(tool.get("available") or tool.get("status") == "available"),
            "version": str(tool.get("version") or ""),
            "last_check": str(tool.get("lastCheck") or ""),
        }
    ollama = workers.get("local_ollama", {})
    status["local_ollama"] = {
        "kind": "local_model_runtime",
        "status": str(ollama.get("status") or "unknown"),
        "available": bool(ollama.get("enabled") and ollama.get("status") == "available"),
        "version": str((ollama.get("hardware") or {}).get("version") or ""),
        "last_check": str((ollama.get("last_probe") or {}).get("checked_at") or ""),
        "model_smoke": "pending",
    }
    return status


def _recommendation(
    use_case: str,
    definition: dict[str, Any],
    tools: dict[str, Any],
    workers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    primary = _runtime_entry(definition["primary"], tools, workers)
    fallback = _runtime_entry(definition["fallback"], tools, workers)
    verification_status = _combined_status(primary)
    return {
        "use_case": use_case,
        "label": definition["label"],
        "primary": primary,
        "fallback": fallback,
        "verification_status": verification_status,
        "reason": definition["reason"],
    }


def _runtime_entry(selection: dict[str, str], tools: dict[str, Any], workers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    runtime = selection["runtime"]
    worker_id = selection["worker"]
    worker = workers.get(worker_id, {})
    tool = tools.get(runtime) if isinstance(tools.get(runtime), dict) else {}
    if runtime == "local_ollama":
        ollama = workers.get("local_ollama", {})
        runtime_available = bool(ollama.get("enabled") and ollama.get("status") == "available")
        runtime_status = str(ollama.get("status") or "unknown")
        version = str((ollama.get("hardware") or {}).get("version") or "")
        verification = "model_pending" if runtime_available else "runtime_missing"
        evidence = (ollama.get("last_probe") or {}).get("summary") or version
    else:
        runtime_available = bool(tool.get("available") or tool.get("status") == "available")
        runtime_status = str(tool.get("status") or "missing")
        version = str(tool.get("version") or "")
        verification = "verified" if runtime_available else "runtime_missing"
        evidence = version or str(tool.get("lastError") or "")
    worker_available = bool(worker.get("enabled") and worker.get("status") == "available")
    if not worker_available:
        verification = "worker_blocked"
    return {
        "runtime": runtime,
        "model": selection["model"],
        "worker": worker_id,
        "runtime_status": runtime_status,
        "worker_status": str(worker.get("status") or "unknown"),
        "verification_status": verification,
        "version": version,
        "evidence": evidence,
    }


def _combined_status(primary: dict[str, Any]) -> str:
    return str(primary.get("verification_status") or "unknown")


def _summary(use_cases: list[dict[str, Any]]) -> dict[str, int]:
    rows = {"total": len(use_cases), "verified": 0, "model_pending": 0, "blocked": 0, "runtime_missing": 0}
    for row in use_cases:
        status = str(row.get("verification_status") or "")
        if status == "verified":
            rows["verified"] += 1
        for route_name in ("primary", "fallback"):
            route_status = str((row.get(route_name) or {}).get("verification_status") or "")
            if route_status == "model_pending":
                rows["model_pending"] += 1
            elif route_status == "runtime_missing":
                rows["runtime_missing"] += 1
            elif route_status and route_status != "verified":
                rows["blocked"] += 1
    return rows
