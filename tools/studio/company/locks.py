"""Path lock management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .errors import CompanyError
from .state import load_locks, save_locks
from .timeutil import now_iso


def _norm(path: str) -> str:
    return Path(path).as_posix().strip("/")


def _conflicts(a: str, b: str) -> bool:
    a_norm = _norm(a)
    b_norm = _norm(b)
    return a_norm == b_norm or a_norm.startswith(b_norm + "/") or b_norm.startswith(a_norm + "/")


def render_locks(root: Path) -> str:
    data = load_locks(root)
    locks = data.get("locks", [])
    if not locks:
        return "No active locks."
    return "\n".join(
        f"{lock.get('path')}  owner={lock.get('owner')} task={lock.get('task_id')} expires={lock.get('expires_at')}"
        for lock in locks
    )


def assert_no_conflict(root: Path, paths: list[str]) -> None:
    locks = load_locks(root).get("locks", [])
    for wanted in paths:
        for lock in locks:
            if _conflicts(wanted, str(lock.get("path", ""))):
                raise CompanyError(f"Path lock conflict: {wanted} conflicts with {lock.get('path')}")


def lock_path(root: Path, path: str, owner: str, task_id: str) -> None:
    data = load_locks(root)
    locks = data.setdefault("locks", [])
    wanted = _norm(path)
    for lock in locks:
        if _conflicts(wanted, str(lock.get("path", ""))):
            raise CompanyError(f"Path already locked: {lock.get('path')} by {lock.get('owner')}")
    expires = datetime.now(timezone.utc).astimezone() + timedelta(hours=4)
    locks.append(
        {
            "path": wanted,
            "owner": owner,
            "task_id": task_id,
            "created_at": now_iso(),
            "expires_at": expires.isoformat(timespec="seconds"),
        }
    )
    save_locks(root, data)


def unlock_path(root: Path, path: str) -> None:
    data = load_locks(root)
    wanted = _norm(path)
    locks: list[dict[str, Any]] = data.get("locks", [])
    kept = [lock for lock in locks if _norm(str(lock.get("path", ""))) != wanted]
    if len(kept) == len(locks):
        raise CompanyError(f"No lock found for path: {path}")
    data["locks"] = kept
    save_locks(root, data)
