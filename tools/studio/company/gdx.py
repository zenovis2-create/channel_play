"""gdx1 worker probes."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .timeutil import now_iso, slugify


def gdx_probe(root: Path) -> Path:
    run_dir = root / "runs" / f"gdx-probe-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "gdx_probe.md"
    ssh = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "gdx1", "hostname"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=8,
    )
    workspace = None
    if ssh.returncode == 0:
        workspace = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "gdx1", "test -d ~/channel_play && echo exists || echo missing"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
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
    return path


def _workspace_result(result: subprocess.CompletedProcess[str] | None) -> str:
    if result is None:
        return "not checked: ssh blocked"
    return result.stdout.strip() or f"check failed exit={result.returncode}"


def gdx_sync(root: Path) -> Path:
    return _blocked_action(root, "sync", "remote sync requires SSH auth to gdx1")


def gdx_run_server(root: Path) -> Path:
    return _blocked_action(root, "run-server", "headless server run requires SSH auth to gdx1")


def gdx_run_bots(root: Path) -> Path:
    return _blocked_action(root, "run-bots", "bot run requires SSH auth to gdx1")


def gdx_collect_logs(root: Path) -> Path:
    return _blocked_action(root, "collect-logs", "log collection requires SSH auth to gdx1")


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
