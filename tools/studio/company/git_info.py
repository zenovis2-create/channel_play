"""Small git helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_short_status(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ["git status unavailable"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"
