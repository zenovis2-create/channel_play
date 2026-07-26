"""gdx1 worker probes."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from shlex import quote

from .paths import rel
from .state import load_state_json, save_state_json

from .timeutil import now_iso, slugify
from .worker_fleet import ensure_worker_fleet

GDX_HOST = "gdx1"
GDX_WORKSPACE = "~/channel_play"
LINUX_SERVER_BUILD = "builds/linux-server/channel_play_server"
SIMWORLD_CANDIDATES = (
    "~/channel_play/tools/simworld/server",
    "~/channel_play/simworld/server",
    "/opt/simworld/server",
    "simworld",
)


def gdx_probe(root: Path) -> Path:
    run_dir = root / "runs" / f"gdx-probe-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "gdx_probe.md"
    ssh = _ssh("hostname", root, timeout=8)
    workspace = None
    if ssh.returncode == 0:
        workspace = _ssh(f"test -d {GDX_WORKSPACE}/.git && echo git-workspace || test -d {GDX_WORKSPACE} && echo plain-workspace || echo missing", root, timeout=8)
    tailscale = subprocess.run(
        ["tailscale", "status", "--peers=false"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=8,
    )
    path.write_text(
        "\n".join(
            [
                "# gdx1 Probe",
                "",
                f"Checked: {now_iso()}",
                f"SSH exit: {ssh.returncode}",
                f"SSH stdout: {ssh.stdout.strip() or 'none'}",
                f"SSH stderr: {ssh.stderr.strip() or 'none'}",
                f"Remote workspace: {_workspace_result(workspace)}",
                f"Tailscale exit: {tailscale.returncode}",
                "",
                "## Result",
                "",
                "usable" if ssh.returncode == 0 else "blocked: SSH authentication or host access failed",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _update_gdx_state(root, ssh.returncode == 0)
    return path


def _workspace_result(result: subprocess.CompletedProcess[str] | None) -> str:
    if result is None:
        return "not checked: ssh blocked"
    return result.stdout.strip() or f"check failed exit={result.returncode}"


def gdx_sync(root: Path) -> Path:
    origin = _origin_url(root)
    command = (
        "set -eu; "
        f"if [ ! -d {GDX_WORKSPACE}/.git ]; then "
        f"rm -rf {GDX_WORKSPACE}; git clone {quote(origin)} {GDX_WORKSPACE}; "
        f"else git -C {GDX_WORKSPACE} fetch origin main; git -C {GDX_WORKSPACE} checkout main; git -C {GDX_WORKSPACE} pull --ff-only; fi; "
        f"git -C {GDX_WORKSPACE} rev-parse --short HEAD"
    )
    return _remote_action(root, "sync", command, timeout=120)


def gdx_run_server(root: Path) -> Path:
    preflight = _deploy_linux_server_build(root)
    command = (
        f"set -eu; cd {GDX_WORKSPACE}; "
        "mkdir -p runs logs; "
        "server='builds/linux-server/channel_play_server'; "
        "if [ -x scripts/gdx1_run_server.sh ]; then ./scripts/gdx1_run_server.sh; "
        "elif [ -x \"$server\" ]; then "
        "arch=$(uname -m); desc=$(file \"$server\" 2>/dev/null || true); "
        "if echo \"$desc\" | grep -qi 'x86-64' && [ \"$arch\" != 'x86_64' ]; then echo \"blocked: architecture mismatch remote=$arch build=x86-64\"; echo \"$desc\"; exit 5; fi; "
        "if [ -f runs/gdx-server.pid ] && kill -0 \"$(cat runs/gdx-server.pid)\" 2>/dev/null; then echo \"server already running pid=$(cat runs/gdx-server.pid)\"; exit 0; fi; "
        "nohup \"$server\" -batchmode -nographics -logFile logs/gdx-server.log > logs/gdx-server.stdout.log 2>&1 & "
        "pid=$!; echo \"$pid\" > runs/gdx-server.pid; sleep 5; "
        "if kill -0 \"$pid\" 2>/dev/null; then echo \"server started pid=$pid\"; tail -n 40 logs/gdx-server.log 2>/dev/null || true; "
        "else echo 'blocked: server exited during startup'; tail -n 80 logs/gdx-server.log 2>/dev/null || true; exit 4; fi; "
        "else echo 'blocked: no gdx1 server runner or Linux server build found'; exit 3; fi"
    )
    return _remote_action(root, "run-server", command, timeout=90, preflight=preflight)


def gdx_run_bots(root: Path) -> Path:
    command = (
        f"set -eu; cd {GDX_WORKSPACE}; "
        "mkdir -p runs logs; "
        "if [ -x scripts/gdx1_run_bots.sh ]; then ./scripts/gdx1_run_bots.sh; "
        "elif [ -f runs/gdx-server.pid ] && kill -0 \"$(cat runs/gdx-server.pid)\" 2>/dev/null; then "
        "echo \"server-smoke ok pid=$(cat runs/gdx-server.pid)\"; "
        "tail -n 40 logs/gdx-server.log 2>/dev/null || true; "
        "else echo 'blocked: no gdx1 bot runner found'; exit 3; fi"
    )
    return _remote_action(root, "run-bots", command, timeout=60)


def gdx_collect_logs(root: Path) -> Path:
    command = (
        f"set -eu; cd {GDX_WORKSPACE}; "
        "if [ -d runs ] || [ -d logs ]; then tar -czf /tmp/channel_play_gdx_logs.tgz runs logs 2>/dev/null || true; echo /tmp/channel_play_gdx_logs.tgz; "
        "else echo 'no remote runs/logs directories yet'; fi"
    )
    path = _remote_action(root, "collect-logs", command, timeout=60)
    archive = path.parent / "channel_play_gdx_logs.tgz"
    subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", f"{GDX_HOST}:/tmp/channel_play_gdx_logs.tgz", str(archive)], cwd=root, capture_output=True, text=True, check=False, timeout=30)
    return path


def gdx_simworld_probe(root: Path) -> Path:
    run_dir = root / "runs" / f"simworld-probe-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = run_dir / "receipt.md"
    remote_probe = _simworld_remote_probe_command()
    ssh_result = _safe_ssh(remote_probe, root, timeout=20)
    tailscale = _safe_local(["tailscale", "status", "--peers=false"], root, timeout=8)
    facts = _parse_probe_facts(ssh_result.stdout if ssh_result else "")
    failures = _simworld_failures(ssh_result, facts)
    status = "simworld_probe_ready" if not failures else "simworld_probe_blocked"
    server_start = "skipped_incompatible" if failures else "ready_not_started"
    failure_lines = [f"- {failure}" for failure in failures] if failures else ["none"]

    (run_dir / "remote_stdout.txt").write_text((ssh_result.stdout if ssh_result else "") or "none\n", encoding="utf-8", errors="ignore")
    (run_dir / "remote_stderr.txt").write_text((ssh_result.stderr if ssh_result else "") or "none\n", encoding="utf-8", errors="ignore")
    (run_dir / "tailscale_stdout.txt").write_text((tailscale.stdout if tailscale else "") or "none\n", encoding="utf-8", errors="ignore")
    (run_dir / "tailscale_stderr.txt").write_text((tailscale.stderr if tailscale else "") or "none\n", encoding="utf-8", errors="ignore")

    receipt.write_text(
        "\n".join(
            [
                "# gdx1 SimWorld Probe",
                "",
                f"Checked: {now_iso()}",
                f"Status: `{status}`",
                f"Host: `{GDX_HOST}`",
                f"SSH exit: `{ssh_result.returncode if ssh_result else 'timeout'}`",
                f"Tailscale exit: `{tailscale.returncode if tailscale else 'missing'}`",
                f"Server start: `{server_start}`",
                "",
                "## Remote Facts",
                "",
                *[f"- {key}: `{value}`" for key, value in sorted(facts.items())],
                "",
                "## Failures",
                "",
                *failure_lines,
                "",
                "## Artifacts",
                "",
                f"- `{(run_dir / 'remote_stdout.txt').relative_to(root)}`",
                f"- `{(run_dir / 'remote_stderr.txt').relative_to(root)}`",
                f"- `{(run_dir / 'tailscale_stdout.txt').relative_to(root)}`",
                f"- `{(run_dir / 'tailscale_stderr.txt').relative_to(root)}`",
                "",
                "## Fallback Rule",
                "",
                "Unity local agent-playtest must remain runnable even when this probe is blocked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _update_gdx_simworld_state(root, status, failures, receipt)
    return receipt


def gdx_simworld_doctor(root: Path) -> Path:
    run_dir = root / "runs" / f"simworld-doctor-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = run_dir / "receipt.md"
    report_path = run_dir / "doctor.json"
    ssh_result = _safe_ssh(_simworld_doctor_remote_command(), root, timeout=30)
    facts = _parse_probe_facts(ssh_result.stdout if ssh_result else "")
    failures = _simworld_failures(ssh_result, facts)
    actions = _simworld_doctor_actions(facts, failures)
    status = "simworld_doctor_ready" if not failures else "simworld_doctor_blocked"

    report = {
        "schema": "channel_play.gdx1_simworld_doctor.v1",
        "checkedAt": now_iso(),
        "status": status,
        "host": GDX_HOST,
        "sshExit": ssh_result.returncode if ssh_result else None,
        "facts": facts,
        "failures": failures,
        "recommendedActions": actions,
        "artifacts": {
            "remoteStdout": rel(root, run_dir / "remote_stdout.txt"),
            "remoteStderr": rel(root, run_dir / "remote_stderr.txt"),
            "report": rel(root, report_path),
        },
    }
    (run_dir / "remote_stdout.txt").write_text((ssh_result.stdout if ssh_result else "") or "none\n", encoding="utf-8", errors="ignore")
    (run_dir / "remote_stderr.txt").write_text((ssh_result.stderr if ssh_result else "") or "none\n", encoding="utf-8", errors="ignore")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_simworld_doctor_receipt(root, report, report_path), encoding="utf-8")
    _update_gdx_simworld_state(root, status, failures, receipt)
    return receipt


def gdx_simworld_install_base(root: Path, args: list[str]) -> Path:
    dry_run = "--dry-run" in args
    run_dir = root / "runs" / f"simworld-install-base-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = run_dir / "receipt.md"
    report_path = run_dir / "install_base.json"
    result = _safe_ssh(_simworld_install_base_remote_command(dry_run=dry_run), root, timeout=60 if dry_run else 7200)
    facts = _parse_probe_facts(result.stdout if result else "")
    failures = _simworld_install_failures(result, facts, dry_run=dry_run)
    status = "simworld_install_plan_ready" if dry_run and not failures else "simworld_install_ready" if not failures else "simworld_install_blocked"
    report = {
        "schema": "channel_play.gdx1_simworld_install_base.v1",
        "checkedAt": now_iso(),
        "status": status,
        "dryRun": dry_run,
        "host": GDX_HOST,
        "sshExit": result.returncode if result else None,
        "facts": facts,
        "failures": failures,
        "artifacts": {
            "remoteStdout": rel(root, run_dir / "remote_stdout.txt"),
            "remoteStderr": rel(root, run_dir / "remote_stderr.txt"),
            "report": rel(root, report_path),
        },
    }
    (run_dir / "remote_stdout.txt").write_text((result.stdout if result else "") or "none\n", encoding="utf-8", errors="ignore")
    (run_dir / "remote_stderr.txt").write_text((result.stderr if result else "") or "none\n", encoding="utf-8", errors="ignore")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_simworld_install_base_receipt(root, report, report_path), encoding="utf-8")
    return receipt


def gdx_simworld_route_plan(root: Path) -> Path:
    run_dir = root / "runs" / f"simworld-route-plan-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = run_dir / "receipt.md"
    plan_path = run_dir / "route_plan.json"
    doctor = _latest_run(root, "simworld-doctor-")
    probe = _latest_run(root, "simworld-probe-")
    acceptance = _latest_run(root, "sim-acceptance-")
    live_check = _latest_run(root, "external-agent-live-check-")
    doctor_report = _read_json(doctor / "doctor.json", default={}) if doctor else {}
    facts = doctor_report.get("facts") if isinstance(doctor_report.get("facts"), dict) else {}
    failures = doctor_report.get("failures") if isinstance(doctor_report.get("failures"), list) else []
    arch_mismatch = any("x86-64" in str(item) and "aarch64" in str(item) for item in failures)
    worker_fleet = ensure_worker_fleet(root)
    x86_worker = _fleet_worker(worker_fleet, "x86_64_linux_gpu_worker")
    x86_status = str(x86_worker.get("status") or "unprobed")
    x86_ready = x86_status == "available"
    x86_host = str((x86_worker.get("hardware") or {}).get("host") or "")

    routes = {
        "unityRuntime": {
            "worker": "mac_studio_local",
            "status": "ready" if _receipt_has(acceptance, "sim_acceptance_passed") else "needs_acceptance",
            "reason": "Unity-first simulation is the validated runtime surface.",
            "evidence": _latest_receipt(root, "sim-acceptance-"),
        },
        "assetAiGpu": {
            "worker": "gdx1",
            "status": "ready" if facts.get("docker_usable") == "yes" and int(facts.get("gpu_count", "0") or "0") > 0 else "blocked",
            "reason": "gdx1 has Docker access and NVIDIA GPU evidence.",
            "evidence": _latest_receipt(root, "simworld-doctor-"),
        },
        "externalAiBridge": {
            "worker": "mac_studio_local",
            "status": "ready" if _receipt_has(live_check, "external_agent_live_check_passed") else "blocked",
            "reason": "Codex/OpenClaw live bridge runs through the local Studio command layer.",
            "evidence": _latest_receipt(root, "external-agent-live-check-"),
        },
        "simworldUeServer": {
            "worker": "x86_64_linux_gpu_worker",
            "status": "ready" if x86_ready else "needs_worker" if arch_mismatch else "blocked",
            "reason": _simworld_ue_route_reason(arch_mismatch, x86_status, x86_host),
            "evidence": rel(root, root / "memory/company/worker_fleet.json"),
        },
    }
    plan = {
        "schema": "channel_play.worker_route_plan.v1",
        "createdAt": now_iso(),
        "status": "worker_route_plan_ready",
        "facts": {
            "gdx1Arch": facts.get("arch", "unknown"),
            "gdx1DockerUsable": facts.get("docker_usable", "unknown"),
            "gdx1GpuCount": facts.get("gpu_count", "0"),
            "simworldBinaryFile": facts.get("simworld_binary_file", "unknown"),
            "x86SimWorldWorkerStatus": x86_status,
            "x86SimWorldWorkerHost": x86_host or "not_configured",
        },
        "routes": routes,
        "blocked": [
            {
                "id": "simworld_ue_gdx1_arch_mismatch",
                "status": "needs_x86_64_worker",
                "reason": "gdx1 cannot be treated as the official SimWorld UE server host until an aarch64 build or validated x86_64 execution path exists.",
                "evidence": _latest_receipt(root, "simworld-doctor-"),
            }
        ]
        if arch_mismatch
        else [],
        "nextCommands": [
            "tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted",
            "tools/channelctl sim-agent live-check all runs/agent-playtest-pyramid-maze-v2-scripted-2026-06-07t15-21-50-09-00 --timeout 240",
            "tools/channelctl simworld doctor",
            "CHANNEL_PLAY_X86_64_SIMWORLD_HOST=<ssh-host> tools/channelctl company workers --probe",
            "tools/channelctl simworld route-plan",
        ],
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_simworld_route_plan_receipt(root, plan, plan_path), encoding="utf-8")
    return receipt


def _fleet_worker(fleet: dict, worker_id: str) -> dict:
    for worker in fleet.get("workers", []):
        if isinstance(worker, dict) and worker.get("id") == worker_id:
            return worker
    return {}


def _simworld_ue_route_reason(arch_mismatch: bool, x86_status: str, x86_host: str) -> str:
    if x86_status == "available":
        return f"Compatible x86_64 SimWorld worker is available at {x86_host}."
    if x86_status == "needs_config":
        return "Official SimWorld Linux UE package is x86-64; set CHANNEL_PLAY_X86_64_SIMWORLD_HOST and probe the worker."
    if x86_status == "needs_simworld_install":
        return "x86_64 worker is reachable, but SimWorld server package is not installed at ~/channel_play/tools/simworld/server."
    if arch_mismatch:
        return "Official SimWorld Linux UE package is x86-64; gdx1 reports aarch64."
    return f"SimWorld UE worker is not ready: x86_64_linux_gpu_worker status={x86_status}."


def gdx_simworld_start_server(root: Path) -> Path:
    route_receipt = gdx_simworld_route_plan(root)
    route_plan_path = route_receipt.parent / "route_plan.json"
    route_plan = _read_json(route_plan_path, default={})
    simworld_route = {}
    if isinstance(route_plan.get("routes"), dict):
        simworld_route = route_plan["routes"].get("simworldUeServer", {})
    run_dir = root / "runs" / f"simworld-start-server-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "start_server.json"
    receipt = run_dir / "receipt.md"
    route_status = simworld_route.get("status", "unknown")
    can_start = route_status == "ready"
    report = {
        "schema": "channel_play.gdx1_simworld_start_server.v1",
        "checkedAt": now_iso(),
        "status": "simworld_start_ready" if can_start else "simworld_start_blocked",
        "routePlan": rel(root, route_plan_path),
        "routePlanReceipt": rel(root, route_receipt),
        "targetWorker": simworld_route.get("worker", "unknown"),
        "routeStatus": route_status,
        "reason": simworld_route.get("reason", "missing route-plan evidence"),
        "evidence": simworld_route.get("evidence", ""),
        "action": "not_started" if not can_start else "start_not_implemented_for_unconfigured_worker",
        "next": "Add an x86_64 Linux GPU worker or obtain an aarch64 SimWorld UE server package before starting SimWorld UE.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_simworld_start_server_receipt(root, report, report_path), encoding="utf-8")
    return receipt


def gdx_simworld_worker_guide(root: Path) -> Path:
    run_dir = root / "runs" / f"simworld-worker-guide-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = run_dir / "receipt.md"
    guide_path = run_dir / "guide.md"
    report_path = run_dir / "worker_guide.json"
    worker_fleet = ensure_worker_fleet(root)
    worker = _fleet_worker(worker_fleet, "x86_64_linux_gpu_worker")
    hardware = worker.get("hardware") if isinstance(worker.get("hardware"), dict) else {}
    requirements = worker.get("requirements") if isinstance(worker.get("requirements"), dict) else {}
    report = {
        "schema": "channel_play.simworld_worker_guide.v1",
        "createdAt": now_iso(),
        "status": "simworld_worker_guide_ready",
        "worker": {
            "id": "x86_64_linux_gpu_worker",
            "status": str(worker.get("status") or "unprobed"),
            "enabled": bool(worker.get("enabled")),
            "host": str(hardware.get("host") or ""),
            "hostEnv": str(requirements.get("host_env") or "CHANNEL_PLAY_X86_64_SIMWORLD_HOST"),
            "requirements": requirements,
            "lastProbe": worker.get("last_probe") or {},
        },
        "routePlanReceipt": _latest_receipt(root, "simworld-route-plan-"),
        "commands": [
            "export CHANNEL_PLAY_X86_64_SIMWORLD_HOST=<ssh-host>",
            "tools/channelctl company workers --probe",
            "tools/channelctl simworld route-plan",
            "tools/channelctl simworld start-server",
        ],
        "artifacts": {
            "guide": rel(root, guide_path),
            "report": rel(root, report_path),
            "workerFleet": "memory/company/worker_fleet.json",
        },
    }
    guide_path.write_text(_simworld_worker_guide_markdown(report), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_simworld_worker_guide_receipt(root, report, report_path), encoding="utf-8")
    return receipt


def _blocked_action(root: Path, action: str, reason: str) -> Path:
    run_dir = root / "runs" / f"gdx-{action}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"gdx_{action}.md"
    path.write_text(
        "\n".join(
            [
                f"# gdx1 {action}",
                "",
                f"Checked: {now_iso()}",
                "Status: blocked",
                f"Reason: {reason}",
                "",
                "Next: register Mac Studio SSH key on gdx1 or enable Tailscale SSH.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _remote_action(root: Path, action: str, command: str, timeout: int, preflight: list[str] | None = None) -> Path:
    run_dir = root / "runs" / f"gdx-{action}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"gdx_{action}.md"
    result = _ssh(command, root, timeout=timeout)
    status = "ok" if result.returncode == 0 else "blocked"
    path.write_text(
        "\n".join(
            [
                f"# gdx1 {action}",
                "",
                f"Checked: {now_iso()}",
                f"Status: {status}",
                f"Exit: {result.returncode}",
                "",
                "## preflight",
                "",
                *(preflight or ["none"]),
                "",
                "## stdout",
                "",
                result.stdout.strip() or "none",
                "",
                "## stderr",
                "",
                result.stderr.strip() or "none",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _update_gdx_state(root, result.returncode == 0 or "no gdx1" not in result.stderr.lower())
    return path


def _deploy_linux_server_build(root: Path) -> list[str]:
    local_build = root / LINUX_SERVER_BUILD
    if not local_build.exists():
        return [f"local build missing: {LINUX_SERVER_BUILD}"]
    mkdir = _ssh(f"mkdir -p {GDX_WORKSPACE}/builds/linux-server", root, timeout=15)
    remote_arch = _ssh("uname -m", root, timeout=8)
    if mkdir.returncode != 0:
        return [f"remote mkdir failed exit={mkdir.returncode}", mkdir.stderr.strip() or "no stderr"]
    remote_target = f"{GDX_HOST}:{GDX_WORKSPACE}/builds/linux-server/channel_play_server"
    copy = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", str(local_build), remote_target],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    chmod = _ssh(f"chmod +x {GDX_WORKSPACE}/builds/linux-server/channel_play_server", root, timeout=15) if copy.returncode == 0 else None
    return [
        f"local build: {LINUX_SERVER_BUILD}",
        f"remote target: {remote_target}",
        f"remote arch: {remote_arch.stdout.strip() if remote_arch.returncode == 0 else 'unknown'}",
        f"scp exit: {copy.returncode}",
        f"scp stderr: {copy.stderr.strip() or 'none'}",
        f"chmod exit: {chmod.returncode if chmod else 'skipped'}",
        f"chmod stderr: {(chmod.stderr.strip() if chmod else '') or 'none'}",
    ]


def _ssh(command: str, root: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", GDX_HOST, command],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _safe_ssh(command: str, root: Path, timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return _ssh(command, root, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def _safe_local(command: list[str], root: Path, timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _simworld_remote_probe_command() -> str:
    candidate_checks = " ".join(quote(candidate) for candidate in SIMWORLD_CANDIDATES)
    return (
        "set +e; "
        "echo host=$(hostname 2>/dev/null); "
        "echo user=$(whoami 2>/dev/null); "
        "echo arch=$(uname -m 2>/dev/null); "
        "echo kernel=$(uname -sr 2>/dev/null | tr ' ' '_'); "
        f"test -d {GDX_WORKSPACE} && echo workspace_present=yes || echo workspace_present=no; "
        f"test -d {GDX_WORKSPACE}/.git && echo workspace_git=yes || echo workspace_git=no; "
        "command -v docker >/dev/null 2>&1 && echo docker_present=yes || echo docker_present=no; "
        "docker --version 2>/dev/null | sed 's/^/docker_version=/'; "
        "docker info >/dev/null 2>&1 && echo docker_usable=yes || echo docker_usable=no; "
        "command -v nvidia-smi >/dev/null 2>&1 && echo nvidia_smi_present=yes || echo nvidia_smi_present=no; "
        "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -n 3 | sed 's/^/gpu=/'; "
        "for candidate in " + candidate_checks + "; do "
        "expanded=$(eval echo \"$candidate\"); "
        "if command -v \"$candidate\" >/dev/null 2>&1 || test -x \"$expanded\"; then echo simworld_candidate=$expanded; fi; "
        "done; "
        "simworld_binary=$(find $HOME/channel_play/tools/simworld/base_linux $HOME/channel_play/simworld /opt/simworld -path '*/SimWorld/Binaries/Linux/SimWorld' -type f 2>/dev/null | head -n 1); "
        "echo simworld_binary=$simworld_binary; "
        "if [ -n \"$simworld_binary\" ]; then file \"$simworld_binary\" | sed 's/^/simworld_binary_file=/'; fi; "
        "echo probe_done=yes"
    )


def _simworld_doctor_remote_command() -> str:
    candidate_checks = " ".join(quote(candidate) for candidate in SIMWORLD_CANDIDATES)
    return (
        "set +e; "
        "echo host=$(hostname 2>/dev/null); "
        "echo user=$(whoami 2>/dev/null); "
        "echo uid=$(id -u 2>/dev/null); "
        "echo groups=$(id -nG 2>/dev/null | tr ' ' ','); "
        "echo arch=$(uname -m 2>/dev/null); "
        "echo kernel=$(uname -sr 2>/dev/null | tr ' ' '_'); "
        f"test -d {GDX_WORKSPACE} && echo workspace_present=yes || echo workspace_present=no; "
        f"test -d {GDX_WORKSPACE}/.git && echo workspace_git=yes || echo workspace_git=no; "
        "command -v docker >/dev/null 2>&1 && echo docker_present=yes || echo docker_present=no; "
        "docker --version 2>/dev/null | sed 's/^/docker_version=/'; "
        "docker info >/dev/null 2>&1 && echo docker_usable=yes || echo docker_usable=no; "
        "test -S /var/run/docker.sock && echo docker_socket=yes || echo docker_socket=no; "
        "ls -l /var/run/docker.sock 2>/dev/null | sed 's/^/docker_socket_ls=/'; "
        "getent group docker 2>/dev/null | awk -F: '{print \"docker_group_members=\"$4}'; "
        "systemctl is-active docker 2>/dev/null | sed 's/^/docker_service=/'; "
        "sudo -n docker info >/dev/null 2>&1 && echo sudo_docker_usable=yes || echo sudo_docker_usable=no; "
        "command -v nvidia-smi >/dev/null 2>&1 && echo nvidia_smi_present=yes || echo nvidia_smi_present=no; "
        "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -n 3 | sed 's/^/gpu=/'; "
        "for candidate in " + candidate_checks + "; do "
        "expanded=$(eval echo \"$candidate\"); "
        "if command -v \"$candidate\" >/dev/null 2>&1 || test -x \"$expanded\"; then echo simworld_candidate=$expanded; fi; "
        "done; "
        "simworld_binary=$(find $HOME/channel_play/tools/simworld/base_linux $HOME/channel_play/simworld /opt/simworld -path '*/SimWorld/Binaries/Linux/SimWorld' -type f 2>/dev/null | head -n 1); "
        "echo simworld_binary=$simworld_binary; "
        "if [ -n \"$simworld_binary\" ]; then file \"$simworld_binary\" | sed 's/^/simworld_binary_file=/'; fi; "
        "echo doctor_done=yes"
    )


def _simworld_install_base_remote_command(*, dry_run: bool) -> str:
    mode = "yes" if dry_run else "no"
    return (
        "set +e; "
        "HF=/home/daehan/.local/bin/hf; "
        "install_dir=$HOME/channel_play/tools/simworld; "
        "download_dir=$install_dir/download; "
        "base_dir=$install_dir/base_linux; "
        "mkdir -p \"$install_dir\" \"$download_dir\"; "
        "echo host=$(hostname 2>/dev/null); "
        "echo user=$(whoami 2>/dev/null); "
        "echo dry_run=" + mode + "; "
        "echo install_dir=$install_dir; "
        "echo download_dir=$download_dir; "
        "echo base_dir=$base_dir; "
        "command -v unzip >/dev/null 2>&1 && echo unzip_present=yes || echo unzip_present=no; "
        "test -x \"$HF\" && echo hf_present=yes || echo hf_present=no; "
        "dry_json=$($HF download SimWorld-AI/SimWorld Base20260201/Linux.zip --repo-type dataset --dry-run --json 2>/tmp/channel_play_simworld_hf_dry.err); "
        "echo hf_dry_run_exit=$?; "
        "echo hf_dry_run_json=$dry_json; "
        "python3 - \"$dry_json\" <<'PY' 2>/dev/null\n"
        "import json, sys\n"
        "try:\n"
        "    data=json.loads(sys.argv[1])\n"
        "    print('package_size=' + str(data[0].get('size', 'unknown')))\n"
        "except Exception:\n"
        "    print('package_size=unknown')\n"
        "PY\n"
        "if [ \"" + mode + "\" = yes ]; then echo install_done=dry_run; exit 0; fi; "
        "$HF download SimWorld-AI/SimWorld Base20260201/Linux.zip --repo-type dataset --local-dir \"$download_dir\" --max-workers 4 --quiet; "
        "echo download_exit=$?; "
        "zip_path=$download_dir/Base20260201/Linux.zip; "
        "echo zip_path=$zip_path; "
        "test -s \"$zip_path\" && echo zip_present=yes || echo zip_present=no; "
        "rm -rf \"$base_dir\"; mkdir -p \"$base_dir\"; "
        "unzip -q \"$zip_path\" -d \"$base_dir\"; "
        "echo unzip_exit=$?; "
        "simworld_sh=$(find \"$base_dir\" -name SimWorld.sh -type f | head -n 1); "
        "echo simworld_sh=$simworld_sh; "
        "if [ -n \"$simworld_sh\" ]; then chmod +x \"$simworld_sh\"; printf '%s\\n' '#!/usr/bin/env bash' \"exec \\\"$simworld_sh\\\" \\\"\\$@\\\"\" > \"$install_dir/server\"; chmod +x \"$install_dir/server\"; fi; "
        "test -x \"$install_dir/server\" && echo server_executable=yes || echo server_executable=no; "
        "echo install_done=yes"
    )


def _parse_probe_facts(stdout: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    gpu_lines: list[str] = []
    candidate_lines: list[str] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "gpu":
            gpu_lines.append(value.strip())
            continue
        if key == "simworld_candidate":
            candidate_lines.append(value.strip())
            continue
        facts[key.strip()] = value.strip() or "unknown"
    facts["gpu_count"] = str(len(gpu_lines))
    if gpu_lines:
        facts["gpu"] = " | ".join(gpu_lines)
    facts["simworld_candidate_count"] = str(len(candidate_lines))
    if candidate_lines:
        facts["simworld_candidates"] = " | ".join(candidate_lines)
    return facts


def _simworld_failures(result: subprocess.CompletedProcess[str] | None, facts: dict[str, str]) -> list[str]:
    failures: list[str] = []
    if result is None:
        return ["ssh timeout before remote probe completed"]
    if result.returncode != 0:
        failures.append(f"ssh probe failed exit={result.returncode}")
    if facts.get("workspace_present") != "yes":
        failures.append(f"remote workspace missing: {GDX_WORKSPACE}")
    if facts.get("docker_present") != "yes":
        failures.append("docker command missing on gdx1")
    if facts.get("docker_usable") != "yes":
        failures.append("docker daemon unavailable or current user lacks access")
    if facts.get("nvidia_smi_present") != "yes":
        failures.append("nvidia-smi missing on gdx1")
    if int(facts.get("gpu_count", "0") or "0") <= 0:
        failures.append("no GPU reported by nvidia-smi")
    if int(facts.get("simworld_candidate_count", "0") or "0") <= 0:
        failures.append("SimWorld server binary not found")
    binary_file = facts.get("simworld_binary_file", "")
    host_arch = facts.get("arch", "")
    if host_arch in {"aarch64", "arm64"} and "x86-64" in binary_file:
        failures.append("SimWorld Linux UE binary is x86-64 but gdx1 host is aarch64")
    return failures


def _simworld_doctor_actions(facts: dict[str, str], failures: list[str]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    groups = set((facts.get("groups") or "").split(","))
    user = facts.get("user") or "daehan"
    if "docker daemon unavailable or current user lacks access" in failures:
        if facts.get("sudo_docker_usable") == "yes":
            actions.append(
                {
                    "id": "docker_group_access",
                    "status": "operator_required",
                    "reason": "docker works through sudo, but the current user cannot access the daemon directly",
                    "command": f"sudo usermod -aG docker {user} && newgrp docker",
                }
            )
        elif "docker" not in groups:
            actions.append(
                {
                    "id": "docker_group_missing",
                    "status": "operator_required",
                    "reason": "current SSH user is not in the docker group or the session has not refreshed group membership",
                    "command": f"sudo usermod -aG docker {user} && log out/in or run newgrp docker",
                }
            )
        else:
            actions.append(
                {
                    "id": "docker_daemon_unavailable",
                    "status": "operator_required",
                    "reason": "user appears to have docker group access, but docker info still fails",
                    "command": "sudo systemctl enable --now docker && docker info",
                }
            )
    if "SimWorld server binary not found" in failures:
        actions.append(
            {
                "id": "simworld_binary_missing",
                "status": "project_required",
                "reason": "no executable SimWorld server was found in the known candidate paths",
                "command": "install or sync SimWorld to ~/channel_play/tools/simworld/server, ~/channel_play/simworld/server, or /opt/simworld/server",
            }
        )
    if "SimWorld Linux UE binary is x86-64 but gdx1 host is aarch64" in failures:
        actions.append(
            {
                "id": "simworld_arch_mismatch",
                "status": "architecture_required",
                "reason": "the official SimWorld Linux UE server package is x86-64, while ASUS GX10/gdx1 reports aarch64",
                "command": "run SimWorld UE server on an x86_64 Linux host, use an x86_64 compatibility layer/container if validated, or obtain/build an aarch64 SimWorld server package",
            }
        )
    if "remote workspace missing: ~/channel_play" in failures:
        actions.append(
            {
                "id": "workspace_missing",
                "status": "project_required",
                "reason": "gdx1 does not have the project checkout at ~/channel_play",
                "command": "tools/channelctl gdx sync",
            }
        )
    if not actions:
        actions.append({"id": "ready", "status": "ready", "reason": "docker, GPU, workspace, and SimWorld binary probes passed", "command": "tools/channelctl simworld probe"})
    return actions


def _simworld_doctor_receipt(root: Path, report: dict, report_path: Path) -> str:
    failures = report["failures"] or ["none"]
    actions = report["recommendedActions"]
    facts = report["facts"]
    lines = [
        "# gdx1 SimWorld Doctor",
        "",
        f"Checked: {report['checkedAt']}",
        f"Status: `{report['status']}`",
        f"Host: `{report['host']}`",
        f"SSH exit: `{report['sshExit'] if report['sshExit'] is not None else 'timeout'}`",
        f"Report: `{rel(root, report_path)}`",
        "",
        "## Key Facts",
        "",
        f"- docker_present: `{facts.get('docker_present', 'unknown')}`",
        f"- docker_usable: `{facts.get('docker_usable', 'unknown')}`",
        f"- sudo_docker_usable: `{facts.get('sudo_docker_usable', 'unknown')}`",
        f"- docker_socket: `{facts.get('docker_socket', 'unknown')}`",
        f"- docker_service: `{facts.get('docker_service', 'unknown')}`",
        f"- groups: `{facts.get('groups', 'unknown')}`",
        f"- nvidia_smi_present: `{facts.get('nvidia_smi_present', 'unknown')}`",
        f"- gpu_count: `{facts.get('gpu_count', '0')}`",
        f"- simworld_candidate_count: `{facts.get('simworld_candidate_count', '0')}`",
        f"- simworld_binary: `{facts.get('simworld_binary', 'unknown')}`",
        f"- simworld_binary_file: `{facts.get('simworld_binary_file', 'unknown')}`",
        "",
        "## Failures",
        "",
        *[f"- {failure}" for failure in failures],
        "",
        "## Recommended Actions",
        "",
    ]
    for action in actions:
        lines.extend(
            [
                f"- `{action['id']}` status=`{action['status']}`",
                f"  - reason: {action['reason']}",
                f"  - command: `{action['command']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{report['artifacts']['remoteStdout']}`",
            f"- `{report['artifacts']['remoteStderr']}`",
            f"- `{report['artifacts']['report']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _simworld_install_failures(result: subprocess.CompletedProcess[str] | None, facts: dict[str, str], *, dry_run: bool) -> list[str]:
    failures: list[str] = []
    if result is None:
        return ["ssh timeout before install command completed"]
    if result.returncode != 0:
        failures.append(f"ssh install command failed exit={result.returncode}")
    if facts.get("hf_present") != "yes":
        failures.append("hf CLI missing at /home/daehan/.local/bin/hf")
    if facts.get("unzip_present") != "yes":
        failures.append("unzip command missing on gdx1")
    if facts.get("hf_dry_run_exit") not in (None, "0"):
        failures.append(f"SimWorld HF dry-run failed exit={facts.get('hf_dry_run_exit')}")
    if dry_run:
        return failures
    if facts.get("download_exit") != "0":
        failures.append(f"SimWorld base download failed exit={facts.get('download_exit', 'unknown')}")
    if facts.get("zip_present") != "yes":
        failures.append("SimWorld Linux.zip missing after download")
    if facts.get("unzip_exit") != "0":
        failures.append(f"SimWorld Linux.zip unzip failed exit={facts.get('unzip_exit', 'unknown')}")
    if facts.get("server_executable") != "yes":
        failures.append("SimWorld server wrapper was not created")
    return failures


def _simworld_install_base_receipt(root: Path, report: dict, report_path: Path) -> str:
    facts = report["facts"]
    failures = report["failures"] or ["none"]
    lines = [
        "# gdx1 SimWorld Base Installer",
        "",
        f"Checked: {report['checkedAt']}",
        f"Status: `{report['status']}`",
        f"Dry run: `{str(report['dryRun']).lower()}`",
        f"Host: `{report['host']}`",
        f"SSH exit: `{report['sshExit'] if report['sshExit'] is not None else 'timeout'}`",
        f"Report: `{rel(root, report_path)}`",
        "",
        "## Package",
        "",
        "- repo: `SimWorld-AI/SimWorld`",
        "- file: `Base20260201/Linux.zip`",
        f"- package_size: `{facts.get('package_size', 'unknown')}`",
        "",
        "## Install Facts",
        "",
        f"- hf_present: `{facts.get('hf_present', 'unknown')}`",
        f"- unzip_present: `{facts.get('unzip_present', 'unknown')}`",
        f"- install_dir: `{facts.get('install_dir', 'unknown')}`",
        f"- server_executable: `{facts.get('server_executable', 'not checked')}`",
        f"- simworld_sh: `{facts.get('simworld_sh', 'not checked')}`",
        "",
        "## Failures",
        "",
        *[f"- {failure}" for failure in failures],
        "",
        "## Next",
        "",
    ]
    if report["dryRun"] and not report["failures"]:
        lines.append("Run `tools/channelctl simworld install-base` to download the 22.2G Linux UE server package and create `~/channel_play/tools/simworld/server` on gdx1.")
    elif not report["failures"]:
        lines.append("Run `tools/channelctl simworld probe` to verify gdx1 SimWorld readiness.")
    else:
        lines.append("Fix the failures above, then rerun this command.")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{report['artifacts']['remoteStdout']}`",
            f"- `{report['artifacts']['remoteStderr']}`",
            f"- `{report['artifacts']['report']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _simworld_route_plan_receipt(root: Path, plan: dict, plan_path: Path) -> str:
    lines = [
        "# SimWorld Worker Route Plan",
        "",
        f"Created: {plan['createdAt']}",
        f"Status: `{plan['status']}`",
        f"Plan: `{rel(root, plan_path)}`",
        "",
        "## Facts",
        "",
    ]
    for key, value in plan["facts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Routes", ""])
    for route_id, route in plan["routes"].items():
        lines.append(f"- `{route_id}` worker=`{route['worker']}` status=`{route['status']}`")
        lines.append(f"  - reason: {route['reason']}")
        lines.append(f"  - evidence: `{route['evidence'] or 'missing'}`")
    lines.extend(["", "## Blocked", ""])
    if plan["blocked"]:
        for blocked in plan["blocked"]:
            lines.append(f"- `{blocked['id']}` status=`{blocked['status']}`")
            lines.append(f"  - reason: {blocked['reason']}")
            lines.append(f"  - evidence: `{blocked['evidence'] or 'missing'}`")
    else:
        lines.append("none")
    lines.extend(["", "## Next Commands", ""])
    for command in plan["nextCommands"]:
        lines.append(f"```bash\n{command}\n```")
    lines.append("")
    return "\n".join(lines)


def _simworld_start_server_receipt(root: Path, report: dict, report_path: Path) -> str:
    return "\n".join(
        [
            "# gdx1 SimWorld Start Server",
            "",
            f"Checked: {report['checkedAt']}",
            f"Status: `{report['status']}`",
            f"Target worker: `{report['targetWorker']}`",
            f"Route status: `{report['routeStatus']}`",
            f"Action: `{report['action']}`",
            f"Report: `{rel(root, report_path)}`",
            "",
            "## Reason",
            "",
            report["reason"],
            "",
            "## Evidence",
            "",
            f"- route plan: `{report['routePlan']}`",
            f"- route receipt: `{report['routePlanReceipt']}`",
            f"- worker evidence: `{report['evidence'] or 'missing'}`",
            "",
            "## Next",
            "",
            report["next"],
            "",
        ]
    )


def _simworld_worker_guide_markdown(report: dict) -> str:
    worker = report["worker"]
    requirements = worker.get("requirements") if isinstance(worker.get("requirements"), dict) else {}
    commands = report.get("commands") if isinstance(report.get("commands"), list) else []
    return "\n".join(
        [
            "# x86_64 SimWorld Worker Setup Packet",
            "",
            f"Created: {report['createdAt']}",
            f"Status: `{report['status']}`",
            f"Current worker status: `{worker['status']}`",
            f"Host env: `{worker['hostEnv']}`",
            "",
            "## Required Machine",
            "",
            f"- arch: `{requirements.get('arch', 'x86_64')}`",
            f"- docker: `{requirements.get('docker', 'required')}`",
            f"- gpu: `{requirements.get('gpu', 'nvidia')}`",
            f"- server path: `{requirements.get('server_path', '~/channel_play/tools/simworld/server')}`",
            "",
            "## Operator Commands",
            "",
            *[f"```bash\n{command}\n```" for command in commands],
            "",
            "## Current Probe",
            "",
            f"- enabled: `{worker['enabled']}`",
            f"- host: `{worker['host'] or 'not_configured'}`",
            f"- summary: `{(worker.get('lastProbe') or {}).get('summary', 'none')}`",
            "",
            "## Expected Ready State",
            "",
            "- `memory/company/worker_fleet.json` has `x86_64_linux_gpu_worker.status=available`",
            "- route-plan has `routes.simworldUeServer.status=ready`",
            "- start-server may run only after that route is ready",
            "",
        ]
    )


def _simworld_worker_guide_receipt(root: Path, report: dict, report_path: Path) -> str:
    artifacts = report["artifacts"]
    return "\n".join(
        [
            "# SimWorld x86_64 Worker Guide",
            "",
            f"Created: {report['createdAt']}",
            f"Status: `{report['status']}`",
            f"Report: `{rel(root, report_path)}`",
            "",
            "## Worker",
            "",
            f"- id: `{report['worker']['id']}`",
            f"- status: `{report['worker']['status']}`",
            f"- host env: `{report['worker']['hostEnv']}`",
            "",
            "## Artifacts",
            "",
            f"- guide: `{artifacts['guide']}`",
            f"- report: `{artifacts['report']}`",
            f"- worker fleet: `{artifacts['workerFleet']}`",
            "",
            "## Next Commands",
            "",
            *[f"```bash\n{command}\n```" for command in report["commands"]],
            "",
        ]
    )


def _latest_run(root: Path, prefix: str) -> Path | None:
    base = root / "runs"
    if not base.exists():
        return None
    candidates = [path for path in base.iterdir() if path.is_dir() and path.name.startswith(prefix)]
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else None


def _latest_receipt(root: Path, prefix: str) -> str:
    run = _latest_run(root, prefix)
    if not run:
        return ""
    receipt = run / "receipt.md"
    return rel(root, receipt) if receipt.exists() else rel(root, run)


def _receipt_has(run_dir: Path | None, text: str) -> bool:
    if not run_dir:
        return False
    receipt = run_dir / "receipt.md"
    return receipt.exists() and text in receipt.read_text(encoding="utf-8-sig", errors="ignore")


def _read_json(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except json.JSONDecodeError:
        return default


def _origin_url(root: Path) -> str:
    result = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=root, capture_output=True, text=True, check=False)
    return result.stdout.strip() or "https://github.com/zenovis2-create/channel_play.git"


def _update_gdx_state(root: Path, ssh_ok: bool) -> None:
    state = load_state_json(root)
    gdx = state.setdefault("gdx1", {})
    gdx["network"] = "online_via_tailscale"
    gdx["ssh"] = "ok" if ssh_ok else "auth_blocked"
    gdx["updated_at"] = now_iso()
    state["updated_at"] = now_iso()
    save_state_json(root, state)


def _update_gdx_simworld_state(root: Path, status: str, failures: list[str], receipt: Path) -> None:
    state = load_state_json(root)
    gdx = state.setdefault("gdx1", {})
    gdx["simworld_probe"] = status
    gdx["simworld_probe_failures"] = failures
    gdx["simworld_probe_receipt"] = receipt.relative_to(root).as_posix()
    gdx["updated_at"] = now_iso()
    state["updated_at"] = now_iso()
    save_state_json(root, state)
