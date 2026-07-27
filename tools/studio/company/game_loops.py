"""Game development loop receipts for the Studio cockpit."""

from __future__ import annotations

from pathlib import Path

from .errors import CompanyError
from .feedback import feedback_new
from .paths import rel
from .timeutil import now_iso, slugify
from .unity import unity_feedback_capture, unity_playtest


def game_feedback_loop(root: Path, args: list[str]) -> Path:
    """Run the playtest/capture/feedback loop and write a single receipt."""
    run_dir = root / "runs" / f"game-feedback-loop-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "game_feedback_loop.md"
    skip_playtest = "--no-playtest" in args

    playtest_path = None if skip_playtest else unity_playtest(root, [])
    if playtest_path and not _playtest_passed(playtest_path):
        raise CompanyError(
            "Feedback loop stopped because Unity playtest smoke failed; "
            f"see {rel(root, playtest_path)}"
        )
    capture_receipt, capture_path = unity_feedback_capture(root)
    feedback_path = feedback_new(root, capture_path)

    lines = [
        "# Game Feedback Loop",
        "",
        f"Checked: {now_iso()}",
        "Status: ready_for_review",
        "",
        "## Artifacts",
        "",
        f"- Playtest: {rel(root, playtest_path) if playtest_path else 'skipped by --no-playtest'}",
        f"- Game capture: {rel(root, capture_path)}",
        f"- Capture receipt: {rel(root, capture_receipt)}",
        f"- Feedback: {rel(root, feedback_path)}",
        "",
        "## Next Action",
        "",
        f"- Fill observation/requested change in {rel(root, feedback_path)}",
        f"- Then run: tools/channelctl feedback process {rel(root, feedback_path)}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _playtest_passed(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return (
        "Exit code: 0" in text
        and "Compile errors: 0" in text
        and "Playtest smoke: passed" in text
    )


def game_server_handoff(root: Path) -> Path:
    """Write a handoff receipt for the future x86_64 Linux server runner."""
    run_dir = root / "runs" / f"game-server-handoff-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "server_handoff.md"
    linux_build = _latest_linux_build(root)
    linux_build_ready = _linux_build_passed(linux_build)
    build_line = (
        rel(root, linux_build)
        if linux_build
        else "missing; run python tools/channelctl unity build linux-server"
    )
    status = (
        "waiting_for_x86_64_runner"
        if linux_build_ready
        else "waiting_for_linux_server_build"
    )
    if linux_build_ready:
        next_action = (
            "- Attach an x86_64 Linux runner or cloud host, then map "
            "gdx.runServer/gdx.runBots to that runner."
        )
    elif linux_build:
        next_action = (
            "- Resolve the blocked or failed Linux server build receipt above, "
            "rerun `python tools/channelctl unity build linux-server`, then "
            "regenerate this handoff."
        )
    else:
        next_action = (
            "- Run `python tools/channelctl unity build linux-server` on the "
            "build-authority editor, then regenerate this handoff."
        )

    lines = [
        "# x86_64 Server Soak Handoff",
        "",
        f"Checked: {now_iso()}",
        f"Status: {status}",
        "",
        "## Current Topology",
        "",
        "- Mac Studio: Unity editor, local playtest, capture, Mac/Linux build authority.",
        "- gdx1: ARM/aarch64 AI/ops worker, repo sync, log collection.",
        "- x86_64 Linux runner: required for real Unity dedicated server soak.",
        "",
        "## Required Runner Contract",
        "",
        "- Architecture: x86_64 Linux.",
        "- Access: SSH or host-runner endpoint.",
        "- Inputs: repo checkout, Linux dedicated server build, bot runner script.",
        "- Outputs: server log, bot log, soak receipt, captured failure reasons.",
        "",
        "## Current Build Evidence",
        "",
        f"- Linux server build receipt: {build_line}",
        "",
        "## Next Action",
        "",
        next_action,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _latest_linux_build(root: Path) -> Path | None:
    runs = sorted(
        (root / "runs").glob("unity-build-linux-server-*"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
        reverse=True,
    )
    for run in runs:
        path = run / "unity_build.md"
        if path.exists():
            return path
    return None


def _linux_build_passed(path: Path | None) -> bool:
    if path is None or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return (
        "Build status: passed" in text
        and "Build output exists: True" in text
    )
