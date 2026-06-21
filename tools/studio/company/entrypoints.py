"""Top-level non-company command dispatch."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .assets import asset_new, asset_screenshot, asset_status
from .capture import capture_screen
from .dashboard import generate_dashboard
from .errors import CompanyError
from .feedback import feedback_new, feedback_process
from .gdx import gdx_collect_logs, gdx_probe, gdx_run_bots, gdx_run_server, gdx_sync
from .paths import find_repo_root, rel
from .unity import unity_check


def dispatch_top_level(command: str, args: list[str]) -> int:
    try:
        root = find_repo_root()
        if command == "unity" and args[:1] == ["check"]:
            unity_check(root, args[1:])
            return 0
        if command == "open":
            return _open(root, args)
        if command == "capture" and args[:1] == ["screen"]:
            path = capture_screen(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "feedback" and args[:1] == ["new"]:
            path = feedback_new(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "feedback" and args[:1] == ["process"]:
            if len(args) < 2:
                raise CompanyError("Usage: feedback process <feedback.md>")
            path = feedback_process(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["new"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset new <asset-id>")
            path = asset_new(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["status"]:
            if len(args) < 3:
                raise CompanyError("Usage: asset status <asset-id> <status>")
            path = asset_status(root, args[1], args[2])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["screenshot"]:
            if len(args) < 3:
                raise CompanyError("Usage: asset screenshot <asset-id> <path>")
            path = asset_screenshot(root, args[1], args[2])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["probe"]:
            path = gdx_probe(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["sync"]:
            path = gdx_sync(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["run-server"]:
            path = gdx_run_server(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["run-bots"]:
            path = gdx_run_bots(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["collect-logs"]:
            path = gdx_collect_logs(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        raise CompanyError(f"Unknown command: {command} {' '.join(args)}")
    except CompanyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _open(root: Path, args: list[str]) -> int:
    if not args:
        raise CompanyError("Usage: open dashboard")
    target = args[0]
    if target == "dashboard":
        path = generate_dashboard(root)
    elif target == "studio":
        path = root / "tools" / "studio" / "app" / "index.html"
    elif target == "unity":
        path = root
    elif target == "obsidian":
        path = root / "obsidian" / "channel_play"
    else:
        raise CompanyError(f"Unknown open target: {target}")
    _open_path(path, root)
    print(f"Opened {rel(root, path)}")
    return 0


def _open_path(path: Path, root: Path) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, str(path)], cwd=root, check=False)
