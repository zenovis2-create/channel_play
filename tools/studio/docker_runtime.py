"""Runtime helpers for containerized Channel Play Studio."""

from __future__ import annotations

import os
import secrets
import stat
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from tools.studio.company.paths import rel

DOCKER_ENV = "CHANNEL_PLAY_STUDIO_DOCKER"
HOST_RUNNER_URL_ENV = "CHANNEL_PLAY_HOST_RUNNER_URL"
RUNNER_TOKEN_ENV = "CHANNEL_PLAY_RUNNER_TOKEN"
RUNNER_TOKEN_FILE_ENV = "CHANNEL_PLAY_RUNNER_TOKEN_FILE"
RUNNER_TOKEN_HEADER = "X-Channel-Play-Runner-Token"
DEFAULT_RUNNER_TOKEN_PATH = Path("memory/company/secrets/host_runner.token")


def is_containerized() -> bool:
    return _truthy(os.environ.get(DOCKER_ENV, "")) or Path("/.dockerenv").exists()


def host_runner_url() -> str:
    return os.environ.get(HOST_RUNNER_URL_ENV, "").strip().rstrip("/")


def runner_token_path(root: Path) -> Path:
    raw = os.environ.get(RUNNER_TOKEN_FILE_ENV, "").strip()
    path = Path(raw) if raw else root / DEFAULT_RUNNER_TOKEN_PATH
    if not path.is_absolute():
        path = root / path
    return path


def read_runner_token(root: Path) -> str:
    env_token = os.environ.get(RUNNER_TOKEN_ENV, "").strip()
    if env_token:
        return env_token
    path = runner_token_path(root)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def ensure_runner_token(root: Path) -> tuple[Path, bool]:
    path = runner_token_path(root)
    if path.exists() and path.read_text(encoding="utf-8").strip():
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path, True


def studio_runtime_state(root: Path) -> dict:
    runner_url = host_runner_url()
    token_path = runner_token_path(root)
    token_configured = bool(read_runner_token(root))
    runner_health = _runner_health(root, runner_url, token_configured)
    docker_socket = Path("/var/run/docker.sock")
    return {
        "containerized": is_containerized(),
        "executionMode": "host_runner" if runner_url else "local",
        "dockerSocketMounted": docker_socket.exists(),
        "hostRunner": {
            "url": _safe_url(runner_url),
            "status": runner_health["status"],
            "message": runner_health["message"],
            "tokenConfigured": token_configured,
            "tokenFile": rel(root, token_path) if str(token_path).startswith(str(root)) else str(token_path),
        },
        "security": {
            "dockerSocketPolicy": "forbidden",
            "secretsPolicy": "runner token via secret file",
            "commandPolicy": "Studio forwards execution to host-runner when configured",
        },
    }


def _runner_health(root: Path, runner_url: str, token_configured: bool) -> dict:
    if not runner_url:
        return {"status": "local", "message": "명령을 Studio 프로세스에서 직접 실행합니다."}
    if not token_configured:
        return {"status": "blocked", "message": "host-runner token이 설정되지 않았습니다."}
    request = urllib.request.Request(
        f"{runner_url}/api/status",
        headers={RUNNER_TOKEN_HEADER: read_runner_token(root)},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=0.5) as response:
            if response.status == 200:
                return {"status": "available", "message": "host-runner 응답 확인됨"}
            return {"status": "blocked", "message": f"host-runner status {response.status}"}
    except (OSError, urllib.error.URLError) as exc:
        return {"status": "blocked", "message": f"host-runner 연결 실패: {exc}"}


def _safe_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    return f"{parsed.scheme}://{parsed.netloc}"


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
