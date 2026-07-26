"""Unity project checks."""

from __future__ import annotations

import os
import re
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - macOS/Linux path is the supported local runner.
    fcntl = None

from .errors import CompanyError
from .timeutil import now_iso, slugify


UNITY_HUB_EDITOR_ROOT = Path("/Applications/Unity/Hub/Editor")
UNITY_FALLBACK = Path("/Applications/Unity/Hub/Editor/6000.4.9f1/Unity.app/Contents/MacOS/Unity")
PLAYTEST_MARKER = "CHANNEL_PLAY_PLAYTEST_SMOKE"
BUILD_MARKER = "CHANNEL_PLAY_BUILD_RESULT"
MANUAL_RECORDER_MARKER = "CHANNEL_PLAY_MANUAL_TRAVERSAL_RECORDER"
MANUAL_REVIEW_MARKER = "CHANNEL_PLAY_MANUAL_TRAVERSAL_REVIEW"
MANUAL_CAPTURE_SETUP_MARKER = "CHANNEL_PLAY_MANUAL_TRAVERSAL_CAPTURE_SETUP"
MANUAL_AUTO_CAPTURE_MARKER = "CHANNEL_PLAY_MANUAL_TRAVERSAL_AUTO_CAPTURE"
PYRAMID_MAZE_V2_MARKER = "CHANNEL_PLAY_PYRAMID_MAZE_V2"
SIM_CHECK_MARKER = "CHANNEL_PLAY_SIM_CHECK"
SEMANTIC_CHECK_MARKER = "CHANNEL_PLAY_SEMANTIC_CHECK"
AGENT_PLAYTEST_MARKER = "CHANNEL_PLAY_AGENT_PLAYTEST"


def _resolve_unity_editor(root: Path) -> Path:
    env_value = os.environ.get("UNITY_EDITOR")
    if env_value:
        return Path(env_value)

    project_version = _project_unity_version(root)
    if project_version:
        project_editor = UNITY_HUB_EDITOR_ROOT / project_version / "Unity.app" / "Contents" / "MacOS" / "Unity"
        if project_editor.exists():
            return project_editor

    if UNITY_FALLBACK.exists():
        return UNITY_FALLBACK

    installed = sorted(UNITY_HUB_EDITOR_ROOT.glob("*/Unity.app/Contents/MacOS/Unity"), reverse=True)
    if installed:
        return installed[0]

    return UNITY_FALLBACK


def resolve_unity_editor(root: Path | None = None) -> Path:
    """Resolve Unity while preserving the original public helper contract."""
    return _resolve_unity_editor(root or Path.cwd())


def _project_unity_version(root: Path) -> str | None:
    version_file = root / "ProjectSettings" / "ProjectVersion.txt"
    if not version_file.exists():
        return None

    for line in version_file.read_text(encoding="utf-8").splitlines():
        match = re.match(r"m_EditorVersion:\s*(\S+)", line)
        if match:
            return match.group(1)

    return None


def unity_check(root: Path, args: list[str]) -> Path:
    run_batch = "--batch" in args
    unity = _resolve_unity_editor(root)
    if not (root / "ProjectSettings" / "ProjectVersion.txt").exists():
        raise CompanyError("Unity ProjectSettings/ProjectVersion.txt not found.")
    run_dir = root / "runs" / f"unity-check-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_check.md"
    lines = [
        "# Unity Check",
        "",
        f"Checked: {now_iso()}",
        f"Unity editor: {unity}",
        f"Unity editor exists: {unity.exists()}",
        f"Project root: {root}",
        f"Batch mode requested: {run_batch}",
        "",
    ]
    if run_batch:
        if not unity.exists():
            raise CompanyError(f"Unity editor not found: {unity}")
        editor_log = run_dir / "Editor.log"
        result = _run_unity_batch(root, unity, editor_log, timeout=180)
        errors = _summarize_unity_errors(editor_log)
        lines.extend([f"Exit code: {result.returncode}", f"Editor log: {editor_log.relative_to(root)}", f"Compile errors: {len(errors)}"])
        if errors:
            lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    else:
        lines.append("Result: quick project check passed. Use `--batch` for Unity batchmode.")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_playtest(root: Path, args: list[str]) -> Path:
    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-playtest-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_playtest.md"
    lines = _unity_header("Unity Playtest Smoke", root, unity)

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(root, unity, editor_log, execute_method="ChannelPlayProductionValidator.RunPlaytestSmoke", timeout=240)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, PLAYTEST_MARKER)
    passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Playtest smoke: {'passed' if passed else 'failed'}",
            "",
            "## Playtest Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_build(root: Path, args: list[str]) -> Path:
    target = args[0] if args else "mac-dev"
    if target not in {"mac-dev", "linux-server"}:
        raise CompanyError("Usage: unity build [mac-dev|linux-server]")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-build-{target}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_build.md"
    lines = _unity_header("Unity Build", root, unity)
    lines.append(f"Target: {target}")
    lines.append("")

    if target == "linux-server":
        linux_support = _linux_build_support_path(unity)
        if linux_support.exists():
            editor_log = run_dir / "Editor.log"
            result = _run_unity_batch(root, unity, editor_log, execute_method="ChannelPlayProductionValidator.BuildLinuxServer", timeout=600)
            errors = _summarize_unity_errors(editor_log)
            markers = _matching_lines(editor_log, BUILD_MARKER)
            output = root / "builds" / "linux-server" / "channel_play_server"
            output_exists = output.exists()
            passed = result.returncode == 0 and not errors and output_exists and any("target=linux-server" in marker and "result=Succeeded" in marker for marker in markers)
            lines.extend(
                [
                    f"Linux build support checked: {linux_support}",
                    f"Linux build support exists: {linux_support.exists()}",
                    f"Exit code: {result.returncode}",
                    f"Editor log: {editor_log.relative_to(root)}",
                    f"Compile errors: {len(errors)}",
                    f"Build status: {'passed' if passed else 'failed'}",
                    "Build output: builds/linux-server/channel_play_server",
                    f"Build output exists: {output_exists}",
                    "",
                    "## Build Markers",
                    "",
                    *(markers or ["none"]),
                ]
            )
            if errors:
                lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"Wrote {log_path.relative_to(root)}")
            return log_path
        lines.extend(
            [
                "Status: blocked",
                f"Linux build support checked: {linux_support}",
                f"Linux build support exists: {linux_support.exists()}",
                "Reason: Unity Linux Build Support is not installed for the active Unity editor on this Mac.",
                "Next: add Linux Build Support / Dedicated Server Support in Unity Hub, then implement ChannelPlayProductionValidator.BuildLinuxServer.",
            ]
        )
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {log_path.relative_to(root)}")
        return log_path

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(root, unity, editor_log, execute_method="ChannelPlayProductionValidator.BuildMacDev", timeout=420)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, BUILD_MARKER)
    output_exists = (root / "builds" / "mac-dev" / "ChannelPlay.app").exists()
    passed = result.returncode == 0 and not errors and output_exists and any("result=Succeeded" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Build status: {'passed' if passed else 'failed'}",
            f"Build output: builds/mac-dev/ChannelPlay.app",
            f"Build output exists: {output_exists}",
            "",
            "## Build Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_manual_review_smoke(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity manual-review-smoke")
    return _run_manual_traversal_review(
        root,
        title="Unity Manual Traversal Review Smoke",
        run_prefix="unity-manual-review-smoke",
        execute_method="ChannelPlayManualTraversalReviewValidator.ValidateManualTraversalReviewTooling",
    )


def unity_manual_recorder_smoke(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity manual-recorder-smoke")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-manual-recorder-smoke-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_manual_recorder.md"
    lines = _unity_header("Unity Manual Traversal Recorder Smoke", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlayManualTraversalRecorderValidator.ValidateManualTraversalRecorder",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlayManualTraversalRecorderValidator.ValidateManualTraversalRecorder",
        timeout=240,
    )
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, MANUAL_RECORDER_MARKER)
    passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Manual traversal recorder: {'passed' if passed else 'failed'}",
            "",
            "## Recorder Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_manual_review(root: Path, args: list[str]) -> Path:
    if len(args) > 1:
        raise CompanyError("Usage: unity manual-review [manual_traversal_session.md]")
    env: dict[str, str] | None = None
    if args:
        receipt_path = Path(args[0])
        if not receipt_path.is_absolute():
            receipt_path = root / receipt_path
        if not receipt_path.exists():
            raise CompanyError(f"Manual traversal receipt not found: {receipt_path}")
        env = os.environ.copy()
        env["CHANNEL_PLAY_MANUAL_TRAVERSAL_RECEIPT"] = str(receipt_path)

    return _run_manual_traversal_review(
        root,
        title="Unity Manual Traversal Review",
        run_prefix="unity-manual-review",
        execute_method="ChannelPlayManualTraversalReviewValidator.ValidateLatestManualTraversalReview",
        env=env,
        receipt_path=Path(args[0]) if args else None,
    )


def unity_manual_finish(root: Path, args: list[str]) -> Path:
    if len(args) > 1:
        raise CompanyError("Usage: unity manual-finish [manual_traversal_session.md]")

    run_dir = _unique_run_dir(root, "unity-manual-finish")
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_manual_finish.md"

    if args:
        session_path = Path(args[0])
        if not session_path.is_absolute():
            session_path = root / session_path
    else:
        session_path = _find_latest_human_manual_session(root)

    lines = [
        "# Unity Manual Traversal Finish",
        "",
        f"Checked: {now_iso()}",
        f"Project root: {root}",
        f"Input mode: {'explicit' if args else 'latest-human-session'}",
        "",
    ]

    if session_path is None or not session_path.exists():
        lines.extend(
            [
                "## Result",
                "",
                "Status: `manual_finish_waiting_for_session`",
                "",
                "No human-operated `manual_traversal_session.md` was found under `runs/manual-traversal-review`.",
                "",
                "## Next Step",
                "",
                "1. In Unity Play Mode, follow the HUD route.",
                "2. Press `F9` at each of the six checkpoints.",
                "3. Press `F10` after route `6/6`.",
                "4. Run `tools/channelctl unity manual-finish`.",
            ]
        )
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {log_path.relative_to(root)}")
        return log_path

    review_path = unity_manual_review(root, [str(session_path)])
    review_text = review_path.read_text(encoding="utf-8", errors="ignore")
    markers = [line.strip() for line in review_text.splitlines() if MANUAL_REVIEW_MARKER in line]
    passed = "Manual traversal review: passed" in review_text and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            "## Result",
            "",
            "Status: `" + ("manual_finish_review_passed" if passed else "manual_finish_review_failed") + "`",
            "",
            "Session receipt:",
            "",
            "- `" + _relative_to_root(root, session_path) + "`",
            "",
            "Review receipt:",
            "",
            "- `" + _relative_to_root(root, review_path) + "`",
            "",
            "## Review Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_manual_capture_setup(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity manual-capture-setup")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-manual-capture-setup-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_manual_capture_setup.md"
    lines = _unity_header("Unity Manual Traversal Capture Setup", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlayManualTraversalCaptureSetupValidator.PrepareManualTraversalCapture",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlayManualTraversalCaptureSetupValidator.PrepareManualTraversalCapture",
        timeout=240,
    )
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, MANUAL_CAPTURE_SETUP_MARKER)
    passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Manual capture setup: {'passed' if passed else 'failed'}",
            "",
            "## Setup Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_manual_auto_capture(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity manual-auto-capture")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-manual-auto-capture-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_manual_auto_capture.md"
    lines = _unity_header("Unity Manual Traversal Auto Capture", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlayPyramidMazeV2AutoTraversalCapture.CaptureAutoTraversal",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlayPyramidMazeV2AutoTraversalCapture.CaptureAutoTraversal",
        timeout=300,
    )
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, MANUAL_AUTO_CAPTURE_MARKER)
    receipt_match = re.search(r'receipt="([^"]+)"', "\n".join(markers))
    session_receipt = receipt_match.group(1) if receipt_match else ""
    auto_passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    review_path: Path | None = None
    review_passed = False
    if auto_passed and session_receipt:
        review_path = unity_manual_review(root, [session_receipt])
        review_text = review_path.read_text(encoding="utf-8", errors="ignore")
        review_passed = "Manual traversal review: passed" in review_text and "result=passed" in review_text

    passed = auto_passed and review_passed
    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Manual traversal auto capture: {'passed' if passed else 'failed'}",
            f"Session receipt: {session_receipt or 'none'}",
            f"Review receipt: {review_path.relative_to(root) if review_path else 'none'}",
            "",
            "## Auto Capture Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_pyramid_maze_v2(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity pyramid-maze-v2")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-pyramid-maze-v2-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_pyramid_maze_v2.md"
    lines = _unity_header("Unity Pyramid Maze V2", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlayPyramidMazeV2Builder.BuildAndValidatePyramidMazeV2",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlayPyramidMazeV2Builder.BuildAndValidatePyramidMazeV2",
        timeout=300,
    )
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, PYRAMID_MAZE_V2_MARKER)
    passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Pyramid Maze V2: {'passed' if passed else 'failed'}",
            "",
            "## Maze Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_sim_check(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: unity sim-check")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-sim-check-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_sim_check.md"
    lines = _unity_header("Unity Simulation Check", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlaySimulationRunner.RunSimCheck",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    env = os.environ.copy()
    env["CHANNEL_PLAY_SIM_RUN_DIR"] = str(run_dir.relative_to(root))
    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlaySimulationRunner.RunSimCheck",
        timeout=240,
        env=env,
    )
    _write_process_streams(run_dir, result)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, SIM_CHECK_MARKER)
    receipt = run_dir / "receipt.md"
    passed = result.returncode == 0 and not errors and receipt.exists() and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Simulation check: {'passed' if passed else 'failed'}",
            f"Receipt: {receipt.relative_to(root) if receipt.exists() else 'none'}",
            "",
            "## Sim Check Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_semantic_check(root: Path, args: list[str]) -> Path:
    if len(args) != 1:
        raise CompanyError("Usage: unity semantic-check <asset-id>")

    asset_id = args[0]
    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"unity-semantic-check-{slugify(asset_id)}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_semantic_check.md"
    lines = _unity_header("Unity Asset Semantic Check", root, unity)
    lines.extend(
        [
            "Execute method: ChannelPlayAssetSemanticValidator.ValidateSemanticPack",
            f"Asset ID: {asset_id}",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    env = os.environ.copy()
    env["CHANNEL_PLAY_SEMANTIC_ASSET_ID"] = asset_id
    env["CHANNEL_PLAY_SEMANTIC_RUN_DIR"] = str(run_dir.relative_to(root))
    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlayAssetSemanticValidator.ValidateSemanticPack",
        timeout=240,
        env=env,
    )
    _write_process_streams(run_dir, result)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, SEMANTIC_CHECK_MARKER)
    receipt = run_dir / "receipt.md"
    passed = result.returncode == 0 and not errors and receipt.exists() and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Semantic check: {'passed' if passed else 'failed'}",
            f"Receipt: {receipt.relative_to(root) if receipt.exists() else 'none'}",
            "",
            "## Semantic Check Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_agent_playtest(root: Path, args: list[str]) -> Path:
    if not args or args[0] != "pyramid-maze-v2":
        raise CompanyError("Usage: unity agent-playtest pyramid-maze-v2 --agent scripted")
    agent = "scripted"
    if "--agent" in args:
        index = args.index("--agent")
        if index + 1 >= len(args):
            raise CompanyError("Missing value for --agent")
        agent = args[index + 1]
    if agent != "scripted":
        raise CompanyError("Only --agent scripted is implemented in this phase.")

    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"agent-playtest-pyramid-maze-v2-scripted-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_agent_playtest.md"
    lines = _unity_header("Unity Agent Playtest", root, unity)
    lines.extend(
        [
            "Environment: pyramid-maze-v2",
            "Agent: scripted",
            "Execute method: ChannelPlaySimulationRunner.RunPyramidMazeV2ScriptedAgentPlaytest",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    env = os.environ.copy()
    env["CHANNEL_PLAY_SIM_RUN_DIR"] = str(run_dir.relative_to(root))
    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(
        root,
        unity,
        editor_log,
        execute_method="ChannelPlaySimulationRunner.RunPyramidMazeV2ScriptedAgentPlaytest",
        timeout=360,
        env=env,
    )
    _write_process_streams(run_dir, result)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, AGENT_PLAYTEST_MARKER)
    required = [
        "receipt.md",
        "review.md",
        "command.json",
        "scene_state.json",
        "semantic_labels.json",
        "actions.jsonl",
        "metrics.jsonl",
        "trajectory.json",
        "collisions.jsonl",
    ]
    missing = [name for name in required if not (run_dir / name).exists()]
    observations = sorted((run_dir / "observations").glob("frame_*_rgb.png")) if (run_dir / "observations").exists() else []
    passed = result.returncode == 0 and not errors and not missing and len(observations) >= 5 and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Agent playtest: {'passed' if passed else 'failed'}",
            f"Observation RGB frames: {len(observations)}",
            f"Missing artifacts: {', '.join(missing) if missing else 'none'}",
            f"Receipt: {run_dir.relative_to(root) / 'receipt.md'}",
            "",
            "## Agent Playtest Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_sim_review(root: Path, args: list[str]) -> Path:
    if len(args) != 1:
        raise CompanyError("Usage: unity sim-review <run-dir>")
    source = Path(args[0])
    if not source.is_absolute():
        source = root / source
    if not source.exists() or not source.is_dir():
        raise CompanyError(f"Agent run directory not found: {source}")

    run_dir = _unique_run_dir(root, "unity-sim-review")
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_sim_review.md"
    required = [
        "receipt.md",
        "review.md",
        "command.json",
        "scene_state.json",
        "semantic_labels.json",
        "actions.jsonl",
        "metrics.jsonl",
        "trajectory.json",
        "collisions.jsonl",
    ]
    missing = [name for name in required if not (source / name).exists()]
    rgb_frames = sorted((source / "observations").glob("frame_*_rgb.png")) if (source / "observations").exists() else []
    action_lines = _count_nonempty_lines(source / "actions.jsonl")
    metric_lines = _count_nonempty_lines(source / "metrics.jsonl")
    passed = not missing and len(rgb_frames) >= 5 and action_lines > 0 and metric_lines > 0

    lines = [
        "# Unity Simulation Review",
        "",
        f"Checked: {now_iso()}",
        f"Source run: {_relative_to_root(root, source)}",
        "",
        "## Result",
        "",
        f"Status: `{'sim_review_passed' if passed else 'sim_review_failed'}`",
        f"RGB observations: `{len(rgb_frames)}`",
        f"Action lines: `{action_lines}`",
        f"Metric lines: `{metric_lines}`",
        f"Missing artifacts: `{', '.join(missing) if missing else 'none'}`",
        "",
        "## Next Command",
        "",
        f"`tools/channelctl unity sim-replay {_relative_to_root(root, source)}`",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_sim_replay(root: Path, args: list[str]) -> Path:
    if len(args) != 1:
        raise CompanyError("Usage: unity sim-replay <run-dir>")
    source = Path(args[0])
    if not source.is_absolute():
        source = root / source
    if not source.exists() or not source.is_dir():
        raise CompanyError(f"Agent run directory not found: {source}")

    run_dir = _unique_run_dir(root, "unity-sim-replay")
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_sim_replay.md"
    replay_index = _build_replay_index(root, source, run_dir)
    replay_index_path = run_dir / "replay_index.json"
    review_notes_path = run_dir / "review_notes.json"
    receipt = run_dir / "receipt.md"
    replay_index_path.write_text(json.dumps(replay_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_notes = _build_review_notes(root, source, replay_index)
    review_notes_path.write_text(json.dumps(review_notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    frame_count = len(replay_index["frames"])
    action_count = len(replay_index["actions"])
    metric_count = len(replay_index["metrics"])
    passed = frame_count > 0 and action_count > 0 and metric_count > 0
    receipt.write_text(
        "\n".join(
            [
                "# Unity Simulation Replay Receipt",
                "",
                f"Checked: {now_iso()}",
                f"Status: `{'sim_replay_passed' if passed else 'sim_replay_failed'}`",
                f"Source run: `{_relative_to_root(root, source)}`",
                f"Frames: `{frame_count}`",
                f"Actions: `{action_count}`",
                f"Metrics: `{metric_count}`",
                f"Replay index: `{_relative_to_root(root, replay_index_path)}`",
                f"Review notes: `{_relative_to_root(root, review_notes_path)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    lines = [
        "# Unity Simulation Replay",
        "",
        f"Checked: {now_iso()}",
        f"Source run: {_relative_to_root(root, source)}",
        f"Status: `{'sim_replay_passed' if passed else 'sim_replay_failed'}`",
        "",
        "## Replay Index",
        "",
        f"- Frames: `{frame_count}`",
        f"- Actions: `{action_count}`",
        f"- Metrics: `{metric_count}`",
        f"- Replay index: `{_relative_to_root(root, replay_index_path)}`",
        f"- Review notes: `{_relative_to_root(root, review_notes_path)}`",
        f"- Receipt: `{_relative_to_root(root, receipt)}`",
        "",
        "## Frames",
        "",
        *[f"- `{frame['rgb']}` route=`{frame.get('routeMarker', 'unknown')}`" for frame in replay_index["frames"][:20]],
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def unity_sim_compare(root: Path, args: list[str]) -> Path:
    if len(args) != 2:
        raise CompanyError("Usage: unity sim-compare <run-a> <run-b>")
    first = _resolve_run_dir(root, args[0])
    second = _resolve_run_dir(root, args[1])

    run_dir = _unique_run_dir(root, "unity-sim-compare")
    run_dir.mkdir(parents=True, exist_ok=True)
    first_summary = _summarize_agent_run(root, first)
    second_summary = _summarize_agent_run(root, second)
    diffs = _compare_run_summaries(first_summary, second_summary)
    diff_lines = [f"- {diff}" for diff in diffs] if diffs else ["none"]
    passed = not diffs
    comparison = {
        "status": "sim_compare_passed" if passed else "sim_compare_changed",
        "checkedAt": now_iso(),
        "first": first_summary,
        "second": second_summary,
        "diffs": diffs,
    }
    comparison_path = run_dir / "comparison.json"
    receipt = run_dir / "receipt.md"
    log_path = run_dir / "unity_sim_compare.md"
    comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(
        "\n".join(
            [
                "# Unity Simulation Comparison Receipt",
                "",
                f"Checked: {now_iso()}",
                f"Status: `{'sim_compare_passed' if passed else 'sim_compare_changed'}`",
                f"First run: `{_relative_to_root(root, first)}`",
                f"Second run: `{_relative_to_root(root, second)}`",
                f"Diff count: `{len(diffs)}`",
                f"Comparison: `{_relative_to_root(root, comparison_path)}`",
                "",
                "## Diffs",
                "",
                *diff_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )
    log_path.write_text(
        "\n".join(
            [
                "# Unity Simulation Comparison",
                "",
                f"Checked: {now_iso()}",
                f"Status: `{'sim_compare_passed' if passed else 'sim_compare_changed'}`",
                f"First run: `{_relative_to_root(root, first)}`",
                f"Second run: `{_relative_to_root(root, second)}`",
                f"Comparison: `{_relative_to_root(root, comparison_path)}`",
                f"Receipt: `{_relative_to_root(root, receipt)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def _build_replay_index(root: Path, source: Path, replay_run_dir: Path) -> dict:
    actions = _read_jsonl(source / "actions.jsonl")
    metrics = _read_jsonl(source / "metrics.jsonl")
    trajectory = _read_json(source / "trajectory.json", default={"points": []})
    frames = []
    observation_dir = source / "observations"
    rgb_frames = sorted(observation_dir.glob("frame_*_rgb.png")) if observation_dir.exists() else []
    for rgb in rgb_frames:
        frame_number = _frame_number(rgb)
        metadata_path = observation_dir / f"frame_{frame_number:03d}.json"
        metadata = _read_json(metadata_path, default={})
        frames.append(
            {
                "frame": frame_number,
                "rgb": _relative_to_root(root, rgb),
                "segmentation": _relative_to_root(root, observation_dir / f"frame_{frame_number:03d}_segmentation.png"),
                "depth": _relative_to_root(root, observation_dir / f"frame_{frame_number:03d}_depth.png"),
                "metadata": _relative_to_root(root, metadata_path),
                "routeMarker": metadata.get("routeMarker", ""),
                "agentId": metadata.get("agentId", ""),
                "reviewNoteId": f"frame-{frame_number:03d}",
            }
        )
    return {
        "status": "replay_index_ready",
        "generatedAt": now_iso(),
        "sourceRun": _relative_to_root(root, source),
        "replayRun": _relative_to_root(root, replay_run_dir),
        "frames": frames,
        "actions": actions,
        "metrics": metrics,
        "trajectory": trajectory,
    }


def _build_review_notes(root: Path, source: Path, replay_index: dict) -> dict:
    return {
        "status": "review_notes_ready",
        "generatedAt": now_iso(),
        "sourceRun": replay_index["sourceRun"],
        "sourceReview": _relative_to_root(root, source / "review.md"),
        "frames": [
            {
                "id": frame["reviewNoteId"],
                "frame": frame["frame"],
                "routeMarker": frame.get("routeMarker", ""),
                "target": frame["rgb"],
                "note": "",
                "status": "open",
            }
            for frame in replay_index["frames"]
        ],
        "actions": [
            {
                "id": f"action-{int(action.get('step', index)):03d}",
                "step": action.get("step", index),
                "action": action.get("action", ""),
                "target": action.get("target", ""),
                "note": "",
                "status": "open",
            }
            for index, action in enumerate(replay_index["actions"])
        ],
    }


def _resolve_run_dir(root: Path, value: str) -> Path:
    source = Path(value)
    if not source.is_absolute():
        source = root / source
    if not source.exists() or not source.is_dir():
        raise CompanyError(f"Agent run directory not found: {source}")
    return source


def _summarize_agent_run(root: Path, source: Path) -> dict:
    metrics = _read_jsonl(source / "metrics.jsonl")
    actions = _read_jsonl(source / "actions.jsonl")
    trajectory = _read_json(source / "trajectory.json", default={"points": []})
    rgb_frames = sorted((source / "observations").glob("frame_*_rgb.png")) if (source / "observations").exists() else []
    route = [metric.get("marker", "") for metric in metrics if metric.get("marker")]
    return {
        "run": _relative_to_root(root, source),
        "rgbFrames": len(rgb_frames),
        "actions": len(actions),
        "metrics": len(metrics),
        "route": route,
        "trajectoryPoints": len(trajectory.get("points", [])) if isinstance(trajectory, dict) else 0,
        "maxCollisionCount": max([int(metric.get("collisionCount", 0) or 0) for metric in metrics] or [0]),
        "maxStuckSeconds": max([float(metric.get("stuckSeconds", 0) or 0) for metric in metrics] or [0]),
        "routeCompletion": bool(route) and route[-1] == "MazeV2_Rear_Service_Exit",
    }


def _compare_run_summaries(first: dict, second: dict) -> list[str]:
    diffs: list[str] = []
    for key in ["rgbFrames", "actions", "metrics", "trajectoryPoints", "maxCollisionCount", "maxStuckSeconds", "routeCompletion"]:
        if first.get(key) != second.get(key):
            diffs.append(f"{key}: {first.get(key)} -> {second.get(key)}")
    if first.get("route") != second.get("route"):
        diffs.append("route sequence changed")
    return diffs


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            rows.append({"parseError": stripped[:200]})
    return rows


def _read_json(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except json.JSONDecodeError:
        return default


def _frame_number(path: Path) -> int:
    match = re.search(r"frame_(\d+)_", path.name)
    return int(match.group(1)) if match else 0


def _summarize_unity_errors(log_path: Path) -> list[str]:
    if not log_path.exists():
        return []
    errors: list[str] = []
    for line in log_path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        if re.search(r"\berror\s+CS\d+", stripped, flags=re.IGNORECASE):
            errors.append(stripped[:240])
        elif re.search(r"(^|\s)(Unhandled\s+)?[A-Za-z0-9_.]*Exception:", stripped):
            errors.append(stripped[:240])
    return errors


def _unity_header(title: str, root: Path, unity: Path) -> list[str]:
    return [
        f"# {title}",
        "",
        f"Checked: {now_iso()}",
        f"Unity editor: {unity}",
        f"Unity editor exists: {unity.exists()}",
        f"Project root: {root}",
        "",
    ]


def _find_latest_human_manual_session(root: Path) -> Path | None:
    manual_root = root / "runs" / "manual-traversal-review"
    if not manual_root.exists():
        return None

    sessions = sorted(
        manual_root.glob("**/manual_traversal_session.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return sessions[0] if sessions else None


def _unique_run_dir(root: Path, prefix: str) -> Path:
    base = root / "runs" / f"{prefix}-{slugify(now_iso())}"
    if not base.exists():
        return base

    suffix = 2
    while True:
        candidate = root / "runs" / f"{prefix}-{slugify(now_iso())}-{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _run_unity_batch(
    root: Path,
    unity: Path,
    editor_log: Path,
    *,
    timeout: int,
    execute_method: str = "",
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        str(unity),
        "-batchmode",
        "-quit",
        "-projectPath",
        str(root),
    ]
    if execute_method:
        command.extend(["-executeMethod", execute_method])
    command.extend(["-logFile", str(editor_log)])
    with _unity_batch_lock(root):
        return subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )


@contextmanager
def _unity_batch_lock(root: Path):
    lock_dir = root / "runs"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".unity-batch.lock"
    with lock_path.open("w", encoding="utf-8") as lock_file:
        lock_file.write(f"pid={os.getpid()}\n")
        lock_file.flush()
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _linux_build_support_path(unity: Path) -> Path:
    editor_root = unity.parents[3]
    return editor_root / "PlaybackEngines" / "LinuxStandaloneSupport"


def _matching_lines(log_path: Path, marker: str) -> list[str]:
    if not log_path.exists():
        return []
    return [line.strip()[:300] for line in log_path.read_text(errors="ignore").splitlines() if marker in line]


def _count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def _write_process_streams(run_dir: Path, result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        (run_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8", errors="ignore")
    if result.stderr:
        (run_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8", errors="ignore")


def _run_manual_traversal_review(
    root: Path,
    *,
    title: str,
    run_prefix: str,
    execute_method: str,
    env: dict[str, str] | None = None,
    receipt_path: Path | None = None,
) -> Path:
    unity = _resolve_unity_editor(root)
    run_dir = root / "runs" / f"{run_prefix}-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_manual_review.md"
    lines = _unity_header(title, root, unity)
    lines.extend(
        [
            f"Execute method: {execute_method}",
            f"Input receipt: {receipt_path or 'latest'}",
            "",
        ]
    )

    if not unity.exists():
        raise CompanyError(f"Unity editor not found: {unity}")

    editor_log = run_dir / "Editor.log"
    result = _run_unity_batch(root, unity, editor_log, execute_method=execute_method, timeout=240, env=env)
    errors = _summarize_unity_errors(editor_log)
    markers = _matching_lines(editor_log, MANUAL_REVIEW_MARKER)
    passed = result.returncode == 0 and not errors and any("result=passed" in marker for marker in markers)

    lines.extend(
        [
            f"Exit code: {result.returncode}",
            f"Editor log: {editor_log.relative_to(root)}",
            f"Compile errors: {len(errors)}",
            f"Manual traversal review: {'passed' if passed else 'failed'}",
            "",
            "## Review Markers",
            "",
            *(markers or ["none"]),
        ]
    )
    if errors:
        lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path
