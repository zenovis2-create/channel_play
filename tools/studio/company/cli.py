"""Agent Company CLI dispatch."""

from __future__ import annotations

import sys
from pathlib import Path

from .advance import advance_task
from .agents import render_agents
from .brain import render_brain_status
from .brief import write_brief
from .errors import CompanyError
from .goal_engine import render_goal_status, run_goal, set_goal
from .locks import lock_path, render_locks, unlock_path
from .model_cookbook import render_model_cookbook
from .paths import find_repo_root, rel
from .planner import assign_task, plan_task
from .reports import create_report, create_review_checkpoint
from .search import rebuild_search_index, render_search_results
from .sessions import end_session, start_session
from .status import render_status
from .tasks import archive_tasks
from .verify import attach_evidence, close_task, verify_task
from .workflow import run_orchestrator_workflow
from .worker_fleet import render_worker_fleet


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
        if command == "brain":
            print(render_brain_status(root))
            return 0
        if command == "search":
            query, rebuild, limit = _search_args(args[1:])
            print(render_search_results(root, query, limit=limit, rebuild=rebuild))
            return 0
        if command == "search-index":
            result = rebuild_search_index(root)
            print(f"Wrote {result['indexPath']} ({result['documentCount']} docs)")
            return 0
        if command == "workers":
            print(render_worker_fleet(root, probe="--probe" in args))
            return 0
        if command in {"models", "model-cookbook"}:
            print(render_model_cookbook(root, refresh="--refresh" in args))
            return 0
        if command == "session":
            return _session(root, args[1:])
        if command == "plan":
            request = " ".join(args[1:]).strip()
            path = plan_task(root, request)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "workflow":
            dry_run = "--real" not in args
            request_parts = [arg for arg in args[1:] if arg != "--real"]
            path = run_orchestrator_workflow(root, " ".join(request_parts).strip(), dry_run=dry_run)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "goal":
            return _goal(root, args[1:])
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
        if command == "review":
            if len(args) < 2:
                raise CompanyError("Usage: company review <task-id> [reviewer-id]")
            reviewer_id = args[2] if len(args) > 2 else "critic_reviewer"
            path = create_review_checkpoint(root, args[1], reviewer_id)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "verify":
            if len(args) < 2:
                raise CompanyError("Usage: company verify <task-id>")
            path = verify_task(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "advance":
            if len(args) < 2:
                raise CompanyError("Usage: company advance <task-id>")
            path = advance_task(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "archive":
            task_ids, reason = _archive_args(args[1:])
            path = archive_tasks(root, task_ids, reason=reason)
            print(f"Archived {len(task_ids)} task(s) to {rel(root, path)}")
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
                "  brain     Show Project Brain and standards registry",
                "  search <query> [--rebuild] [--limit N]",
                "  search-index",
                "  workers [--probe]",
                "  models [--refresh]",
                "  session start <goal>",
                "  session end",
                "  plan <request>",
                "  workflow <request> [--real]",
                "  goal status | set <objective> | run [--real] [--max-iterations N]",
                "  assign <task-id> <agent-id>",
                "  locks | lock <path> <owner> <task-id> | unlock <path>",
                "  report <task-id> <agent-id> [status]",
                "  review <task-id> [reviewer-id]",
                "  evidence <task-id> <path> [note]",
                "  verify <task-id>",
                "  advance <task-id>",
                "  archive <task-id...> [--reason reason]",
                "  close <task-id> [--blocked reason]",
            ]
        )
    )
    return 0


def _search_args(args: list[str]) -> tuple[str, bool, int]:
    rebuild = False
    limit = 20
    query_parts: list[str] = []
    index = 0
    while index < len(args):
        value = args[index]
        if value == "--rebuild":
            rebuild = True
            index += 1
            continue
        if value == "--limit":
            if index + 1 >= len(args):
                raise CompanyError("Usage: --limit <number>")
            try:
                limit = int(args[index + 1])
            except ValueError as exc:
                raise CompanyError(f"Invalid number for --limit: {args[index + 1]}") from exc
            index += 2
            continue
        query_parts.append(value)
        index += 1
    return " ".join(query_parts).strip(), rebuild, limit


def _archive_args(args: list[str]) -> tuple[list[str], str]:
    if not args:
        raise CompanyError("Usage: company archive <task-id...> [--reason reason]")
    task_ids: list[str] = []
    reason_parts: list[str] = []
    in_reason = False
    for arg in args:
        if arg == "--reason":
            in_reason = True
            continue
        if in_reason:
            reason_parts.append(arg)
        else:
            task_ids.append(arg)
    if not task_ids:
        raise CompanyError("Usage: company archive <task-id...> [--reason reason]")
    return task_ids, " ".join(reason_parts).strip()


def _goal(root: Path, args: list[str]) -> int:
    if not args or args[0] in {"status", "show"}:
        print(render_goal_status(root))
        return 0
    if args[0] in {"set", "start"}:
        max_iterations = _arg_int(args, "--max-iterations", 12)
        objective = " ".join(_strip_option(args[1:], "--max-iterations")).strip()
        path = set_goal(root, objective, max_iterations=max_iterations)
        print(f"Wrote {rel(root, path)}")
        return 0
    if args[0] in {"run", "step"}:
        dry_run = "--real" not in args
        max_iterations = _arg_int(args, "--max-iterations", 12)
        path = run_goal(root, dry_run=dry_run, max_iterations=max_iterations)
        print(f"Wrote {rel(root, path)}")
        return 0
    raise CompanyError("Usage: company goal status | set <objective> | run [--real] [--max-iterations N]")


def _arg_int(args: list[str], option: str, default: int) -> int:
    if option not in args:
        return default
    index = args.index(option)
    if index + 1 >= len(args):
        raise CompanyError(f"Missing value for {option}")
    try:
        return max(1, int(args[index + 1]))
    except ValueError as exc:
        raise CompanyError(f"Invalid integer for {option}: {args[index + 1]}") from exc


def _strip_option(args: list[str], option: str) -> list[str]:
    cleaned: list[str] = []
    skip_next = False
    for item in args:
        if skip_next:
            skip_next = False
            continue
        if item == option:
            skip_next = True
            continue
        cleaned.append(item)
    return cleaned


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
