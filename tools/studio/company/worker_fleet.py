"""Worker fleet registry and hardware probes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from .paths import rel
from .state import CompanyPaths, read_json, write_json
from .timeutil import now_iso

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

GDX_HOST = "gdx1"
X86_SIMWORLD_HOST_ENV = "CHANNEL_PLAY_X86_64_SIMWORLD_HOST"

WORKER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "mac_studio": {
        "label": "Mac Studio M2 Ultra",
        "kind": "local_hardware",
        "capabilities": ["unity_editor", "blender", "obs_capture", "metal_gpu", "local_builds", "screenshots"],
        "recommended_jobs": ["unity.compile", "unity.playtest", "unity.build.mac", "unity.build.linuxServer", "capture.screen"],
    },
    "gdx1": {
        "label": "ASUS GX10 gdx1",
        "kind": "remote_hardware",
        "capabilities": ["remote_ai_ops", "long_running_jobs", "log_collection", "linux_aarch64_worker", "repo_sync"],
        "recommended_jobs": ["gdx.probe", "gdx.sync", "gdx.collectLogs", "openclaw.tool.smoke", "research.pack"],
    },
    "x86_linux_runner": {
        "label": "Future x86_64 Linux Runner",
        "kind": "external_hardware",
        "capabilities": ["unity_linux_server", "headless_server", "bot_soak", "server_logs"],
        "recommended_jobs": ["unity.build.linuxServer", "gdx.runServer", "gdx.runBots", "gdx.collectLogs"],
    },
    "x86_64_linux_gpu_worker": {
        "label": "SimWorld x86_64 Linux GPU Worker",
        "kind": "external_hardware",
        "capabilities": ["linux_x86_64_worker", "nvidia_gpu", "docker", "simworld_ue_server", "headless_unreal"],
        "recommended_jobs": ["simworld.workerProbe", "simworld.installBase", "simworld.startServer"],
        "requirements": {
            "host_env": X86_SIMWORLD_HOST_ENV,
            "arch": "x86_64",
            "docker": "required",
            "gpu": "nvidia",
            "server_path": "~/channel_play/tools/simworld/server",
        },
    },
    "local_ollama": {
        "label": "Local Ollama",
        "kind": "local_model_runtime",
        "executable": "ollama",
        "capabilities": ["local_llm", "offline_drafts", "model_smoke"],
        "recommended_jobs": ["model.local.smoke", "qa_review.draft"],
    },
    "hermes": {
        "label": "Hermes",
        "kind": "agent_tool",
        "executable": "hermes",
        "capabilities": ["research", "long_context_notes", "librarian_agent"],
        "recommended_jobs": ["research.pack", "memory.summary", "doc.audit"],
    },
    "openclaw": {
        "label": "OpenClaw",
        "kind": "agent_tool",
        "executable": "openclaw",
        "capabilities": ["gateway_agent", "gdx_ops", "tool_smoke"],
        "recommended_jobs": ["openclaw.tool.smoke", "gdx_ops.review"],
    },
}


def worker_fleet_path(root: Path) -> Path:
    return CompanyPaths(root).memory_dir / "worker_fleet.json"


def ensure_worker_fleet(root: Path) -> dict[str, Any]:
    path = worker_fleet_path(root)
    if not path.exists():
        data = _default_fleet()
        write_json(path, data)
        return data
    data = read_json(path)
    changed = _merge_defaults(data)
    if changed:
        write_json(path, data)
    return data


def probe_worker_fleet(root: Path, runner: CommandRunner | None = None) -> dict[str, Any]:
    run = runner or subprocess.run
    data = ensure_worker_fleet(root)
    workers = {str(worker.get("id")): worker for worker in data.get("workers", [])}
    workers["mac_studio"].update(_probe_mac_studio(run))
    workers["gdx1"].update(_probe_gdx1(root, run))
    workers["x86_64_linux_gpu_worker"].update(_probe_x86_64_simworld_worker(root, run))
    for worker_id in ("local_ollama", "hermes", "openclaw"):
        workers[worker_id].update(_probe_executable(worker_id, run))
    data["updated_at"] = now_iso()
    data["workers"] = [workers[key] for key in WORKER_DEFINITIONS]
    write_json(worker_fleet_path(root), data)
    return data


def render_worker_fleet(root: Path, probe: bool = False) -> str:
    data = probe_worker_fleet(root) if probe else ensure_worker_fleet(root)
    lines = [
        f"Worker Fleet: {rel(root, worker_fleet_path(root))}",
        f"Updated: {data.get('updated_at') or 'never'}",
        "",
    ]
    for worker in data.get("workers", []):
        enabled = "enabled" if worker.get("enabled") else "disabled"
        caps = ", ".join(worker.get("capabilities") or [])
        last_probe = worker.get("last_probe") or {}
        lines.extend(
            [
                f"{worker.get('id'):<14} {enabled:<8} {worker.get('status', 'unknown'):<12} {worker.get('label', '')}",
                f"  capabilities: {caps or 'none'}",
                f"  recommended: {', '.join(worker.get('recommended_jobs') or []) or 'none'}",
                f"  last_probe: {last_probe.get('checked_at') or 'never'} {last_probe.get('summary') or ''}".rstrip(),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _default_fleet() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": "",
        "workers": [
            {
                "id": worker_id,
                "label": definition["label"],
                "kind": definition["kind"],
                "enabled": worker_id == "mac_studio",
                "status": "unknown" if worker_id == "mac_studio" else "unprobed",
                "capabilities": list(definition["capabilities"]),
                "recommended_jobs": list(definition["recommended_jobs"]),
                "last_probe": {},
            }
            for worker_id, definition in WORKER_DEFINITIONS.items()
        ],
    }


def _merge_defaults(data: dict[str, Any]) -> bool:
    changed = False
    data.setdefault("version", 1)
    data.setdefault("updated_at", "")
    existing = {str(worker.get("id")): worker for worker in data.setdefault("workers", []) if isinstance(worker, dict)}
    for worker_id, definition in WORKER_DEFINITIONS.items():
        worker = existing.get(worker_id)
        if not worker:
            worker = {
                "id": worker_id,
                "enabled": worker_id == "mac_studio",
                "status": "unknown" if worker_id == "mac_studio" else "unprobed",
                "last_probe": {},
            }
            data["workers"].append(worker)
            existing[worker_id] = worker
            changed = True
        for key in ("label", "kind", "capabilities", "recommended_jobs", "requirements"):
            if key not in definition:
                continue
            desired = list(definition[key]) if isinstance(definition[key], list) else definition[key]
            if worker.get(key) != desired:
                worker[key] = desired
                changed = True
    data["workers"] = [existing[key] for key in WORKER_DEFINITIONS]
    return changed


def _probe_mac_studio(run: CommandRunner) -> dict[str, Any]:
    hardware = _system_profiler(run)
    memsize = _run_stdout(run, ["sysctl", "-n", "hw.memsize"], timeout=5)
    chip = _run_stdout(run, ["sysctl", "-n", "machdep.cpu.brand_string"], timeout=5)
    ram_gb = _bytes_to_gb(memsize)
    displays = hardware.get("SPDisplaysDataType") or []
    gpu = displays[0] if displays and isinstance(displays[0], dict) else {}
    hw_rows = hardware.get("SPHardwareDataType") or []
    hw = hw_rows[0] if hw_rows and isinstance(hw_rows[0], dict) else {}
    machine = str(hw.get("machine_name") or "Mac Studio")
    chip_text = str(hw.get("chip_type") or chip or "Apple Silicon")
    metal = str(gpu.get("spdisplays_mtlgpufamilysupport") or "")
    gpu_model = str(gpu.get("sppci_model") or gpu.get("_name") or chip_text)
    gpu_cores = str(gpu.get("sppci_cores") or "")
    return {
        "enabled": True,
        "status": "available",
        "hardware": {
            "machine": machine,
            "chip": chip_text,
            "ram_gb": ram_gb,
            "gpu": gpu_model,
            "gpu_cores": gpu_cores,
            "backend": "Metal" if metal else "Apple Silicon",
            "metal": metal or "unknown",
        },
        "last_probe": {
            "checked_at": now_iso(),
            "summary": f"{machine} / {chip_text} / {ram_gb}GB RAM / {gpu_model}",
        },
    }


def _probe_gdx1(root: Path, run: CommandRunner) -> dict[str, Any]:
    ssh = run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", GDX_HOST, "hostname; uname -sm"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    ssh_ok = ssh.returncode == 0
    status = "available" if ssh_ok else "blocked"
    details = ssh.stdout.strip() if ssh_ok else ssh.stderr.strip()
    return {
        "enabled": ssh_ok,
        "status": status,
        "hardware": {
            "host": GDX_HOST,
            "remote": details,
            "ssh": "ok" if ssh_ok else "failed",
        },
        "last_probe": {
            "checked_at": now_iso(),
            "exit": ssh.returncode,
            "summary": "SSH ok" if ssh_ok else "SSH blocked",
            "stdout": ssh.stdout.strip(),
            "stderr": ssh.stderr.strip(),
        },
    }


def _probe_x86_64_simworld_worker(root: Path, run: CommandRunner) -> dict[str, Any]:
    host = os.environ.get(X86_SIMWORLD_HOST_ENV, "").strip()
    if not host:
        return {
            "enabled": False,
            "status": "needs_config",
            "hardware": {"host_env": X86_SIMWORLD_HOST_ENV, "host": ""},
            "last_probe": {
                "checked_at": now_iso(),
                "summary": f"{X86_SIMWORLD_HOST_ENV} not set",
            },
        }

    script = (
        "echo host=$(hostname); "
        "echo arch=$(uname -m); "
        "if command -v docker >/dev/null 2>&1; then echo docker=yes; else echo docker=no; fi; "
        "if command -v nvidia-smi >/dev/null 2>&1; then echo gpu_count=$(nvidia-smi -L | wc -l | tr -d ' '); else echo gpu_count=0; fi; "
        "if test -x ~/channel_play/tools/simworld/server; then echo simworld_server=yes; else echo simworld_server=no; fi"
    )
    probe = run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", host, script],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    facts = _parse_probe_facts(probe.stdout)
    arch_ok = facts.get("arch") in {"x86_64", "amd64"}
    docker_ok = facts.get("docker") == "yes"
    gpu_count = _safe_int(facts.get("gpu_count"))
    server_ok = facts.get("simworld_server") == "yes"
    if probe.returncode != 0:
        status = "blocked"
    elif not (arch_ok and docker_ok and gpu_count > 0):
        status = "blocked"
    elif not server_ok:
        status = "needs_simworld_install"
    else:
        status = "available"

    return {
        "enabled": status == "available",
        "status": status,
        "hardware": {
            "host_env": X86_SIMWORLD_HOST_ENV,
            "host": host,
            **facts,
        },
        "last_probe": {
            "checked_at": now_iso(),
            "exit": probe.returncode,
            "summary": _x86_probe_summary(status, host, facts),
            "stdout": probe.stdout.strip(),
            "stderr": probe.stderr.strip(),
        },
    }


def _probe_executable(worker_id: str, run: CommandRunner) -> dict[str, Any]:
    executable = str(WORKER_DEFINITIONS[worker_id].get("executable") or worker_id)
    path = shutil.which(executable) or ""
    if not path:
        return {
            "enabled": False,
            "status": "missing",
            "hardware": {"executable": executable, "resolved_path": ""},
            "last_probe": {"checked_at": now_iso(), "summary": f"missing executable: {executable}"},
        }
    version = _version_for(executable, run)
    return {
        "enabled": True,
        "status": "available",
        "hardware": {"executable": executable, "resolved_path": path, "version": version},
        "last_probe": {"checked_at": now_iso(), "summary": version or f"{executable} available"},
    }


def _system_profiler(run: CommandRunner) -> dict[str, Any]:
    result = run(
        ["system_profiler", "SPHardwareDataType", "SPDisplaysDataType", "-json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def _run_stdout(run: CommandRunner, command: list[str], timeout: int) -> str:
    result = run(command, capture_output=True, text=True, check=False, timeout=timeout)
    return result.stdout.strip() if result.returncode == 0 else ""


def _parse_probe_facts(text: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        facts[key.strip()] = value.strip()
    return facts


def _x86_probe_summary(status: str, host: str, facts: dict[str, str]) -> str:
    return (
        f"{host} {status}: arch={facts.get('arch', 'unknown')} "
        f"docker={facts.get('docker', 'unknown')} gpu_count={facts.get('gpu_count', '0')} "
        f"simworld_server={facts.get('simworld_server', 'unknown')}"
    )


def _safe_int(value: str | None) -> int:
    try:
        return int(value or "0")
    except ValueError:
        return 0


def _version_for(executable: str, run: CommandRunner) -> str:
    command = [executable, "--version"]
    result = run(command, capture_output=True, text=True, check=False, timeout=8)
    if result.returncode != 0 and executable == "ollama":
        result = run([executable, "-v"], capture_output=True, text=True, check=False, timeout=8)
    return (result.stdout or result.stderr).strip().splitlines()[0] if result.returncode == 0 else ""


def _bytes_to_gb(value: str) -> int:
    try:
        return round(int(value) / (1024**3))
    except (TypeError, ValueError):
        return 0
