#!/usr/bin/env python3
"""Fail-closed aggregate validation for the Khufu V7 entry-wayfinding slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace


RUN_ROOT = Path("runs/khufu-v7-entry-wayfinding")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
FABLE_REVIEW = Path("work/fable-harness/khufu-v7-entry-wayfinding-final-review.fable.md")
DOC_ROOT = Path("docs/khufu-v7-entry-wayfinding")
DOC_TOKENS = {
    "README.md": "fictional game wayfinding",
    "GOAL.md": "## False-Done Conditions",
    "PLAN.md": "## Stop Conditions",
    "RULES.md": "## Scope Boundary",
    "TEST_PLAN.md": "V7-T-010",
    "STATUS.md": "Current decision:",
}
FABLE_ERROR_TOKENS = ("FABLE_HARNESS_ERROR", "<system-warning>", "tool-call warning")

SOURCE_HASH_LABELS = {
    "V7 builder": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingBuilder.cs"),
    "V7 validator": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs"),
    "V7 entry probe": Path("Assets/_Project/Scripts/Gameplay/KhufuV7EntryProofProbe.cs"),
    "Follow camera": Path("Assets/_Project/Scripts/Player/ChannelFollowCamera.cs"),
    "V7 camera profile": Path("Assets/_Project/Scripts/Player/KhufuV7EntryCameraProfile.cs"),
    "Cutaway": Path("Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs"),
    "Windows build script": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7WindowsBuild.cs"),
}

STAGED_EXACT = {
    SCENE.as_posix(),
    "Assets/_Project/Scripts/Player/ChannelFollowCamera.cs",
    "Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs.meta",
    "tools/validate_khufu_v7_entry_wayfinding.py",
    "tools/tests/test_validate_khufu_v7_entry_wayfinding.py",
}
STAGED_PREFIXES = (
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7",
    "Assets/_Project/Scripts/Gameplay/KhufuV7",
    "Assets/_Project/Scripts/Player/KhufuV7",
    DOC_ROOT.as_posix() + "/",
    RUN_ROOT.as_posix() + "/",
    "work/fable-harness/khufu-v7-",
)
STAGED_FORBIDDEN = (
    "Packages/",
    "ProjectSettings/",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6",
)
STAGED_REQUIRED = {
    SCENE.as_posix(),
    "Assets/_Project/Scripts/Player/ChannelFollowCamera.cs",
    "Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs",
    "Assets/_Project/Scripts/Player/KhufuV7EntryCameraProfile.cs",
    "Assets/_Project/Scripts/Player/KhufuV7EntryCameraProfile.cs.meta",
    "Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs.meta",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingBuilder.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7PlayModeRegressionRunner.cs",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7WindowsBuild.cs",
    "Assets/_Project/Scripts/Gameplay/KhufuV7EntryProofProbe.cs",
    "tools/validate_khufu_v7_entry_wayfinding.py",
    "tools/tests/test_validate_khufu_v7_entry_wayfinding.py",
    (RUN_ROOT / "frozen-inputs-baseline.md").as_posix(),
    (RUN_ROOT / "validation.md").as_posix(),
    (RUN_ROOT / "idempotence.md").as_posix(),
    (RUN_ROOT / "off-route-mutation.md").as_posix(),
    (RUN_ROOT / "v5-playmode-regression.md").as_posix(),
    (RUN_ROOT / "windows-build.md").as_posix(),
    (RUN_ROOT / "final-validation.md").as_posix(),
    (RUN_ROOT / "entry-proof/binding.json").as_posix(),
    (RUN_ROOT / "entry-proof/v7-final-entry-proof.md").as_posix(),
    (RUN_ROOT / "entry-proof/v7-final-participant-entry.png").as_posix(),
    (RUN_ROOT / "entry-proof/v7-pylon-mutation-blocked-pylon-mutation.md").as_posix(),
    (RUN_ROOT / "entry-proof/v7-pylon-mutation-participant-entry.png").as_posix(),
    (RUN_ROOT / "performance-final/binding.json").as_posix(),
    (RUN_ROOT / "performance-final/validation.md").as_posix(),
    (RUN_ROOT / "performance-final/v7-final-performance.md").as_posix(),
    (RUN_ROOT / "performance-final/v7-final.raw").as_posix(),
    (RUN_ROOT / "performance-final/v7-final-windows-player-initial.png").as_posix(),
    (RUN_ROOT / "performance-final/v7-final-windows-player-operator.png").as_posix(),
    FABLE_REVIEW.as_posix(),
}
STAGED_REQUIRED.update((DOC_ROOT / name).as_posix() for name in DOC_TOKENS)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    observed: dict[str, object] = field(default_factory=dict)
    artifacts: set[Path] = field(default_factory=set)

    @property
    def passed(self) -> bool:
        return not self.errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def _read(root: Path, relative: Path, result: ValidationResult) -> str:
    path = root / relative
    result.artifacts.add(path)
    if not path.is_file():
        result.errors.append(f"missing required file: {relative.as_posix()}")
        return ""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.strip():
        result.errors.append(f"empty required file: {relative.as_posix()}")
    return text


def _marker(text: str, marker: str, label: str, errors: list[str]) -> None:
    if marker not in text:
        errors.append(f"{label} missing marker: {marker}")


def _extract(pattern: str, text: str, label: str, errors: list[str]) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        errors.append(f"missing {label}")
        return ""
    return match.group(1)


def _bound_scene_hash(text: str, expected: str, label: str, errors: list[str]) -> None:
    actual = _extract(r"Scene(?: source)? SHA256: `([0-9a-f]{64})`", text, f"{label} scene hash", errors)
    if actual and actual != expected:
        errors.append(f"{label} is bound to stale scene {actual}, expected {expected}")


def _safe_relative(root: Path, raw: str, label: str, errors: list[str]) -> Path | None:
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} escapes project root: {raw}")
        return None
    return candidate


def _check_frozen_inputs(root: Path, result: ValidationResult) -> None:
    text = _read(root, RUN_ROOT / "frozen-inputs-baseline.md", result)
    section = text.partition("## Forbidden Inputs")[2].partition("## Intentional Shared-Code Inputs")[0]
    rows = re.findall(r"^\| `([0-9a-f]{64})` \| `([^`]+)` \|$", section, re.MULTILINE)
    if len(rows) != 14:
        result.errors.append(f"forbidden input table has {len(rows)} entries, expected 14")
    seen: set[str] = set()
    for expected, raw in rows:
        if raw in seen:
            result.errors.append(f"duplicate frozen input: {raw}")
            continue
        seen.add(raw)
        path = _safe_relative(root, raw, "frozen input", result.errors)
        if path is None or not path.is_file():
            result.errors.append(f"missing frozen input: {raw}")
            continue
        result.artifacts.add(path)
        actual = sha256(path)
        if actual != expected:
            result.errors.append(f"frozen input hash mismatch: {raw} expected={expected} actual={actual}")
    result.observed["frozen_input_count"] = len(rows)


def _require_source_tokens(root: Path, relative: Path, tokens: tuple[str, ...], result: ValidationResult) -> str:
    text = _read(root, relative, result)
    for token in tokens:
        if token not in text:
            result.errors.append(f"{relative.as_posix()} missing contract token: {token}")
    return text


def _check_shared_contract(root: Path, result: ValidationResult) -> None:
    _require_source_tokens(
        root,
        Path("Assets/_Project/Scripts/Player/ChannelFollowCamera.cs"),
        (
            "[DefaultExecutionOrder(100)]",
            "new Vector3(0f, 6f, -8f)",
            "CurrentLookAheadOffset",
            "SetLookAheadOffset",
            "lookHeight + lookAheadOffset",
        ),
        result,
    )
    cutaway = _require_source_tokens(
        root,
        Path("Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs"),
        (
            "[DefaultExecutionOrder(200)]",
            'string.Equals(objectName, "V5_Valley_Gate_Pylon_-1"',
            'string.Equals(objectName, "V5_Valley_Gate_Pylon_1"',
            "DiagnosticVisibleOccluderCount",
            "originalEnabled",
            "renderer.enabled = false",
        ),
        result,
    )
    if 'contains("valley")' in cutaway.lower() or 'startswith("V5_Valley_Gate_Pylon_")' in cutaway:
        result.errors.append("cutaway exact-pylon scope was broadened")
    _require_source_tokens(
        root,
        Path("Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs"),
        ("V5_Covered_Causeway_Pylon_1", "rearRenderer.enabled", "frontRenderer.enabled", "valley_pylons=2"),
        result,
    )
    _require_source_tokens(
        root,
        Path("Assets/_Project/Scripts/Player/KhufuV7EntryCameraProfile.cs"),
        ("[DefaultExecutionOrder(50)]", "new Vector3(3f, 7f, -12f)", "new Vector3(-7f, 0f, 0f)"),
        result,
    )
    _require_source_tokens(
        root,
        Path("Assets/_Project/Scripts/Gameplay/KhufuV7EntryProofProbe.cs"),
        ("[DefaultExecutionOrder(300)]", "guideViewportCount >= 2", "routeCenterClear", "failed-as-expected"),
        result,
    )


def _check_static_receipts(root: Path, scene_hash: str, result: ValidationResult) -> None:
    validation = _read(root, RUN_ROOT / "validation.md", result)
    _marker(validation, "V7_VALIDATION: passed", "V7 validation", result.errors)
    _bound_scene_hash(validation, scene_hash, "V7 validation", result.errors)
    for token in (
        "renderers=803_vertices=23968_triangles=16604_colliders=441",
        "renderers=8_vertices=192_triangles=96_colliders=0",
        "9730013ededc08da590b99de5d2bd1ae91c485b25d67e6c591117d4431c2d321",
    ):
        _marker(validation, token, "V7 validation", result.errors)

    idempotence = _read(root, RUN_ROOT / "idempotence.md", result)
    _marker(idempotence, "V7_IDEMPOTENCE: passed", "V7 idempotence", result.errors)
    signatures = re.findall(r"(?:First|Second) signature: `([0-9a-f]{64})`", idempotence)
    if len(signatures) != 2 or len(set(signatures)) != 1:
        result.errors.append("V7 idempotence signatures do not match")
    metrics = re.findall(r"(?:First|Second) metrics: `([^`]+)`", idempotence)
    if len(metrics) != 2 or len(set(metrics)) != 1 or (metrics and metrics[0] != "renderers=8_vertices=192_triangles=96_colliders=0"):
        result.errors.append("V7 idempotence metrics do not match the approved budget")

    mutation = _read(root, RUN_ROOT / "off-route-mutation.md", result)
    _check_off_route_text(mutation, result.errors)

    gate = _read(root, Path("runs/khufu-mega-labyrinth-v5/gate4-acceptance.md"), result)
    for token in ("Verdict: **passed**", "Objective permutations: 6/6", "Controller-clearance samples: 415", "Hub proxy positions: 8/8"):
        _marker(gate, token, "V5 Gate 4", result.errors)

    playmode = _read(root, RUN_ROOT / "v5-playmode-regression.md", result)
    _marker(playmode, "V7_V5_PLAYMODE_REGRESSION: passed", "V5 PlayMode regression", result.errors)
    _bound_scene_hash(playmode, scene_hash, "V5 PlayMode regression", result.errors)
    probe = root / "runs/khufu-mega-labyrinth-v5/playmode-probe.md"
    expected_probe = _extract(r"V5 probe SHA256: `([0-9a-f]{64})`", playmode, "V5 probe hash", result.errors)
    if not probe.is_file():
        result.errors.append("missing V5 PlayMode probe")
    else:
        result.artifacts.add(probe)
        if expected_probe and expected_probe != sha256(probe):
            result.errors.append("V5 PlayMode probe hash mismatch")


def _check_off_route_text(text: str, errors: list[str]) -> None:
    _marker(text, "V7_OFF_ROUTE_MUTATION: passed", "off-route mutation", errors)
    _marker(text, "V7_Entry_Guide_01 + 3m on world Z", "off-route mutation", errors)
    _marker(text, "Guide placement mismatch: V7_Entry_Guide_01", "off-route mutation", errors)


def _check_entry_receipt_text(normal: str, mutation: str, errors: list[str]) -> None:
    for token in (
        "Harness verdict: **passed**",
        "Entry proof: `passed`",
        "Mutation enabled: `False`",
        "Visible candidate occluders: `0`",
        "Look-ahead offset: `-7.000,0.000,0.000`",
        "Player in frame: `True`",
        "Route center clear: `True`",
        "V7_ENTRY_PROOF: passed",
    ):
        _marker(normal, token, "normal entry proof", errors)
    pylons = _extract(r"Active Valley Gate pylons: `(\d+)`", normal, "normal active pylon count", errors)
    guides = _extract(r"Guides in viewport: `(\d+)`", normal, "normal guide viewport count", errors)
    if pylons and int(pylons) < 1:
        errors.append("normal entry proof has no active exact pylon cutaway")
    if guides and int(guides) < 2:
        errors.append("normal entry proof has fewer than two guides in the viewport")
    center = _extract(r"Center environment hit: `([^`]+)`", normal, "normal center environment hit", errors)
    if center and "Floor" not in center and not center.startswith("V7_Entry_Guide_"):
        errors.append(f"normal entry proof center is not a route surface: {center}")

    for token in (
        "Harness verdict: **passed**",
        "Entry proof: `failed-as-expected`",
        "Mutation enabled: `True`",
        "Active Valley Gate pylons: `0`",
        "Route center clear: `False`",
        "_MUTATED_BLOCKING_CONTROL",
        "V7_BLOCKED_PYLON_MUTATION: passed",
    ):
        _marker(mutation, token, "blocked-pylon mutation", errors)


def _check_png(root: Path, receipt: str, label: str, result: ValidationResult) -> None:
    raw = _extract(r"Screenshot: `([^`]+)`", receipt, f"{label} screenshot path", result.errors)
    if not raw:
        return
    normalized = raw.replace("D:/AI2_WIN/channel_play/", "")
    path = _safe_relative(root, normalized, f"{label} screenshot", result.errors)
    if path is None or not path.is_file():
        result.errors.append(f"missing {label} screenshot: {raw}")
        return
    result.artifacts.add(path)
    try:
        if png_dimensions(path) != (1536, 1024):
            result.errors.append(f"{label} screenshot is not 1536x1024")
    except ValueError as error:
        result.errors.append(f"{label} screenshot: {error}")
    if path.stat().st_size < 65536:
        result.errors.append(f"{label} screenshot is too small")


def _check_entry_proof(root: Path, result: ValidationResult) -> None:
    normal = _read(root, RUN_ROOT / "entry-proof/v7-final-entry-proof.md", result)
    mutation = _read(root, RUN_ROOT / "entry-proof/v7-pylon-mutation-blocked-pylon-mutation.md", result)
    _check_entry_receipt_text(normal, mutation, result.errors)
    _check_png(root, normal, "normal entry proof", result)
    _check_png(root, mutation, "blocked-pylon mutation", result)
    for relative, marker in (
        (RUN_ROOT / "entry-proof/player.log", "CHANNEL_PLAY_KHUFU_V7_ENTRY_PROOF result=passed mutation=False"),
        (RUN_ROOT / "entry-proof/mutation-player.log", "CHANNEL_PLAY_KHUFU_V7_ENTRY_PROOF result=passed mutation=True"),
    ):
        log = _read(root, relative, result)
        _marker(log, marker, relative.name, result.errors)


def _check_binding(root: Path, relative: Path, expected_schema: str, scene_hash: str, result: ValidationResult) -> None:
    text = _read(root, relative, result)
    if not text:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        result.errors.append(f"invalid binding JSON {relative.as_posix()}: {error}")
        return
    if data.get("schema") != expected_schema or data.get("verdict") != "passed":
        result.errors.append(f"binding contract mismatch: {relative.as_posix()}")
    records = [data.get("scene"), data.get("player"), data.get("built_level")]
    records.extend(data.get("sources", []))
    records.extend(data.get("artifacts", []))
    for record in records:
        if not isinstance(record, dict):
            result.errors.append(f"binding has malformed record: {relative.as_posix()}")
            continue
        raw = str(record.get("path", ""))
        path = _safe_relative(root, raw, "binding artifact", result.errors)
        if path is None or not path.is_file():
            result.errors.append(f"binding artifact missing: {raw}")
            continue
        result.artifacts.add(path)
        if record.get("bytes") != path.stat().st_size:
            result.errors.append(f"binding byte count mismatch: {raw}")
        if record.get("sha256") != sha256(path):
            result.errors.append(f"binding hash mismatch: {raw}")
    scene_record = data.get("scene", {})
    if scene_record.get("path") != SCENE.as_posix() or scene_record.get("sha256") != scene_hash:
        result.errors.append(f"binding is not tied to current scene: {relative.as_posix()}")


def _check_windows_build(root: Path, scene_hash: str, result: ValidationResult) -> None:
    text = _read(root, RUN_ROOT / "windows-build.md", result)
    for token in ("V7_WINDOWS_BUILD: passed", "Errors: `0`", "Frame Timing Stats in player: `enabled`"):
        _marker(text, token, "Windows build", result.errors)
    _bound_scene_hash(text, scene_hash, "Windows build", result.errors)
    before = _extract(r"Player settings before SHA256: `([0-9a-f]{64})`", text, "settings-before hash", result.errors)
    build_time = _extract(r"Player settings build-time SHA256: `([0-9a-f]{64})`", text, "settings build-time hash", result.errors)
    restored = _extract(r"Player settings restored SHA256: `([0-9a-f]{64})`", text, "settings-restored hash", result.errors)
    if before and restored != before:
        result.errors.append("PlayerSettings.asset was not restored after build")
    if before and build_time == before:
        result.errors.append("Windows build did not bind its frame-timing settings delta")
    for label, relative in SOURCE_HASH_LABELS.items():
        expected = _extract(rf"{re.escape(label)} SHA256: `([0-9a-f]{{64}})`", text, f"{label} hash", result.errors)
        path = root / relative
        result.artifacts.add(path)
        if not path.is_file():
            result.errors.append(f"missing build-bound source: {relative.as_posix()}")
        elif expected and expected != sha256(path):
            result.errors.append(f"Windows build source hash mismatch: {relative.as_posix()}")
    outputs = {
        "Player executable": Path("Builds/KhufuV7/ChannelPlayKhufuV7.exe"),
        "UnityPlayer": Path("Builds/KhufuV7/UnityPlayer.dll"),
        "Built level": Path("Builds/KhufuV7/ChannelPlayKhufuV7_Data/level0"),
    }
    for label, relative in outputs.items():
        expected = _extract(rf"{label} SHA256: `([0-9a-f]{{64}})`", text, f"{label} hash", result.errors)
        path = root / relative
        result.artifacts.add(path)
        if not path.is_file():
            result.errors.append(f"missing Windows build output: {relative.as_posix()}")
        elif expected and expected != sha256(path):
            result.errors.append(f"Windows build output hash mismatch: {relative.as_posix()}")


def _check_performance(root: Path, result: ValidationResult) -> None:
    perf = RUN_ROOT / "performance-final"
    validation = _read(root, perf / "validation.md", result)
    _marker(validation, "PERFORMANCE_VERDICT: passed", "performance validation", result.errors)
    budget = Path("runs/khufu-mega-labyrinth-v5/performance-budget.json")
    receipt = perf / "v7-final-performance.md"
    raw = perf / "v7-final.raw"
    log = perf / "player.log"
    screenshots = [perf / "v7-final-windows-player-initial.png", perf / "v7-final-windows-player-operator.png"]
    for relative in (budget, receipt, raw, log, *screenshots):
        result.artifacts.add(root / relative)
    if str(root / "tools") not in sys.path:
        sys.path.insert(0, str(root / "tools"))
    try:
        from validate_khufu_v5_performance import validate as validate_performance

        passed, failures, observed = validate_performance(
            SimpleNamespace(
                budget=root / budget,
                receipt=root / receipt,
                profiler_raw=root / raw,
                player_log=root / log,
                screenshots=[root / item for item in screenshots],
            )
        )
        result.observed["performance"] = observed
        if not passed:
            result.errors.extend(f"performance: {failure}" for failure in failures)
    except (ImportError, OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        result.errors.append(f"could not directly revalidate performance: {error}")


def _check_docs(root: Path, result: ValidationResult) -> None:
    for name, token in DOC_TOKENS.items():
        text = _read(root, DOC_ROOT / name, result)
        _marker(text, token, f"documentation {name}", result.errors)


def _check_fable_text(text: str, errors: list[str]) -> None:
    for token in FABLE_ERROR_TOKENS:
        if token in text:
            errors.append(f"Fable final review contains harness error token: {token}")
    ships = re.findall(r"^FINAL_REVIEW:\s*ship\s*$", text, re.MULTILINE | re.IGNORECASE)
    if len(ships) != 1:
        errors.append(f"Fable final review has {len(ships)} ship decisions, expected exactly one")
    if re.search(r"^FINAL_REVIEW:\s*(revise|block)\s*$", text, re.MULTILINE | re.IGNORECASE):
        errors.append("Fable final review is not a ship decision")


def _check_fable(root: Path, result: ValidationResult) -> None:
    text = _read(root, FABLE_REVIEW, result)
    _check_fable_text(text, result.errors)


def _check_staged(root: Path, result: ValidationResult) -> None:
    process = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        result.errors.append(f"could not inspect staged files: {process.stderr.strip()}")
        return
    staged = [line.replace("\\", "/") for line in process.stdout.splitlines() if line.strip()]
    if not staged:
        result.errors.append("staged validation requested but index is empty")
    staged_set = set(staged)
    for path in sorted(STAGED_REQUIRED - staged_set):
        result.errors.append(f"required V7 path is not staged: {path}")
    for path in staged:
        if any(path.startswith(prefix) for prefix in STAGED_FORBIDDEN):
            result.errors.append(f"forbidden staged path: {path}")
        if path not in STAGED_EXACT and not any(path.startswith(prefix) for prefix in STAGED_PREFIXES):
            result.errors.append(f"out-of-scope staged path: {path}")

    unstaged_process = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if unstaged_process.returncode != 0:
        result.errors.append(f"could not inspect unstaged files: {unstaged_process.stderr.strip()}")
    else:
        unstaged = {line.replace("\\", "/") for line in unstaged_process.stdout.splitlines() if line.strip()}
        for path in sorted(staged_set & unstaged):
            result.errors.append(f"staged path has an additional unstaged delta: {path}")

    baseline = _read(root, RUN_ROOT / "frozen-inputs-baseline.md", result)
    divergence_section = baseline.partition("## Pre-existing Index Divergences")[2]
    divergences = re.findall(
        r"^\| `([0-9a-f]{64})` \| `([0-9a-f]{64})` \| `([^`]+)` \|$",
        divergence_section,
        re.MULTILINE,
    )
    if len(divergences) != 2:
        result.errors.append(f"pre-existing index divergence table has {len(divergences)} entries, expected 2")
    for expected_index, expected_worktree, path in divergences:
        index_process = subprocess.run(
            ["git", "show", f":{path}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if index_process.returncode != 0:
            result.errors.append(f"could not read staged-index input {path}")
        elif sha256_bytes(index_process.stdout) != expected_index:
            result.errors.append(f"staged-index hash mismatch for inherited input: {path}")
        worktree_path = root / path
        if not worktree_path.is_file() or sha256(worktree_path) != expected_worktree:
            result.errors.append(f"worktree hash mismatch for inherited input: {path}")
    result.observed["staged_file_count"] = len(staged)


def _artifact_digest(root: Path, artifacts: set[Path]) -> str:
    lines: list[str] = []
    for path in sorted(artifacts):
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        lines.append(f"{relative}\0{sha256(path)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def validate(root: Path, *, require_fable: bool = True, staged: bool = False) -> ValidationResult:
    root = root.resolve()
    result = ValidationResult()
    scene = root / SCENE
    if not scene.is_file():
        result.errors.append(f"missing scene: {SCENE.as_posix()}")
        scene_hash = ""
    else:
        result.artifacts.add(scene)
        scene_hash = sha256(scene)
        result.observed["scene_sha256"] = scene_hash
    _check_frozen_inputs(root, result)
    _check_shared_contract(root, result)
    _check_static_receipts(root, scene_hash, result)
    _check_entry_proof(root, result)
    _check_windows_build(root, scene_hash, result)
    _check_performance(root, result)
    _check_binding(root, RUN_ROOT / "entry-proof/binding.json", "khufu-v7-entry-proof-binding-v1", scene_hash, result)
    _check_binding(root, RUN_ROOT / "performance-final/binding.json", "khufu-v7-performance-binding-v1", scene_hash, result)
    _check_docs(root, result)
    if require_fable:
        _check_fable(root, result)
    if staged:
        _check_staged(root, result)
    result.observed["artifact_digest"] = _artifact_digest(root, result.artifacts)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-fable", action="store_true")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    result = validate(args.root, require_fable=not args.skip_fable, staged=args.staged)
    lines = [
        "# Khufu V7 Aggregate Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Scene SHA256: `{result.observed.get('scene_sha256', '')}`",
        f"- Frozen inputs: `{result.observed.get('frozen_input_count', 0)}`",
        f"- Artifact digest: `{result.observed.get('artifact_digest', '')}`",
        f"- Fable required: `{not args.skip_fable}`",
        f"- Staged scope checked: `{args.staged}`",
    ]
    lines.extend(f"- Failure: {error}" for error in result.errors)
    lines.extend(["", f"V7_AGGREGATE_VERDICT: {'passed' if result.passed else 'failed'}", ""])
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(lines[-2])
    for error in result.errors:
        print(f"FAIL: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
