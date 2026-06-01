"""gdx1 worker probes."""

from __future__ import annotations

import subprocess
from pathlib import Path
from shlex import quote

from .state import load_state_json, save_state_json

from .timeutil import now_iso, slugify

GDX_HOST = "gdx1"
GDX_WORKSPACE = "~/channel_play"


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
    command = (
        f"set -eu; cd {GDX_WORKSPACE}; "
        "if [ -x scripts/gdx1_run_server.sh ]; then ./scripts/gdx1_run_server.sh; "
        "elif [ -x builds/linux-server/channel_play_server ]; then ./builds/linux-server/channel_play_server -batchmode -nographics; "
        "else echo 'blocked: no gdx1 server runner or Linux server build found'; exit 3; fi"
    )
    return _remote_action(root, "run-server", command, timeout=60)


def gdx_run_bots(root: Path) -> Path:
    command = (
        f"set -eu; cd {GDX_WORKSPACE}; "
        "if [ -x scripts/gdx1_run_bots.sh ]; then ./scripts/gdx1_run_bots.sh; "
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


def _remote_action(root: Path, action: str, command: str, timeout: int) -> Path:
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


def _ssh(command: str, root: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", GDX_HOST, command],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


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
