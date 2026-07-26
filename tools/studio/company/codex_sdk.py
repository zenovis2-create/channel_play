"""Optional OpenAI Codex Python SDK integration."""

from __future__ import annotations

import importlib
import importlib.util
import os
import signal
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class CodexSDKTimeout(TimeoutError):
    """Raised when an SDK turn exceeds the Studio adapter timeout."""


def codex_sdk_status(package: str = "openai_codex", root: Path | None = None) -> dict[str, Any]:
    added_paths = _ensure_sdk_path(root)
    spec = importlib.util.find_spec(package)
    if spec is None:
        return {
            "available": False,
            "status": "missing",
            "package": package,
            "version": "",
            "origin": "",
            "last_error": f"Python package not installed: {package}",
            "search_paths": added_paths,
        }
    try:
        module = importlib.import_module(package)
    except Exception as exc:  # pragma: no cover - import failures are environment-specific.
        return {
            "available": False,
            "status": "import_failed",
            "package": package,
            "version": "",
            "origin": str(spec.origin or ""),
            "last_error": str(exc),
            "search_paths": added_paths,
        }
    return {
        "available": True,
        "status": "available",
        "package": package,
        "version": str(getattr(module, "__version__", "")),
        "origin": str(spec.origin or ""),
        "last_error": "",
        "search_paths": added_paths,
    }


def run_codex_sdk_turn(
    root: Path,
    prompt: str,
    *,
    timeout_seconds: int,
    package: str = "openai_codex",
    approval_mode_name: str = "auto_review",
    sandbox_name: str = "workspace_write",
    model: str = "",
) -> dict[str, Any]:
    _ensure_sdk_path(root)
    module = importlib.import_module(package)
    Codex = getattr(module, "Codex")
    ApprovalMode = getattr(module, "ApprovalMode", None)
    Sandbox = getattr(module, "Sandbox", None)

    approval_mode = _enum_value(ApprovalMode, approval_mode_name)
    sandbox = _enum_value(Sandbox, sandbox_name)
    thread_kwargs = _clean_kwargs(
        {
            "cwd": str(root),
            "approval_mode": approval_mode,
            "sandbox": sandbox,
            "model": model or None,
        }
    )
    run_kwargs = _clean_kwargs(
        {
            "cwd": str(root),
            "approval_mode": approval_mode,
            "sandbox": sandbox,
            "model": model or None,
        }
    )

    try:
        with _timeout_after(timeout_seconds):
            with Codex() as codex:
                thread = codex.thread_start(**thread_kwargs)
                result = thread.run(prompt, **run_kwargs)
    except CodexSDKTimeout:
        return {
            "status": "timeout",
            "exit": 124,
            "stdout": "",
            "stderr": f"Codex Python SDK timed out after {timeout_seconds}s.\n",
            "executor": "codex_sdk",
            "sdk": codex_sdk_status(package, root),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "exit": 1,
            "stdout": "",
            "stderr": f"Codex Python SDK failed: {exc}\n",
            "executor": "codex_sdk",
            "sdk": codex_sdk_status(package, root),
        }

    error = getattr(result, "error", None)
    final_response = str(getattr(result, "final_response", "") or "")
    status_text = _status_text(getattr(result, "status", ""))
    failed = bool(error) or status_text.lower() in {"failed", "error", "cancelled", "canceled"}
    return {
        "status": "failed" if failed else "ok",
        "exit": 1 if failed else 0,
        "stdout": final_response or _status_output(result, status_text),
        "stderr": _error_text(error),
        "executor": "codex_sdk",
        "sdk": codex_sdk_status(package, root),
        "turn": {
            "id": str(getattr(result, "id", "") or ""),
            "status": status_text,
            "duration_ms": getattr(result, "duration_ms", None),
            "usage": _portable(getattr(result, "usage", None)),
        },
    }


def _enum_value(enum_cls: Any, name: str) -> Any:
    if enum_cls is None or not name:
        return None
    return getattr(enum_cls, name, None)


def _clean_kwargs(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _status_text(value: Any) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", getattr(value, "name", value)))


def _error_text(error: Any) -> str:
    if not error:
        return ""
    if hasattr(error, "message"):
        return str(error.message)
    return str(error)


def _status_output(result: Any, status_text: str) -> str:
    turn_id = str(getattr(result, "id", "") or "")
    suffix = f" turn={turn_id}" if turn_id else ""
    return f"Codex SDK turn completed with status {status_text or 'unknown'}{suffix}.\n"


def _portable(value: Any) -> Any:
    if value is None:
        return None
    for attr in ("model_dump", "dict"):
        method = getattr(value, attr, None)
        if callable(method):
            try:
                return method()
            except TypeError:
                pass
    return str(value)


def _ensure_sdk_path(root: Path | None) -> list[str]:
    candidates: list[Path] = []
    env_path = os.environ.get("CHANNEL_PLAY_CODEX_SDK_VENV", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())
    if root is not None:
        candidates.extend([root / ".venv" / "codex-sdk", root / ".venv"])

    added: list[str] = []
    for candidate in candidates:
        if not candidate.exists():
            continue
        for site_packages in sorted(candidate.glob("lib/python*/site-packages")):
            value = str(site_packages)
            if value not in sys.path:
                sys.path.insert(0, value)
                added.append(value)
    return added


@contextmanager
def _timeout_after(seconds: int) -> Iterator[None]:
    if seconds <= 0 or threading.current_thread() is not threading.main_thread():
        yield
        return

    def raise_timeout(signum: int, frame: Any) -> None:
        raise CodexSDKTimeout()

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    signal.signal(signal.SIGALRM, raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])
