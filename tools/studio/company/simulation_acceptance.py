"""Final acceptance gate for the Channel Play simulation stack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .asset_forge import asset_semantic_pack
from .errors import CompanyError
from .paths import rel
from .timeutil import now_iso, slugify
from .unity import (
    unity_agent_playtest,
    unity_semantic_check,
    unity_sim_check,
    unity_sim_compare,
    unity_sim_replay,
    unity_sim_review,
)


def sim_acceptance_check(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: sim-acceptance check")

    run_dir = _unique_run_dir(root, "sim-acceptance")
    run_dir.mkdir(parents=True, exist_ok=False)
    latest_agent_run = _latest(root, "agent-playtest-pyramid-maze-v2-scripted-")
    checks = _build_checks(root, latest_agent_run)
    passed = all(check["passed"] for check in checks)
    report = {
        "schema": "channel_play.sim_acceptance.v1",
        "checkedAt": now_iso(),
        "status": "sim_acceptance_passed" if passed else "sim_acceptance_failed",
        "checks": checks,
    }
    report_path = run_dir / "acceptance_report.json"
    receipt = run_dir / "receipt.md"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_receipt(root, report, report_path), encoding="utf-8")
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def sim_acceptance_handoff(root: Path, args: list[str]) -> Path:
    if args:
        raise CompanyError("Usage: sim-acceptance handoff")

    acceptance = _latest(root, "sim-acceptance-")
    if not acceptance:
        raise CompanyError("No sim-acceptance run found. Run: tools/channelctl sim-acceptance check")

    run_dir = _unique_run_dir(root, "sim-handoff")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = _handoff_manifest(root, acceptance, run_dir)
    manifest_path = run_dir / "handoff_manifest.json"
    handoff_path = run_dir / "handoff.md"
    receipt = run_dir / "receipt.md"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    handoff_path.write_text(_handoff_markdown(manifest), encoding="utf-8")
    receipt.write_text(
        "\n".join(
            [
                "# Simulation Handoff Receipt",
                "",
                f"Checked: {now_iso()}",
                "Status: `sim_handoff_ready`",
                f"Acceptance: `{manifest['acceptance']['receipt']}`",
                f"Handoff: `{rel(root, handoff_path)}`",
                f"Manifest: `{rel(root, manifest_path)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def sim_acceptance_proof_refresh(root: Path, args: list[str]) -> Path:
    collect_only = False
    semantic_asset_id = "pyramid_temple_full_environment"
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--collect-only":
            collect_only = True
            index += 1
            continue
        if arg == "--semantic-asset":
            if index + 1 >= len(args):
                raise CompanyError("Missing value for --semantic-asset")
            semantic_asset_id = args[index + 1]
            index += 2
            continue
        raise CompanyError("Usage: sim-acceptance proof-refresh [--collect-only] [--semantic-asset <asset-id>]")

    run_dir = _unique_run_dir(root, "sim-proof-refresh")
    run_dir.mkdir(parents=True, exist_ok=False)
    steps: list[dict[str, Any]] = []

    if collect_only:
        _collect_latest_steps(root, steps)
    else:
        _run_proof_step(
            root,
            steps,
            "asset_semantic_pack",
            f"tools/channelctl asset semantic-pack {semantic_asset_id}",
            lambda: asset_semantic_pack(root, semantic_asset_id),
            expected="semantic_pack_ready",
            required=False,
        )
        _run_proof_step(
            root,
            steps,
            "unity_semantic_check",
            f"tools/channelctl unity semantic-check {semantic_asset_id}",
            lambda: unity_semantic_check(root, [semantic_asset_id]),
            expected="semantic_check_passed",
        )
        _run_proof_step(
            root,
            steps,
            "unity_sim_check",
            "tools/channelctl unity sim-check",
            lambda: unity_sim_check(root, []),
            expected="sim_check_passed",
        )
        _run_proof_step(
            root,
            steps,
            "unity_agent_playtest",
            "tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted",
            lambda: unity_agent_playtest(root, ["pyramid-maze-v2", "--agent", "scripted"]),
            expected="agent_playtest_passed",
        )

        latest_agent_run = _latest(root, "agent-playtest-pyramid-maze-v2-scripted-")
        if latest_agent_run:
            latest_agent_rel = rel(root, latest_agent_run)
            _run_proof_step(
                root,
                steps,
                "unity_sim_review",
                f"tools/channelctl unity sim-review {latest_agent_rel}",
                lambda: unity_sim_review(root, [latest_agent_rel]),
                expected="sim_review_passed",
            )
            _run_proof_step(
                root,
                steps,
                "unity_sim_replay",
                f"tools/channelctl unity sim-replay {latest_agent_rel}",
                lambda: unity_sim_replay(root, [latest_agent_rel]),
                expected="sim_replay_passed",
            )

            previous_agent_run = _previous(root, "agent-playtest-pyramid-maze-v2-scripted-", latest_agent_run)
            if previous_agent_run:
                previous_agent_rel = rel(root, previous_agent_run)
                _run_proof_step(
                    root,
                    steps,
                    "unity_sim_compare",
                    f"tools/channelctl unity sim-compare {latest_agent_rel} {previous_agent_rel}",
                    lambda: unity_sim_compare(root, [latest_agent_rel, previous_agent_rel]),
                    expected="sim_compare_",
                    required=False,
                )
            else:
                steps.append(_step("unity_sim_compare", "skipped", "No previous scripted agent run to compare.", required=False))
        else:
            steps.append(_step("unity_sim_review", "failed", "No scripted agent run was available after playtest.", required=True))
            steps.append(_step("unity_sim_replay", "failed", "No scripted agent run was available after playtest.", required=True))

        _run_proof_step(
            root,
            steps,
            "sim_acceptance_check",
            "tools/channelctl sim-acceptance check",
            lambda: sim_acceptance_check(root, []),
            expected="sim_acceptance_passed",
            required=False,
        )
        _run_proof_step(
            root,
            steps,
            "sim_acceptance_handoff",
            "tools/channelctl sim-acceptance handoff",
            lambda: sim_acceptance_handoff(root, []),
            expected="sim_handoff_ready",
            required=False,
        )

    report = {
        "schema": "channel_play.sim_proof_refresh.v1",
        "checkedAt": now_iso(),
        "status": _proof_refresh_status(steps, collect_only=collect_only),
        "mode": "collect_only" if collect_only else "run",
        "semanticAssetId": semantic_asset_id,
        "steps": steps,
        "evidence": _proof_evidence(root),
    }
    report_path = run_dir / "proof_bundle.json"
    receipt = run_dir / "receipt.md"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.write_text(_proof_refresh_receipt(root, report, report_path), encoding="utf-8")
    print(f"Wrote {rel(root, receipt)}")
    return receipt


def _build_checks(root: Path, latest_agent_run: Path | None) -> list[dict[str, Any]]:
    latest_sim_check = _latest(root, "unity-sim-check-")
    latest_semantic_check = _latest(root, "unity-semantic-check-")
    latest_replay = _latest(root, "unity-sim-replay-")
    latest_simworld = _latest(root, "simworld-probe-")
    codex_run = _latest(root, "external-agent-codex-")
    openclaw_run = _latest(root, "external-agent-openclaw-")
    external_compare = _latest(root, "external-agent-compare-")

    rgb_count = _count(latest_agent_run, "observations/*_rgb.png")
    segmentation_count = _count(latest_agent_run, "observations/*_segmentation.png")
    depth_count = _count(latest_agent_run, "observations/*_depth.png")
    required_agent_files = ["receipt.md", "actions.jsonl", "metrics.jsonl", "trajectory.json", "scene_state.json", "semantic_labels.json"]

    return [
        _check("unity_sim_check", "unity sim-check passes", _receipt_has(latest_sim_check, "sim_check_passed"), latest_sim_check),
        _check("unity_agent_playtest", "scripted agent playtest passes", _receipt_has(latest_agent_run, "agent_playtest_passed"), latest_agent_run),
        _check(
            "agent_run_artifacts",
            "agent run includes observations/actions/metrics/trajectory/receipt",
            bool(latest_agent_run)
            and rgb_count >= 6
            and all((latest_agent_run / name).exists() for name in required_agent_files),
            latest_agent_run,
            {"rgb": rgb_count, "requiredFiles": required_agent_files},
        ),
        _check("studio_screen", "Studio shows run and artifact controls", _studio_screen_ready(root), root / "tools/studio/app/app.js"),
        _check("rgb_sensor", "RGB sensor works", rgb_count >= 6, latest_agent_run, {"rgb": rgb_count}),
        _check("segmentation_sensor", "segmentation labels work", segmentation_count >= 6 and _exists(latest_agent_run, "semantic_labels.json"), latest_agent_run, {"segmentation": segmentation_count}),
        _check("depth_documented", "depth placeholder or capture is documented", depth_count >= 6 and _metadata_has_depth(latest_agent_run), latest_agent_run, {"depth": depth_count}),
        _check("feedback_targets", "human feedback attaches to frame/action", _review_notes_ready(latest_replay), latest_replay),
        _check("semantic_pack_consumed", "Asset Forge semantic pack is consumed", _receipt_has(latest_semantic_check, "semantic_check_passed"), latest_semantic_check),
        _check("external_agents", "at least 2 external agents use the same action schema", _external_agents_ready(codex_run, openclaw_run, external_compare), external_compare),
        _check("orchestrator_decomposition", "orchestrator decomposes goal into game/asset tasks", _orchestrator_ready(root), root / "memory/company/task_board.json"),
        _check("gdx_or_fallback", "gdx1 or fallback worker handles long-running work", bool(latest_simworld) and _receipt_has(latest_agent_run, "agent_playtest_passed"), latest_simworld),
        _check("receipt_backed", "completion states have receipt-backed proof", _required_receipts_exist([latest_sim_check, latest_agent_run, latest_semantic_check, latest_replay, codex_run, openclaw_run, external_compare]), root / "runs"),
        _check("one_screen_status", "user can understand status/result from one Studio screen", _one_screen_ready(root), root / "tools/studio/app/app.js"),
    ]


def _handoff_manifest(root: Path, acceptance: Path, handoff_run_dir: Path) -> dict[str, Any]:
    report = _read_json(acceptance / "acceptance_report.json", default={})
    checks = report.get("checks") if isinstance(report.get("checks"), list) else []
    failed = [check for check in checks if not check.get("passed")]
    live_check = _latest(root, "external-agent-live-check-")
    live_report = _read_json(live_check / "live_check.json", default={}) if live_check else {}
    latest_simworld = _latest(root, "simworld-probe-")
    latest_simworld_doctor = _latest(root, "simworld-doctor-")
    simworld_doctor_report = _read_json(latest_simworld_doctor / "doctor.json", default={}) if latest_simworld_doctor else {}
    evidence = {
        "acceptance": _latest_receipt(root, "sim-acceptance-"),
        "unitySimCheck": _latest_receipt(root, "unity-sim-check-"),
        "agentPlaytest": _latest_receipt(root, "agent-playtest-pyramid-maze-v2-scripted-"),
        "semanticCheck": _latest_receipt(root, "unity-semantic-check-"),
        "replay": _latest_receipt(root, "unity-sim-replay-"),
        "simworldProbe": _latest_receipt(root, "simworld-probe-"),
        "simworldDoctor": _latest_receipt(root, "simworld-doctor-"),
        "simworldInstallBase": _latest_receipt(root, "simworld-install-base-"),
        "simworldRoutePlan": _latest_receipt(root, "simworld-route-plan-"),
        "simworldStartServer": _latest_receipt(root, "simworld-start-server-"),
        "simworldWorkerGuide": _latest_receipt(root, "simworld-worker-guide-"),
        "codexBridge": _latest_receipt(root, "external-agent-codex-"),
        "openclawBridge": _latest_receipt(root, "external-agent-openclaw-"),
        "agentCompare": _latest_receipt(root, "external-agent-compare-"),
        "liveAgentBridge": _latest_receipt(root, "external-agent-live-check-"),
    }
    known_blocked = []
    if not _receipt_has(latest_simworld, "simworld_probe_ready"):
        failures = simworld_doctor_report.get("failures") if isinstance(simworld_doctor_report.get("failures"), list) else []
        reason = "; ".join(str(item) for item in failures) if failures else "latest SimWorld probe is not ready"
        latest = _latest_receipt(root, "simworld-doctor-") or _latest_receipt(root, "simworld-probe-")
        known_blocked.append(f"gdx1 SimWorld server is not ready: {reason}; latest receipt {latest}.")
    if live_report.get("status") != "external_agent_live_check_passed":
        latest = _latest_receipt(root, "external-agent-live-check-")
        if latest:
            known_blocked.append(f"External AI bridge live check is not passed yet: {live_report.get('status', 'unknown')}; latest receipt {latest}.")
        else:
            known_blocked.append("External AI bridge live check has not produced a receipt yet.")
    return {
        "schema": "channel_play.sim_handoff.v1",
        "createdAt": now_iso(),
        "status": "sim_handoff_ready" if not failed and report.get("status") == "sim_acceptance_passed" else "sim_handoff_needs_attention",
        "handoffRun": rel(root, handoff_run_dir),
        "acceptance": {
            "run": rel(root, acceptance),
            "receipt": rel(root, acceptance / "receipt.md"),
            "report": rel(root, acceptance / "acceptance_report.json"),
            "status": report.get("status", "unknown"),
            "passedChecks": sum(1 for check in checks if check.get("passed")),
            "totalChecks": len(checks),
        },
        "evidence": evidence,
        "knownBlocked": known_blocked,
        "nextCommands": [
            "tools/channelctl sim-acceptance check",
            "tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted",
            "tools/channelctl unity sim-replay runs/agent-playtest-pyramid-maze-v2-scripted-2026-06-07t15-21-50-09-00",
            "tools/channelctl sim-agent run codex runs/agent-playtest-pyramid-maze-v2-scripted-2026-06-07t15-21-50-09-00",
            "tools/channelctl sim-agent live-check all runs/agent-playtest-pyramid-maze-v2-scripted-2026-06-07t15-21-50-09-00 --timeout 240",
        ],
    }


def _latest_receipt(root: Path, prefix: str) -> str:
    run = _latest(root, prefix)
    if not run:
        return ""
    receipt = run / "receipt.md"
    return rel(root, receipt) if receipt.exists() else rel(root, run)


def _handoff_markdown(manifest: dict[str, Any]) -> str:
    acceptance = manifest["acceptance"]
    lines = [
        "# Channel Play Simulation Handoff",
        "",
        f"Created: {manifest['createdAt']}",
        f"Status: `{manifest['status']}`",
        "",
        "## Acceptance",
        "",
        f"- Status: `{acceptance['status']}`",
        f"- Checks: `{acceptance['passedChecks']}/{acceptance['totalChecks']}`",
        f"- Receipt: `{acceptance['receipt']}`",
        f"- Report: `{acceptance['report']}`",
        "",
        "## Evidence",
        "",
    ]
    for key, path in manifest["evidence"].items():
        lines.append(f"- {key}: `{path or 'missing'}`")
    lines.extend(["", "## Known Blocked", ""])
    lines.extend(f"- {item}" for item in manifest["knownBlocked"])
    lines.extend(["", "## Next Commands", ""])
    lines.extend(f"```bash\n{command}\n```" for command in manifest["nextCommands"])
    lines.append("")
    return "\n".join(lines)


def _check(check_id: str, label: str, passed: bool, evidence: Path | None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "passed": bool(passed),
        "evidence": str(evidence) if evidence else "",
        "details": details or {},
    }


def _run_proof_step(
    root: Path,
    steps: list[dict[str, Any]],
    step_id: str,
    command: str,
    action: Callable[[], Path],
    *,
    expected: str | None = None,
    required: bool = True,
) -> None:
    try:
        path = action()
        passed = _path_has(path, expected) if expected else path.exists()
        status = "passed" if passed else "failed"
        detail = f"Expected marker not found: {expected}" if expected and not passed else ""
        steps.append(_step(step_id, status, detail, path=path, command=command, required=required))
    except Exception as exc:
        steps.append(_step(step_id, "failed", str(exc), command=command, required=required))


def _collect_latest_steps(root: Path, steps: list[dict[str, Any]]) -> None:
    evidence = _proof_evidence(root)
    required = {
        "unitySimCheck": "sim_check_passed",
        "agentPlaytest": "agent_playtest_passed",
        "semanticCheck": "semantic_check_passed",
        "replay": "sim_replay_passed",
    }
    for key, marker in required.items():
        path = Path(evidence.get(key) or "")
        full_path = root / path if path and not path.is_absolute() else path
        passed = bool(path) and _path_has(full_path, marker)
        steps.append(
            _step(
                f"collect_{key}",
                "passed" if passed else "failed",
                "" if passed else f"Missing latest evidence marker: {marker}",
                path=full_path if path else None,
                required=True,
            )
        )


def _step(
    step_id: str,
    status: str,
    detail: str,
    *,
    path: Path | None = None,
    command: str = "",
    required: bool = True,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "status": status,
        "required": required,
        "command": command,
        "path": str(path) if path else "",
        "detail": detail,
    }


def _proof_refresh_status(steps: list[dict[str, Any]], *, collect_only: bool) -> str:
    required_failed = [step for step in steps if step.get("required") and step.get("status") != "passed"]
    advisory_failed = [step for step in steps if not step.get("required") and step.get("status") == "failed"]
    if required_failed:
        return "proof_refresh_incomplete" if collect_only else "proof_refresh_failed"
    if advisory_failed:
        return "proof_refresh_partial"
    return "proof_refresh_collected" if collect_only else "proof_refresh_passed"


def _proof_evidence(root: Path) -> dict[str, str]:
    latest_acceptance = _latest(root, "sim-acceptance-")
    latest_handoff = _latest(root, "sim-handoff-")
    return {
        "semanticPack": _latest_receipt(root, "asset-semantic-pack-"),
        "unitySimCheck": _latest_receipt(root, "unity-sim-check-"),
        "agentPlaytest": _latest_receipt(root, "agent-playtest-pyramid-maze-v2-scripted-"),
        "semanticCheck": _latest_receipt(root, "unity-semantic-check-"),
        "review": _latest_file(root, "unity-sim-review-", "unity_sim_review.md"),
        "replay": _latest_receipt(root, "unity-sim-replay-"),
        "compare": _latest_receipt(root, "unity-sim-compare-"),
        "acceptance": _latest_receipt(root, "sim-acceptance-"),
        "handoff": _latest_receipt(root, "sim-handoff-"),
        "acceptanceReport": rel(root, latest_acceptance / "acceptance_report.json") if latest_acceptance and (latest_acceptance / "acceptance_report.json").exists() else "",
        "handoffManifest": rel(root, latest_handoff / "handoff_manifest.json") if latest_handoff and (latest_handoff / "handoff_manifest.json").exists() else "",
    }


def _proof_refresh_receipt(root: Path, report: dict[str, Any], report_path: Path) -> str:
    failed = [step for step in report["steps"] if step["status"] != "passed"]
    lines = [
        "# Simulation Proof Refresh",
        "",
        f"Checked: {report['checkedAt']}",
        f"Status: `{report['status']}`",
        f"Mode: `{report['mode']}`",
        f"Semantic asset: `{report['semanticAssetId']}`",
        f"Proof bundle: `{rel(root, report_path)}`",
        "",
        "## Steps",
        "",
    ]
    for step in report["steps"]:
        marker = "pass" if step["status"] == "passed" else step["status"]
        path = _display_path(root, step.get("path", ""))
        lines.append(f"- `{marker}` {step['id']} -> `{path or 'none'}`")
        if step.get("detail"):
            lines.append(f"  - {step['detail']}")
    lines.extend(["", "## Evidence", ""])
    for key, path in report["evidence"].items():
        lines.append(f"- {key}: `{path or 'missing'}`")
    if failed:
        lines.extend(["", "## Attention", ""])
        lines.extend(f"- {step['id']}: {step.get('detail') or step['status']}" for step in failed)
    lines.append("")
    return "\n".join(lines)


def _path_has(path: Path | None, text: str | None) -> bool:
    if not path or not text:
        return False
    candidates = [path]
    if path.is_file():
        candidates.append(path.parent / "receipt.md")
    elif path.is_dir():
        candidates.append(path / "receipt.md")
    for candidate in candidates:
        if candidate.exists() and text in candidate.read_text(encoding="utf-8-sig", errors="ignore"):
            return True
    return False


def _previous(root: Path, prefix: str, current: Path) -> Path | None:
    base = root / "runs"
    if not base.exists():
        return None
    candidates = [path for path in base.iterdir() if path.is_dir() and path.name.startswith(prefix) and path != current]
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else None


def _latest_file(root: Path, prefix: str, filename: str) -> str:
    latest = _latest(root, prefix)
    path = latest / filename if latest else None
    return rel(root, path) if path and path.exists() else ""


def _display_path(root: Path, path: str) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if candidate.is_absolute() and str(candidate).startswith(str(root)):
        return rel(root, candidate)
    return path


def _latest(root: Path, prefix: str) -> Path | None:
    base = root / "runs"
    if not base.exists():
        return None
    candidates = [path for path in base.iterdir() if path.is_dir() and path.name.startswith(prefix)]
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else None


def _receipt_has(run_dir: Path | None, text: str) -> bool:
    if not run_dir:
        return False
    receipt = run_dir / "receipt.md"
    return receipt.exists() and text in receipt.read_text(encoding="utf-8-sig", errors="ignore")


def _exists(run_dir: Path | None, relative: str) -> bool:
    return bool(run_dir) and (run_dir / relative).exists()


def _count(run_dir: Path | None, pattern: str) -> int:
    return len(list(run_dir.glob(pattern))) if run_dir else 0


def _metadata_has_depth(run_dir: Path | None) -> bool:
    if not run_dir:
        return False
    metadata = run_dir / "observations" / "frame_000.json"
    return metadata.exists() and "depthStatus" in metadata.read_text(encoding="utf-8-sig", errors="ignore")


def _review_notes_ready(run_dir: Path | None) -> bool:
    if not run_dir:
        return False
    notes = _read_json(run_dir / "review_notes.json", default={})
    return bool(notes.get("frames")) and bool(notes.get("actions"))


def _external_agents_ready(codex_run: Path | None, openclaw_run: Path | None, compare_run: Path | None) -> bool:
    if not codex_run or not openclaw_run or not compare_run:
        return False
    codex = _read_json(codex_run / "response.json", default={})
    openclaw = _read_json(openclaw_run / "response.json", default={})
    return (
        codex.get("schema") == "channel_play.external_agent_response.v1"
        and openclaw.get("schema") == "channel_play.external_agent_response.v1"
        and _receipt_has(codex_run, "external_agent_run_passed")
        and _receipt_has(openclaw_run, "external_agent_run_passed")
        and _receipt_has(compare_run, "external_agent_compare_passed")
    )


def _orchestrator_ready(root: Path) -> bool:
    server = root / "tools/studio/workspace_server.py"
    board = _read_json(root / "memory/company/task_board.json", default={})
    tasks = board.get("tasks") if isinstance(board, dict) else []
    has_orchestrator = server.exists() and "orchestrator.run" in server.read_text(encoding="utf-8", errors="ignore")
    has_game_or_asset_tasks = any("asset" in json.dumps(task, ensure_ascii=False).lower() or "game" in json.dumps(task, ensure_ascii=False).lower() for task in tasks or [])
    return has_orchestrator and has_game_or_asset_tasks


def _studio_screen_ready(root: Path) -> bool:
    app = root / "tools/studio/app/app.js"
    return app.exists() and all(token in app.read_text(encoding="utf-8", errors="ignore") for token in ["unity.agentPlaytestPyramid", "data-file-path", "simAgent.runCodex", "simAgent.liveCheckAll"])


def _one_screen_ready(root: Path) -> bool:
    screenshots = [
        root / "channel-play-external-agent-bridge-buttons-20260607.png",
        root / "channel-play-live-agent-bridge-button-20260607.png",
    ]
    return _studio_screen_ready(root) and any(path.exists() for path in screenshots)


def _required_receipts_exist(runs: list[Path | None]) -> bool:
    return all(bool(run_dir) and (run_dir / "receipt.md").exists() for run_dir in runs)


def _read_json(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except json.JSONDecodeError:
        return default


def _unique_run_dir(root: Path, prefix: str) -> Path:
    base = root / "runs" / f"{prefix}-{slugify(now_iso())}"
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = root / "runs" / f"{base.name}-{suffix}"
        suffix += 1
    return candidate


def _receipt(root: Path, report: dict[str, Any], report_path: Path) -> str:
    failed = [check for check in report["checks"] if not check["passed"]]
    lines = [
        "# Simulation Final Acceptance",
        "",
        f"Checked: {report['checkedAt']}",
        f"Status: `{report['status']}`",
        f"Passed checks: `{len(report['checks']) - len(failed)}/{len(report['checks'])}`",
        f"Report: `{rel(root, report_path)}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        marker = "pass" if check["passed"] else "fail"
        evidence = check["evidence"]
        if evidence.startswith(str(root)):
            evidence = rel(root, Path(evidence))
        lines.append(f"- `{marker}` {check['label']} -> `{evidence or 'none'}`")
    if failed:
        lines.extend(["", "## Failed", ""])
        lines.extend(f"- {check['label']}" for check in failed)
    lines.append("")
    return "\n".join(lines)
