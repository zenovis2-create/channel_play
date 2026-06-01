"""Local web cockpit for Channel Play Studio."""

from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tools.studio.company.errors import CompanyError
from tools.studio.company.git_info import git_head, git_short_status
from tools.studio.company.paths import find_repo_root, rel
from tools.studio.company.state import CompanyPaths, load_company_state, read_json, read_text

APP_DIR = Path(__file__).resolve().parent / "app"
MAX_FILE_BYTES = 120_000
ALLOWED_READ_PREFIXES = (
    "agents",
    "asset_pipeline",
    "docs",
    "memory",
    "reviews",
    "runs",
    "tools/studio/templates",
)


def serve(host: str = "127.0.0.1", port: int = 8766, open_browser: bool = False) -> None:
    root = find_repo_root()
    server = ThreadingHTTPServer((host, port), _handler(root))
    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    print(f"Channel Play Studio serving {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nChannel Play Studio stopped")
    finally:
        server.server_close()


def collect_workspace_state(root: Path) -> dict:
    company = load_company_state(root)
    paths = CompanyPaths(root)
    tasks = company["tasks"]
    open_tasks = [task for task in tasks if task.get("status") not in {"closed", "closed_blocked"}]
    return {
        "project": "channel_play",
        "root": str(root),
        "git": {
            "head": git_head(root),
            "dirty": git_short_status(root),
        },
        "company": {
            "state": company["state"],
            "agents": company["agents"],
            "tasks": tasks,
            "openTasks": open_tasks,
            "locks": company["locks"],
        },
        "memory": {
            "currentContext": read_text(paths.current_context_md),
            "currentBrief": read_text(paths.current_brief_md),
            "decisionLog": read_text(paths.memory_dir / "decision_log.md"),
        },
        "feedback": _list_feedback(root),
        "assets": _load_assets(root),
        "sessions": _list_dirs(root / "memory" / "sessions"),
        "runs": _list_runs(root),
        "commands": sorted(COMMANDS.keys()),
    }


def build_command(root: Path, name: str, payload: dict) -> list[str]:
    channelctl = str(root / "tools" / "channelctl")
    if name not in COMMANDS:
        raise CompanyError(f"Command not allowed: {name}")
    return [channelctl, *COMMANDS[name](payload)]


def run_command(root: Path, name: str, payload: dict) -> dict:
    command = build_command(root, name, payload)
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "UNITY_EDITOR": os.environ.get("UNITY_EDITOR", ""),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
    }
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
        env=env,
    )
    return {
        "ok": result.returncode == 0,
        "exit": result.returncode,
        "command": " ".join(command),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def read_workspace_file(root: Path, raw_path: str) -> dict:
    path = _safe_path(root, raw_path)
    if not path.exists() or not path.is_file():
        raise CompanyError(f"File not found: {raw_path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise CompanyError(f"File too large for preview: {raw_path}")
    return {"path": rel(root, path), "content": path.read_text(encoding="utf-8", errors="replace")}


def _handler(root: Path):
    class StudioHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/state":
                    self._json(collect_workspace_state(root))
                    return
                if parsed.path == "/api/file":
                    query = parse_qs(parsed.query)
                    self._json(read_workspace_file(root, query.get("path", [""])[0]))
                    return
                self._static(parsed.path)
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive web boundary
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path != "/api/command":
                    self._json({"ok": False, "error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body or "{}")
                self._json(run_command(root, str(data.get("command", "")), data.get("payload") or {}))
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive web boundary
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _static(self, path_text: str) -> None:
            target = "index.html" if path_text in {"/", ""} else path_text.lstrip("/")
            path = (APP_DIR / target).resolve()
            if not str(path).startswith(str(APP_DIR.resolve())) or not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
                return
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return StudioHandler


def _safe_path(root: Path, raw_path: str) -> Path:
    clean = raw_path.strip().lstrip("/")
    if not clean:
        raise CompanyError("Path is required.")
    if not any(clean == prefix or clean.startswith(prefix + "/") for prefix in ALLOWED_READ_PREFIXES):
        raise CompanyError(f"Path not readable from Studio: {raw_path}")
    path = (root / clean).resolve()
    if not str(path).startswith(str(root.resolve())):
        raise CompanyError(f"Path escapes repo: {raw_path}")
    return path


def _list_dirs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for child in sorted(path.iterdir(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:24]:
        if child.is_dir():
            rows.append({"name": child.name, "path": rel(path.parents[1], child)})
    return rows


def _list_feedback(root: Path) -> list[dict]:
    rows = []
    base = root / "reviews"
    if not base.exists():
        return rows
    for note in sorted(base.glob("20*/feedback-*/feedback.md"), key=lambda item: item.stat().st_mtime, reverse=True)[:24]:
        text = note.read_text(encoding="utf-8", errors="ignore")
        rows.append(
            {
                "id": note.parent.name,
                "path": rel(root, note),
                "status": _field(text, "Status") or "unknown",
                "scene": _field(text, "Scene") or "TBD",
                "screenshot": _field(text, "Screenshot") or "TBD",
            }
        )
    return rows


def _load_assets(root: Path) -> list[dict]:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        return []
    return read_json(index).get("assets", [])


def _list_runs(root: Path) -> list[dict]:
    base = root / "runs"
    if not base.exists():
        return []
    rows = []
    for child in sorted(base.iterdir(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:32]:
        if not child.is_dir():
            continue
        md_files = list(child.glob("*.md"))
        rows.append({"name": child.name, "path": rel(root, child), "file": rel(root, md_files[0]) if md_files else ""})
    return rows


def _field(text: str, name: str) -> str:
    prefix = f"{name}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _required(payload: dict, key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise CompanyError(f"Missing field: {key}")
    return value


COMMANDS = {
    "company.status": lambda payload: ["company", "status"],
    "company.agents": lambda payload: ["company", "agents"],
    "company.brief": lambda payload: ["company", "brief"],
    "company.session.start": lambda payload: ["company", "session", "start", _required(payload, "goal")],
    "company.session.end": lambda payload: ["company", "session", "end"],
    "company.plan": lambda payload: ["company", "plan", _required(payload, "request")],
    "company.assign": lambda payload: ["company", "assign", _required(payload, "taskId"), _required(payload, "agentId")],
    "company.locks": lambda payload: ["company", "locks"],
    "company.lock": lambda payload: ["company", "lock", _required(payload, "path"), _required(payload, "owner"), _required(payload, "taskId")],
    "company.unlock": lambda payload: ["company", "unlock", _required(payload, "path")],
    "company.report": lambda payload: ["company", "report", _required(payload, "taskId"), _required(payload, "agentId"), str(payload.get("status", "needs_review"))],
    "company.evidence": lambda payload: ["company", "evidence", _required(payload, "taskId"), _required(payload, "path"), str(payload.get("note", ""))],
    "company.verify": lambda payload: ["company", "verify", _required(payload, "taskId")],
    "company.close": lambda payload: ["company", "close", _required(payload, "taskId")],
    "unity.check": lambda payload: ["unity", "check"],
    "capture.screen": lambda payload: ["capture", "screen"],
    "feedback.new": lambda payload: ["feedback", "new"],
    "feedback.process": lambda payload: ["feedback", "process", _required(payload, "path")],
    "asset.new": lambda payload: ["asset", "new", _required(payload, "assetId")],
    "asset.status": lambda payload: ["asset", "status", _required(payload, "assetId"), _required(payload, "status")],
    "asset.screenshot": lambda payload: ["asset", "screenshot", _required(payload, "assetId"), _required(payload, "path")],
    "gdx.probe": lambda payload: ["gdx", "probe"],
    "gdx.sync": lambda payload: ["gdx", "sync"],
    "gdx.runServer": lambda payload: ["gdx", "run-server"],
    "gdx.runBots": lambda payload: ["gdx", "run-bots"],
    "gdx.collectLogs": lambda payload: ["gdx", "collect-logs"],
}
