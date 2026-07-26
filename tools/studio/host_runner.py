"""Local host runner for containerized Channel Play Studio."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tools.studio.company.errors import CompanyError
from tools.studio.company.paths import find_repo_root, rel
from tools.studio.company.agent_runner import collect_agent_adapter_state
from tools.studio.docker_runtime import RUNNER_TOKEN_HEADER, ensure_runner_token, read_runner_token
from tools.studio.workspace_server import run_local_command


def serve(host: str = "127.0.0.1", port: int = 8788) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise CompanyError("Host runner must bind to loopback only.")
    root = find_repo_root()
    token_path, created = ensure_runner_token(root)
    server = ThreadingHTTPServer((host, port), _handler(root))
    print(f"Channel Play host-runner serving http://{host}:{port}/")
    print(f"Runner token: {rel(root, token_path)}{' created' if created else ''}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nChannel Play host-runner stopped")
    finally:
        server.server_close()


def ensure_token(root: Path | None = None) -> Path:
    target_root = root or find_repo_root()
    path, _ = ensure_runner_token(target_root)
    return path


def _handler(root: Path):
    class HostRunnerHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            try:
                if self.path == "/api/status":
                    self._require_token()
                    self._json({"ok": True, "mode": "host_runner", "root": str(root)})
                    return
                if self.path == "/api/adapters":
                    self._require_token()
                    self._json({"ok": True, "adapters": collect_agent_adapter_state(root)})
                    return
                if self.path != "/api/status":
                    self._json({"ok": False, "error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)
                    return
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:
            try:
                if self.path != "/api/command":
                    self._json({"ok": False, "error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)
                    return
                self._require_token()
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body or "{}")
                result = run_local_command(root, str(data.get("command", "")), data.get("payload") or {})
                result["runner"] = "host"
                self._json(result)
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive process boundary
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _require_token(self) -> None:
            token = read_runner_token(root)
            if not token:
                raise CompanyError("Host runner token is not configured.")
            if self.headers.get(RUNNER_TOKEN_HEADER, "") != token:
                raise CompanyError("Host runner token missing or invalid.")

        def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return HostRunnerHandler
