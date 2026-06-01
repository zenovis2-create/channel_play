"""Agent Company CLI dispatch."""

from __future__ import annotations

import sys
from pathlib import Path

from .agents import render_agents
from .brief import write_brief
from .errors import CompanyError
from .locks import lock_path, render_locks, unlock_path
from .paths import find_repo_root, rel
from .planner import assign_task, plan_task
from .reports import create_report
from .sessions import end_session, start_session
from .status import render_status
from .verify import attach_evidence, close_task, verify_task


def main(argv: list[str] | None = None) -> int:
    args = list(argv or [])
    try:
        root = find_repo_root()
        if not args or args[0] in {"help", "-h", "--help"}:
            return _help()

        command = args[0]
        if command == "status":
            print(render_status(root))
            return 0
        if command == "agents":
            print(render_agents(root))
            return 0
        if command == "brief":
            path = write_brief(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "session":
            return _session(root, args[1:])
        if command == "plan":
            request = " ".join(args[1:]).strip()
            path = plan_task(root, request)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "assign":
            if len(args) < 3:
                raise CompanyError("Usage: company assign <task-id> <agent-id>")
            path = assign_task(root, args[1], args[2])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "locks":
            print(render_locks(root))
            return 0
        if command == "lock":
            if len(args) < 4:
                raise CompanyError("Usage: company lock <path> <owner> <task-id>")
            lock_path(root, args[1], args[2], args[3])
            print("Locked")
            return 0
        if command == "unlock":
            if len(args) < 2:
                raise CompanyError("Usage: company unlock <path>")
            unlock_path(root, args[1])
            print("Unlocked")
            return 0
        if command == "report":
            if len(args) < 3:
                raise CompanyError("Usage: company report <task-id> <agent-id> [status]")
            status = args[3] if len(args) > 3 else "needs_review"
            path = create_report(root, args[1], args[2], status)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "verify":
            if len(args) < 2:
                raise CompanyError("Usage: company verify <task-id>")
            path = verify_task(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "evidence":
            if len(args) < 3:
                raise CompanyError("Usage: company evidence <task-id> <path> [note]")
            note = " ".join(args[3:]).strip() if len(args) > 3 else ""
            attach_evidence(root, args[1], args[2], note)
            print("Evidence attached")
            return 0
        if command == "close":
            if len(args) < 2:
                raise CompanyError("Usage: company close <task-id>")
            blocked_reason = None
            if "--blocked" in args:
                idx = args.index("--blocked")
                blocked_reason = " ".join(args[idx + 1 :]).strip() or "blocked"
            close_task(root, args[1], blocked_reason)
            print("Closed")
            return 0

        print(f"Unknown company command: {command}", file=sys.stderr)
        return 2
    except CompanyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _help() -> int:
    print(
        "\n".join(
            [
                "channelctl company",
                "",
                "Commands:",
                "  status    Show shared memory, git, task, lock, gdx1 state",
                "  agents    List registered agent profiles",
                "  brief     Generate memory/company/current_brief.md",
                "  session start <goal>",
                "  session end",
                "  plan <request>",
                "  assign <task-id> <agent-id>",
                "  locks | lock <path> <owner> <task-id> | unlock <path>",
                "  report <task-id> <agent-id> [status]",
                "  evidence <task-id> <path> [note]",
                "  verify <task-id>",
                "  close <task-id> [--blocked reason]",
            ]
        )
    )
    return 0


def _session(root: Path, args: list[str]) -> int:
    if not args:
        raise CompanyError("Usage: company session start <goal> | end")
    command = args[0]
    if command == "start":
        goal = " ".join(args[1:]).strip()
        path = start_session(root, goal)
        print(f"Started {rel(root, path.parent)}")
        return 0
    if command == "end":
        path = end_session(root)
        print(f"Wrote {rel(root, path)}")
        return 0
    raise CompanyError("Usage: company session start <goal> | end")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
