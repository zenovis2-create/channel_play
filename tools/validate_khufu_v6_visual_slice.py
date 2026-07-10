#!/usr/bin/env python3
"""Fail-closed validation for the Khufu V6 visual-fidelity slice."""

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


RUN_ROOT = Path("runs/khufu-v6-visual-slice")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
FABLE_REVIEW = Path("work/fable-harness/khufu-v6-visual-slice-final-review.fable.md")
WINDOWS_BUILD_SOURCE = Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6WindowsBuild.cs")
DOC_ROOT = Path("docs/khufu-v6-visual-slice")
DOC_TOKENS = {
    "README.md": "fictionalized production-readability slice",
    "GOAL.md": "## False-Done Conditions",
    "PLAN.md": "**Final gate**",
    "RULES.md": "Final completion requires",
    "TEST_PLAN.md": "V6-T-011",
    "STATUS.md": "Current decision:",
}
V6_SOURCES = {
    "Builder": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs"),
    "Validator": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs"),
    "Exporter": Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceScreenshotExporter.cs"),
}
CAPTURES = (
    "hero_valley_to_pyramid",
    "player_temple_hub",
    "dense_core",
    "temple_hub_detail",
)
MATERIALS = (
    "V6_Tura_Casing",
    "V6_Core_Limestone",
    "V6_Interior_Limestone",
    "V6_Basalt_Court",
    "V6_Red_Granite",
    "V6_Causeway_Limestone",
    "V6_Scan_Inlay",
)
SURFACES = ("TuraCasing", "CoreLimestone", "Basalt", "RedGranite")
MATERIAL_SURFACE = {
    "V6_Tura_Casing": "TuraCasing",
    "V6_Core_Limestone": "CoreLimestone",
    "V6_Interior_Limestone": "CoreLimestone",
    "V6_Basalt_Court": "Basalt",
    "V6_Red_Granite": "RedGranite",
    "V6_Causeway_Limestone": "CoreLimestone",
    "V6_Scan_Inlay": "Basalt",
}
FABLE_ERROR_TOKENS = ("FABLE_HARNESS_ERROR", "<system-warning>", "tool-call warning")

STAGED_EXACT = {
    SCENE.as_posix(),
    "tools/validate_khufu_v6_visual_slice.py",
    "tools/tests/test_validate_khufu_v6_visual_slice.py",
    "work/fable-harness/khufu-v6-visual-slice-plan-critique.retry.md",
    "work/fable-harness/khufu-v6-visual-slice-plan-critique.retry.fable.md",
    "work/fable-harness/khufu-v6-visual-slice-plan-critique.retry.fable.md.meta.json",
    "work/fable-harness/khufu-v6-visual-slice-final-review.md",
    FABLE_REVIEW.as_posix(),
    "work/fable-harness/khufu-v6-visual-slice-final-review.fable.md.meta.json",
    (RUN_ROOT / "frozen-inputs-baseline.md").as_posix(),
    (RUN_ROOT / "validation.md").as_posix(),
    (RUN_ROOT / "idempotence.md").as_posix(),
    (RUN_ROOT / "v5-playmode-regression.md").as_posix(),
    (RUN_ROOT / "windows-build.md").as_posix(),
    (RUN_ROOT / "pre-fable-validation.md").as_posix(),
    (RUN_ROOT / "final-validation.md").as_posix(),
    (RUN_ROOT / "staged-index-validation.md").as_posix(),
    (RUN_ROOT / "performance-final/binding.json").as_posix(),
    (RUN_ROOT / "performance-final/invalid-oversized-raw-performance.md").as_posix(),
    (RUN_ROOT / "performance-final/player.log").as_posix(),
    (RUN_ROOT / "performance-final/v6-final.raw").as_posix(),
    (RUN_ROOT / "performance-final/v6-final-performance.md").as_posix(),
    (RUN_ROOT / "performance-final/v6-final-windows-player-initial.png").as_posix(),
    (RUN_ROOT / "performance-final/v6-final-windows-player-operator.png").as_posix(),
    (RUN_ROOT / "performance-final/validation.md").as_posix(),
    (RUN_ROOT / "performance-final/validation-first-attempt.md").as_posix(),
}
STAGED_PREFIXES = (
    "Assets/_Project/Art/Generated/KhufuV6VisualSlice",
    "Assets/_Project/Materials/KhufuV6",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6",
    DOC_ROOT.as_posix() + "/",
    (RUN_ROOT / "captures").as_posix() + "/",
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    observed: dict[str, object] = field(default_factory=dict)
    artifact_sha256: str = ""

    @property
    def passed(self) -> bool:
        return not self.errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def _read(root: Path, relative: Path, errors: list[str]) -> str:
    path = root / relative
    if not path.is_file():
        errors.append(f"missing required file: {relative.as_posix()}")
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        errors.append(f"empty required file: {relative.as_posix()}")
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


def _safe_path(root: Path, raw: str, label: str, errors: list[str]) -> Path | None:
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} escapes project root: {raw}")
        return None
    return candidate


def _check_frozen_inputs(root: Path, errors: list[str]) -> int:
    relative = RUN_ROOT / "frozen-inputs-baseline.md"
    text = _read(root, relative, errors)
    rows = re.findall(r"^\| `([0-9a-f]{64})` \| `([^`]+)` \|$", text, re.MULTILINE)
    if len(rows) != 9:
        errors.append(f"frozen input table has {len(rows)} entries, expected 9")
    seen: set[str] = set()
    for expected, raw_path in rows:
        if raw_path in seen:
            errors.append(f"duplicate frozen input path: {raw_path}")
            continue
        seen.add(raw_path)
        path = _safe_path(root, raw_path, "frozen input", errors)
        if path is None or not path.is_file():
            errors.append(f"missing frozen input: {raw_path}")
            continue
        actual = sha256(path)
        if actual != expected:
            errors.append(f"frozen input hash mismatch: {raw_path} expected={expected} actual={actual}")
    return len(rows)


def _check_v6_receipts(root: Path, scene_hash: str, errors: list[str], observed: dict[str, object]) -> list[Path]:
    artifacts: list[Path] = []
    validation_rel = RUN_ROOT / "validation.md"
    validation = _read(root, validation_rel, errors)
    artifacts.append(root / validation_rel)
    _marker(validation, "V6_VALIDATION: passed", "V6 validation", errors)
    metrics = re.search(
        r"Added V6 metrics: `renderers=(\d+) vertices=(\d+) triangles=(\d+) colliders=(\d+)`",
        validation,
    )
    if metrics is None:
        errors.append("missing V6 added metrics")
    else:
        renderers, vertices, triangles, colliders = map(int, metrics.groups())
        observed.update(
            v6_renderers=renderers,
            v6_vertices=vertices,
            v6_triangles=triangles,
            v6_colliders=colliders,
        )
        if renderers > 12 or vertices > 800 or triangles > 600 or colliders != 0:
            errors.append("V6 added metrics exceed the approved static budget")
    materials = _extract(r"V6 materials: `(\d+) / 8`", validation, "V6 material count", errors)
    if materials and int(materials) > 8:
        errors.append("V6 material count exceeds 8")
    signature = _extract(r"Visual signature: `([0-9a-f]{64})`", validation, "V6 visual signature", errors)

    idempotence_rel = RUN_ROOT / "idempotence.md"
    idempotence = _read(root, idempotence_rel, errors)
    artifacts.append(root / idempotence_rel)
    _marker(idempotence, "V6_IDEMPOTENCE: passed", "V6 idempotence", errors)
    first_signature = _extract(
        r"First visual signature: `([0-9a-f]{64})`", idempotence, "first idempotence signature", errors
    )
    second_signature = _extract(
        r"Second visual signature: `([0-9a-f]{64})`", idempotence, "second idempotence signature", errors
    )
    if signature and (signature != first_signature or signature != second_signature):
        errors.append("V6 validation and idempotence signatures do not match")
    first_metrics = _extract(r"First added metrics: `([^`]+)`", idempotence, "first idempotence metrics", errors)
    second_metrics = _extract(r"Second added metrics: `([^`]+)`", idempotence, "second idempotence metrics", errors)
    if first_metrics and first_metrics != second_metrics:
        errors.append("V6 idempotence metrics do not match")

    playmode_rel = RUN_ROOT / "v5-playmode-regression.md"
    playmode = _read(root, playmode_rel, errors)
    artifacts.append(root / playmode_rel)
    _marker(playmode, "V6_V5_PLAYMODE_REGRESSION: passed", "V5 PlayMode regression", errors)
    playmode_scene = _extract(r"Scene SHA256: `([0-9a-f]{64})`", playmode, "PlayMode scene hash", errors)
    if playmode_scene and playmode_scene != scene_hash:
        errors.append("V5 PlayMode receipt is not bound to the current scene")
    probe_rel = Path("runs/khufu-mega-labyrinth-v5/playmode-probe.md")
    probe_hash = _extract(r"V5 probe SHA256: `([0-9a-f]{64})`", playmode, "V5 probe hash", errors)
    probe = _read(root, probe_rel, errors)
    artifacts.append(root / probe_rel)
    _marker(probe, "Verdict: **passed**", "V5 PlayMode probe", errors)
    if probe_hash and (root / probe_rel).is_file() and probe_hash != sha256(root / probe_rel):
        errors.append("V5 PlayMode probe hash mismatch")

    gate_rel = Path("runs/khufu-mega-labyrinth-v5/gate4-acceptance.md")
    gate = _read(root, gate_rel, errors)
    artifacts.append(root / gate_rel)
    for token in ("Verdict: **passed**", "Objective permutations: 6/6", "Controller-clearance samples: 415", "Hub proxy positions: 8/8"):
        _marker(gate, token, "V5 Gate 4", errors)
    return artifacts


def _check_captures(root: Path, scene_hash: str, errors: list[str], observed: dict[str, object]) -> list[Path]:
    manifest_rel = RUN_ROOT / "captures/manifest.md"
    manifest = _read(root, manifest_rel, errors)
    artifacts = [root / manifest_rel]
    _marker(manifest, "CAPTURE_INTEGRITY: passed", "capture manifest", errors)
    _marker(manifest, "VISUAL_DELTA: passed", "capture manifest", errors)
    manifest_scene = _extract(r"Scene SHA256: `([0-9a-f]{64})`", manifest, "capture scene hash", errors)
    if manifest_scene and manifest_scene != scene_hash:
        errors.append("capture manifest is not bound to the current scene")
    for label, relative in V6_SOURCES.items():
        expected = _extract(rf"{label} SHA256: `([0-9a-f]{{64}})`", manifest, f"capture {label} hash", errors)
        path = root / relative
        if not path.is_file():
            errors.append(f"missing V6 source: {relative.as_posix()}")
        elif expected and expected != sha256(path):
            errors.append(f"capture {label} hash mismatch")
        artifacts.append(path)

    hashes: set[str] = set()
    for name in CAPTURES:
        section = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |^CAPTURE_INTEGRITY:|\Z)", manifest, re.MULTILINE | re.DOTALL)
        if section is None:
            errors.append(f"missing capture manifest section: {name}")
            continue
        expected_hash = _extract(r"^- SHA256: `([0-9a-f]{64})`", section.group(1), f"{name} hash", errors)
        expected_bytes = _extract(r"^- Bytes: `(\d+)`", section.group(1), f"{name} byte count", errors)
        path = root / RUN_ROOT / "captures" / f"{name}.png"
        artifacts.append(path)
        if not path.is_file():
            errors.append(f"missing capture: {path.relative_to(root).as_posix()}")
            continue
        actual_hash = sha256(path)
        hashes.add(actual_hash)
        if expected_hash and expected_hash != actual_hash:
            errors.append(f"capture hash mismatch: {name}")
        if expected_bytes and int(expected_bytes) != path.stat().st_size:
            errors.append(f"capture byte count mismatch: {name}")
        try:
            if png_dimensions(path) != (1536, 1024):
                errors.append(f"capture has wrong dimensions: {name}")
        except ValueError as error:
            errors.append(f"capture {name}: {error}")
        if path.stat().st_size < 65536:
            errors.append(f"capture is too small: {name}")
    if len(hashes) != len(CAPTURES):
        errors.append("V6 captures are missing or duplicate")
    observed["capture_count"] = len(hashes)
    return artifacts


def _check_generated_assets(root: Path, errors: list[str]) -> list[Path]:
    artifacts: list[Path] = []
    texture_guids: dict[tuple[str, str], str] = {}
    texture_root = root / "Assets/_Project/Art/Generated/KhufuV6VisualSlice/Textures"
    for surface in SURFACES:
        for kind in ("Albedo", "Normal"):
            path = texture_root / f"V6_{surface}_{kind}.png"
            meta = Path(str(path) + ".meta")
            artifacts.extend((path, meta))
            if not path.is_file():
                errors.append(f"missing generated texture: {path.relative_to(root).as_posix()}")
                continue
            try:
                if png_dimensions(path) != (512, 512):
                    errors.append(f"generated texture has wrong dimensions: {path.name}")
            except ValueError as error:
                errors.append(f"generated texture {path.name}: {error}")
            if not meta.is_file():
                errors.append(f"missing generated texture meta: {meta.relative_to(root).as_posix()}")
                continue
            guid = _extract(r"^guid: ([0-9a-f]{32})$", meta.read_text(encoding="utf-8"), f"{meta.name} GUID", errors)
            if guid:
                texture_guids[(surface, kind)] = guid

    for name in MATERIALS:
        path = root / "Assets/_Project/Materials/KhufuV6" / f"{name}.mat"
        meta = Path(str(path) + ".meta")
        artifacts.extend((path, meta))
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing generated material: {name}")
            continue
        if not meta.is_file():
            errors.append(f"missing generated material meta: {meta.relative_to(root).as_posix()}")
        else:
            _extract(r"^guid: ([0-9a-f]{32})$", meta.read_text(encoding="utf-8"), f"{meta.name} GUID", errors)
        material_text = path.read_text(encoding="utf-8", errors="replace")
        surface = MATERIAL_SURFACE[name]
        for kind in ("Albedo", "Normal"):
            guid = texture_guids.get((surface, kind), "")
            if guid and f"guid: {guid}" not in material_text:
                errors.append(f"material {name} does not reference its {kind.lower()} texture GUID")
    return artifacts


def _check_windows_build(root: Path, scene_hash: str, errors: list[str], observed: dict[str, object]) -> list[Path]:
    receipt_rel = RUN_ROOT / "windows-build.md"
    receipt = _read(root, receipt_rel, errors)
    artifacts = [root / receipt_rel]
    _marker(receipt, "V6_WINDOWS_BUILD: passed", "Windows build", errors)
    _marker(receipt, "- Errors: `0`", "Windows build", errors)
    _marker(receipt, "- Frame Timing Stats in player: `enabled`", "Windows build", errors)
    built_scene = _extract(r"Scene source SHA256: `([0-9a-f]{64})`", receipt, "Windows build scene hash", errors)
    if built_scene and built_scene != scene_hash:
        errors.append("Windows build is not bound to the current scene")
    expected_builder = _extract(r"Builder SHA256: `([0-9a-f]{64})`", receipt, "Windows build builder hash", errors)
    builder = root / V6_SOURCES["Builder"]
    if expected_builder and builder.is_file() and expected_builder != sha256(builder):
        errors.append("Windows build builder hash mismatch")
    expected_build_script = _extract(
        r"Windows build script SHA256: `([0-9a-f]{64})`",
        receipt,
        "Windows build script hash",
        errors,
    )
    build_script = root / WINDOWS_BUILD_SOURCE
    if not build_script.is_file():
        errors.append(f"missing Windows build source: {WINDOWS_BUILD_SOURCE.as_posix()}")
    elif expected_build_script and expected_build_script != sha256(build_script):
        errors.append("Windows build script hash mismatch")
    before = _extract(r"Player settings before SHA256: `([0-9a-f]{64})`", receipt, "settings-before hash", errors)
    build_time = _extract(r"Player settings build-time SHA256: `([0-9a-f]{64})`", receipt, "settings build-time hash", errors)
    restored = _extract(r"Player settings restored SHA256: `([0-9a-f]{64})`", receipt, "settings-restored hash", errors)
    if before and before != restored:
        errors.append("PlayerSettings.asset was not restored after the Windows build")
    if before and build_time == before:
        errors.append("Windows build did not bind the frame-timing settings delta")

    outputs = {
        "Player executable": Path("Builds/KhufuV6/ChannelPlayKhufuV6.exe"),
        "UnityPlayer": Path("Builds/KhufuV6/UnityPlayer.dll"),
        "Built level": Path("Builds/KhufuV6/ChannelPlayKhufuV6_Data/level0"),
    }
    for label, relative in outputs.items():
        expected = _extract(rf"{label} SHA256: `([0-9a-f]{{64}})`", receipt, f"{label} hash", errors)
        path = root / relative
        if not path.is_file():
            errors.append(f"missing Windows build output: {relative.as_posix()}")
        elif expected and expected != sha256(path):
            errors.append(f"Windows build output hash mismatch: {relative.as_posix()}")
    observed["windows_build_warnings"] = int(
        _extract(r"Warnings: `(\d+)`", receipt, "Windows build warning count", errors) or 0
    )
    artifacts.append(build_script)
    return artifacts


def _check_performance(root: Path, scene_hash: str, errors: list[str], observed: dict[str, object]) -> list[Path]:
    perf_root = RUN_ROOT / "performance-final"
    validation_rel = perf_root / "validation.md"
    validation = _read(root, validation_rel, errors)
    _marker(validation, "PERFORMANCE_VERDICT: passed", "performance validation", errors)
    receipt_rel = perf_root / "v6-final-performance.md"
    raw_rel = perf_root / "v6-final.raw"
    log_rel = perf_root / "player.log"
    screenshots = (
        perf_root / "v6-final-windows-player-initial.png",
        perf_root / "v6-final-windows-player-operator.png",
    )
    budget_rel = Path("runs/khufu-mega-labyrinth-v5/performance-budget.json")
    paths = [validation_rel, receipt_rel, raw_rel, log_rel, budget_rel, *screenshots]
    if str(root / "tools") not in sys.path:
        sys.path.insert(0, str(root / "tools"))
    try:
        from validate_khufu_v5_performance import validate as validate_performance

        args = SimpleNamespace(
            budget=root / budget_rel,
            receipt=root / receipt_rel,
            profiler_raw=root / raw_rel,
            player_log=root / log_rel,
            screenshots=[root / item for item in screenshots],
        )
        passed, failures, metrics = validate_performance(args)
        if not passed:
            errors.extend(f"performance: {failure}" for failure in failures)
        observed["performance"] = metrics
    except (OSError, ValueError, KeyError, ImportError, json.JSONDecodeError) as error:
        errors.append(f"performance validator could not run: {error}")

    binding_rel = perf_root / "binding.json"
    binding_path = root / binding_rel
    paths.append(binding_rel)
    if not binding_path.is_file():
        errors.append(f"missing performance binding: {binding_rel.as_posix()}")
    else:
        try:
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            if binding.get("schema") != "khufu-v6-performance-binding-v1" or binding.get("verdict") != "passed":
                errors.append("performance binding schema or verdict is invalid")
            contract = binding.get("run_contract", {})
            expected_contract = {
                "rendered_window": True,
                "resolution": "1536x1024",
                "quality": "Ultra",
                "graphics_api": "D3D11",
                "raw_capture_frames": 30,
            }
            for key, expected in expected_contract.items():
                if contract.get(key) != expected:
                    errors.append(f"performance binding contract mismatch: {key}")
            expected_entries = {
                "scene": SCENE,
                "player": Path("Builds/KhufuV6/ChannelPlayKhufuV6.exe"),
                "built_level": Path("Builds/KhufuV6/ChannelPlayKhufuV6_Data/level0"),
            }
            for key, relative in expected_entries.items():
                entry = binding.get(key, {})
                if entry.get("path") != relative.as_posix():
                    errors.append(f"performance binding path mismatch: {key}")
                    continue
                target = root / relative
                if not target.is_file() or entry.get("sha256") != sha256(target):
                    errors.append(f"performance binding hash mismatch: {key}")
            if binding.get("scene", {}).get("sha256") != scene_hash:
                errors.append("performance binding is not bound to the current scene")
            expected_artifacts = {item.as_posix() for item in (validation_rel, receipt_rel, raw_rel, log_rel, *screenshots)}
            bound_artifacts = binding.get("artifacts", [])
            if {entry.get("path") for entry in bound_artifacts} != expected_artifacts:
                errors.append("performance binding artifact set mismatch")
            for entry in bound_artifacts:
                target = root / str(entry.get("path", ""))
                if not target.is_file() or entry.get("sha256") != sha256(target):
                    errors.append(f"performance binding artifact hash mismatch: {entry.get('path')}")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            errors.append(f"performance binding could not be read: {error}")
    return [root / path for path in paths if path not in (raw_rel, log_rel)]


def _binding_entry(root: Path, relative: Path) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(relative.as_posix())
    return {"path": relative.as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size}


def write_performance_binding(root: Path) -> Path:
    root = root.resolve()
    perf_root = RUN_ROOT / "performance-final"
    artifacts = (
        perf_root / "validation.md",
        perf_root / "v6-final-performance.md",
        perf_root / "v6-final.raw",
        perf_root / "player.log",
        perf_root / "v6-final-windows-player-initial.png",
        perf_root / "v6-final-windows-player-operator.png",
    )
    payload = {
        "schema": "khufu-v6-performance-binding-v1",
        "verdict": "passed",
        "run_contract": {
            "rendered_window": True,
            "resolution": "1536x1024",
            "quality": "Ultra",
            "graphics_api": "D3D11",
            "raw_capture_frames": 30,
        },
        "scene": _binding_entry(root, SCENE),
        "player": _binding_entry(root, Path("Builds/KhufuV6/ChannelPlayKhufuV6.exe")),
        "built_level": _binding_entry(root, Path("Builds/KhufuV6/ChannelPlayKhufuV6_Data/level0")),
        "artifacts": [_binding_entry(root, relative) for relative in artifacts],
    }
    output = root / perf_root / "binding.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _git_index_bytes(root: Path, relative: str) -> bytes | None:
    process = subprocess.run(
        ["git", "show", f":{relative}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return process.stdout if process.returncode == 0 else None


def validate_staged_index(root: Path) -> ValidationResult:
    root = root.resolve()
    result = ValidationResult()
    process = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        result.errors.append("could not read staged index: " + process.stderr.decode(errors="replace"))
        return result
    staged = {item.decode("utf-8") for item in process.stdout.split(b"\0") if item}
    result.observed["staged_files"] = len(staged)
    if not staged:
        result.errors.append("staged index is empty")
    unexpected = sorted(
        path for path in staged if path not in STAGED_EXACT and not any(path.startswith(prefix) for prefix in STAGED_PREFIXES)
    )
    result.errors.extend(f"unexpected staged path: {path}" for path in unexpected)

    required = {
        SCENE.as_posix(),
        *(path.as_posix() for path in V6_SOURCES.values()),
        WINDOWS_BUILD_SOURCE.as_posix(),
        "tools/validate_khufu_v6_visual_slice.py",
        "tools/tests/test_validate_khufu_v6_visual_slice.py",
        FABLE_REVIEW.as_posix(),
        (RUN_ROOT / "final-validation.md").as_posix(),
    }
    result.errors.extend(f"required V6 path is not staged: {path}" for path in sorted(required - staged))

    baseline = _read(root, RUN_ROOT / "frozen-inputs-baseline.md", result.errors)
    frozen_rows = re.findall(r"^\| `([0-9a-f]{64})` \| `([^`]+)` \|$", baseline, re.MULTILINE)
    divergence_rows = re.findall(
        r"^\| `([0-9a-f]{64})` \| `([0-9a-f]{64})` \| `([^`]+)` \|$",
        baseline,
        re.MULTILINE,
    )
    divergences = {path: (index_hash, worktree_hash) for index_hash, worktree_hash, path in divergence_rows}
    accepted_divergences = 0
    for expected, relative in frozen_rows:
        if relative in staged:
            result.errors.append(f"frozen input must not be staged: {relative}")
        content = _git_index_bytes(root, relative)
        if content is None:
            result.errors.append(f"frozen input missing from staged index: {relative}")
            continue
        index_hash = hashlib.sha256(content).hexdigest()
        if index_hash == expected:
            continue
        recorded = divergences.get(relative)
        if recorded == (index_hash, expected):
            accepted_divergences += 1
            continue
        result.errors.append(f"staged frozen input hash mismatch: {relative}")
    result.observed["staged_frozen_inputs"] = len(frozen_rows)
    result.observed["preexisting_index_divergences"] = accepted_divergences

    staged_scene = _git_index_bytes(root, SCENE.as_posix())
    if staged_scene is None:
        result.errors.append("current scene is missing from staged index")
    else:
        staged_scene_hash = hashlib.sha256(staged_scene).hexdigest()
        result.observed["staged_scene_sha256"] = staged_scene_hash
        worktree_scene_hash = sha256(root / SCENE)
        if staged_scene_hash != worktree_scene_hash:
            result.errors.append("staged scene differs from the evidence-bound worktree scene")
        final_receipt = _read(root, RUN_ROOT / "final-validation.md", result.errors)
        recorded_scene = _extract(r'"scene_sha256": "([0-9a-f]{64})"', final_receipt, "final receipt scene hash", result.errors)
        if recorded_scene and staged_scene_hash != recorded_scene:
            result.errors.append("staged scene differs from the final validation receipt")

    expected_meta = {
        f"Assets/_Project/Materials/KhufuV6/{name}.mat.meta" for name in MATERIALS
    }
    expected_meta.update(
        f"Assets/_Project/Art/Generated/KhufuV6VisualSlice/Textures/V6_{surface}_{kind}.png.meta"
        for surface in SURFACES
        for kind in ("Albedo", "Normal")
    )
    missing_meta = sorted(expected_meta - staged)
    result.errors.extend(f"generated asset meta is not staged: {path}" for path in missing_meta)
    result.observed["staged_generated_meta"] = len(expected_meta - set(missing_meta))
    return result


def write_staged_validation(root: Path, output: Path) -> ValidationResult:
    result = validate_staged_index(root)
    lines = [
        "# Khufu V6 Staged Index Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Observed: `{json.dumps(result.observed, sort_keys=True)}`",
    ]
    lines.extend(f"- Failure: {error}" for error in result.errors)
    lines.extend(["", f"STAGED_INDEX_VALIDATION: {'passed' if result.passed else 'failed'}", ""])
    path = output if output.is_absolute() else root / output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return result


def _check_fable(root: Path, errors: list[str]) -> list[Path]:
    text = _read(root, FABLE_REVIEW, errors)
    for token in FABLE_ERROR_TOKENS:
        if token.lower() in text.lower():
            errors.append(f"Fable final review contains error token: {token}")
    verdicts = re.findall(r"^FABLE_VERDICT:\s*(ship|revise|investigate)\s*$", text, re.MULTILINE | re.IGNORECASE)
    if len(verdicts) != 1:
        errors.append(f"Fable final review must contain exactly one verdict line, found {len(verdicts)}")
    elif verdicts[0].lower() != "ship":
        errors.append(f"Fable final verdict is {verdicts[0].lower()}, not ship")
    return [root / FABLE_REVIEW]


def _check_docs(root: Path, errors: list[str]) -> list[Path]:
    artifacts: list[Path] = []
    for name, token in DOC_TOKENS.items():
        relative = DOC_ROOT / name
        text = _read(root, relative, errors)
        if text and token not in text:
            errors.append(f"V6 document {name} missing required token: {token}")
        artifacts.append(root / relative)
    return artifacts


def _fingerprint(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted({item.resolve() for item in paths if item.is_file()}):
        label = path.relative_to(root.resolve()).as_posix()
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\0")
    return digest.hexdigest()


def validate(root: Path) -> ValidationResult:
    root = root.resolve()
    result = ValidationResult()
    scene_path = root / SCENE
    if not scene_path.is_file():
        result.errors.append(f"missing current scene: {SCENE.as_posix()}")
        scene_hash = ""
    else:
        scene_hash = sha256(scene_path)
        result.observed["scene_sha256"] = scene_hash

    result.observed["frozen_inputs"] = _check_frozen_inputs(root, result.errors)
    artifacts: list[Path] = [scene_path, root / RUN_ROOT / "frozen-inputs-baseline.md"]
    artifacts.extend(_check_v6_receipts(root, scene_hash, result.errors, result.observed))
    artifacts.extend(_check_captures(root, scene_hash, result.errors, result.observed))
    artifacts.extend(_check_generated_assets(root, result.errors))
    artifacts.extend(_check_windows_build(root, scene_hash, result.errors, result.observed))
    artifacts.extend(_check_performance(root, scene_hash, result.errors, result.observed))
    artifacts.extend(_check_docs(root, result.errors))
    artifacts.extend(_check_fable(root, result.errors))
    artifacts.append(root / "tools/validate_khufu_v6_visual_slice.py")
    result.artifact_sha256 = _fingerprint(root, artifacts)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=RUN_ROOT / "final-validation.md")
    parser.add_argument("--write-performance-binding", action="store_true")
    parser.add_argument("--validate-staged", action="store_true")
    args = parser.parse_args()
    if args.write_performance_binding:
        output = write_performance_binding(args.root)
        print(f"V6_PERFORMANCE_BINDING: wrote {output}")
        return 0
    if args.validate_staged:
        result = write_staged_validation(args.root.resolve(), RUN_ROOT / "staged-index-validation.md")
        print(f"STAGED_INDEX_VALIDATION: {'passed' if result.passed else 'failed'}")
        for error in result.errors:
            print(f"FAIL: {error}")
        return 0 if result.passed else 1
    result = validate(args.root)
    lines = [
        "# Khufu V6 Final Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Artifact SHA256: `{result.artifact_sha256}`",
        f"- Observed: `{json.dumps(result.observed, sort_keys=True)}`",
    ]
    lines.extend(f"- Failure: {error}" for error in result.errors)
    lines.extend(["", f"V6_FINAL_VALIDATION: {'passed' if result.passed else 'failed'}", ""])
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(lines[-2])
    for error in result.errors:
        print(f"FAIL: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
