from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path("runs/khufu-v10-interior-spine")
DOC_ROOT = Path("docs/khufu-v10-interior-spine")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
BUILD_ROOT = Path("Builds/KhufuV10")
PLAYER = BUILD_ROOT / "ChannelPlayKhufuV10.exe"
BUILT_LEVEL = BUILD_ROOT / "ChannelPlayKhufuV10_Data/level0"
ASSEMBLY = BUILD_ROOT / "ChannelPlayKhufuV10_Data/Managed/Assembly-CSharp.dll"
ALLOWLIST = DOC_ROOT / "staging-allowlist.txt"
EDITOR_BINDING = RUN_ROOT / "editor-binding.json"
PLAYER_BINDING = RUN_ROOT / "player-proof/binding.json"
PERFORMANCE_BINDING = RUN_ROOT / "performance-final/binding.json"
EXTERNAL_FABLE = Path("work/fable-harness/khufu-v10-interior-spine-final-review.fable.md")
STAGED_INVENTORY = RUN_ROOT / "staged-inventory.json"
STAGED_REPORT = RUN_ROOT / "staged-index-validation.md"
POSTCOMMIT_REPORT = RUN_ROOT / "post-commit-validation.md"
EDITOR_SCHEMA = "khufu-v10-editor-binding-v2"
PLAYER_SCHEMA = "khufu-v10-player-binding-v2"
PERFORMANCE_SCHEMA = "khufu-v10-performance-binding-v2"


SOURCE_FILES = [
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorAudit.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorBuilder.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorMeshPipeline.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorScreenshotExporter.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10WindowsBuild.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuControllerHitRecorder.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10RouteContract.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10SegmentTag.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10TraversalProofProbe.cs"),
    Path("tools/validate_khufu_v10_prewrite.py"),
    Path("tools/validate_khufu_v10_release.py"),
    Path("tools/tests/test_validate_khufu_v10_prewrite.py"),
    Path("tools/tests/test_validate_khufu_v10_release.py"),
]

SOURCE_META_FILES = [
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorBuilder.cs.meta"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorMeshPipeline.cs.meta"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorScreenshotExporter.cs.meta"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs.meta"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10WindowsBuild.cs.meta"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10RouteContract.cs.meta"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10SegmentTag.cs.meta"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV10TraversalProofProbe.cs.meta"),
]

GENERATED_FILES = [
    Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine.meta"),
    *[
        Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine") / name
        for name in (
            "KhufuV10_Gallery_Detail.asset",
            "KhufuV10_Gallery_Detail.asset.meta",
            "KhufuV10_Hybrid_Service_Return.asset",
            "KhufuV10_Hybrid_Service_Return.asset.meta",
            "KhufuV10_Limestone_Structure.asset",
            "KhufuV10_Limestone_Structure.asset.meta",
            "KhufuV10_Red_Granite_Boundary.asset",
            "KhufuV10_Red_Granite_Boundary.asset.meta",
            "KhufuV10_Route_Inlay.asset",
            "KhufuV10_Route_Inlay.asset.meta",
            "KhufuV10_Shadow_Recess.asset",
            "KhufuV10_Shadow_Recess.asset.meta",
        )
    ],
]

MATERIAL_FILES = [
    Path("Assets/_Project/Materials/KhufuV10Interior.meta"),
    *[
        Path("Assets/_Project/Materials/KhufuV10Interior") / name
        for name in (
            "V10_Aged_Limestone.mat",
            "V10_Aged_Limestone.mat.meta",
            "V10_Deep_Shadow.mat",
            "V10_Deep_Shadow.mat.meta",
            "V10_Gallery_Detail.mat",
            "V10_Gallery_Detail.mat.meta",
            "V10_Hybrid_Service.mat",
            "V10_Hybrid_Service.mat.meta",
            "V10_Red_Granite.mat",
            "V10_Red_Granite.mat.meta",
            "V10_Route_Amber.mat",
            "V10_Route_Amber.mat.meta",
        )
    ],
]

LEGACY_SCENE_DEPENDENCY_FILES = [
    Path("Assets/_Project/Art/Generated/PyramidReferenceMatchedV4.meta"),
    Path("Assets/_Project/Art/Generated/PyramidReferenceMatchedV4/Meshes.meta"),
    *[
        Path("Assets/_Project/Art/Generated/PyramidReferenceMatchedV4/Meshes") / name
        for name in (
            "PyramidV4_Casing_East.asset",
            "PyramidV4_Casing_East.asset.meta",
            "PyramidV4_Casing_North_Left.asset",
            "PyramidV4_Casing_North_Left.asset.meta",
            "PyramidV4_Casing_North_Right.asset",
            "PyramidV4_Casing_North_Right.asset.meta",
            "PyramidV4_Casing_North_Upper.asset",
            "PyramidV4_Casing_North_Upper.asset.meta",
            "PyramidV4_Casing_South.asset",
            "PyramidV4_Casing_South.asset.meta",
            "PyramidV4_Casing_West.asset",
            "PyramidV4_Casing_West.asset.meta",
            "PyramidV4_Section_Poche_Mesh.asset",
            "PyramidV4_Section_Poche_Mesh.asset.meta",
        )
    ],
]

RELEASE_INPUT_FILES = [
    Path(".gitattributes"),
    *SOURCE_FILES,
    *SOURCE_META_FILES,
    *GENERATED_FILES,
    *MATERIAL_FILES,
    *LEGACY_SCENE_DEPENDENCY_FILES,
]

DOC_FILES = [
    DOC_ROOT / name
    for name in (
        "GOAL.md",
        "LOOP.md",
        "PLAN.md",
        "README.md",
        "RESEARCH_BRIEF.md",
        "RULES.md",
        "STATUS.md",
        "TEST_PLAN.md",
        "disable-manifest.json",
        "performance-budget.json",
        "segment-classification.json",
        "staging-allowlist.txt",
    )
]

CAPTURE_ARTIFACTS = [
    RUN_ROOT / "captures/manifest.md",
    *[
        RUN_ROOT / "captures" / name
        for name in (
            "north_entrance_approach.png",
            "ascending_plug_girdle.png",
            "gallery_foot_queen_boundary.png",
            "grand_gallery_long_axis.png",
            "gallery_corbel_slot_detail.png",
            "great_step_boundary.png",
            "hybrid_service_return.png",
            "pyramid_cutaway_integration.png",
            "mutation_superseded_overlap.png",
        )
    ],
]

EDITOR_ARTIFACTS = [
    RUN_ROOT / "audit.json",
    RUN_ROOT / "audit.md",
    RUN_ROOT / "audit-unity.log",
    RUN_ROOT / "postwrite-audit.md",
    RUN_ROOT / "validation.md",
    RUN_ROOT / "idempotence.md",
    RUN_ROOT / "pair-mutation.md",
    RUN_ROOT / "transition-mutation.md",
    RUN_ROOT / "metric-mutation.md",
    RUN_ROOT / "transition-amendment.md",
    RUN_ROOT / "static-all-gates-hit-classification.log",
    RUN_ROOT / "capture-export-geometry-amendment.log",
    RUN_ROOT / "legacy-v4-final.log",
    RUN_ROOT / "legacy-v5-gate4-final.log",
    RUN_ROOT / "legacy-v5-playmode-final.log",
    RUN_ROOT / "legacy-regression.md",
    RUN_ROOT / "python-tests.md",
    RUN_ROOT / "manual-qa.md",
    RUN_ROOT / "debugging-audit.md",
    RUN_ROOT / "clean-index-import.log",
    RUN_ROOT / "clean-index-import.md",
    *CAPTURE_ARTIFACTS,
]

PLAYER_ARTIFACTS = [
    RUN_ROOT / "windows-build-hit-classification.log",
    RUN_ROOT / "windows-build.md",
    RUN_ROOT / "windows-player-validation.md",
    *[
        RUN_ROOT / "player-proof" / name
        for name in (
            "normal-player.log",
            "boundary-player.log",
            "error-metric-player.log",
            "v10-final-round-trip.md",
            "v10-final-boundary-control.md",
            "v10-final-error-metric-mutation.md",
            "v10-final-normal-round-trip-movement-trace.csv",
            "v10-final-great-step-boundary-control-movement-trace.csv",
            "v10-final-error-metric-negative-control-movement-trace.csv",
            "v10-final-normal-round-trip-north_entrance_start.png",
            "v10-final-normal-round-trip-great_step_stop.png",
            "v10-final-normal-round-trip-return_to_north_exit.png",
            "v10-final-great-step-boundary-control-great_step_control_start.png",
            "v10-final-great-step-boundary-control-great_step_named_blocker.png",
        )
    ],
]

PERFORMANCE_ARTIFACTS = [
    DOC_ROOT / "performance-budget.json",
    *[
        RUN_ROOT / "performance-final" / name
        for name in (
            "performance-validation.md",
            "player.log",
            "v10-final-performance.md",
            "v10-final.raw",
            "v10-final-windows-player-initial.png",
            "v10-final-windows-player-operator.png",
        )
    ],
]

REVIEW_FILES = [
    EXTERNAL_FABLE,
    RUN_ROOT / "external-fable-final-review.md",
    RUN_ROOT / "local-fable-final.md",
    RUN_ROOT / "review-work.md",
]

REQUIRED_TOKENS = {
    RUN_ROOT / "audit.md": "KHUFU_V10_PREWRITE_AUDIT: passed",
    RUN_ROOT / "postwrite-audit.md": "KHUFU_V10_POSTWRITE_AUDIT: passed",
    RUN_ROOT / "validation.md": "KHUFU_V10_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "V10_IDEMPOTENCE: passed",
    RUN_ROOT / "pair-mutation.md": "V10_PAIR_MUTATION: passed",
    RUN_ROOT / "transition-mutation.md": "V10_TRANSITION_MUTATION: passed",
    RUN_ROOT / "metric-mutation.md": "V10_METRIC_MUTATION: passed",
    RUN_ROOT / "transition-amendment.md": "KHUFU_V10_TRANSITION_AMENDMENT: passed",
    RUN_ROOT / "captures/manifest.md": "V10_OVERLAP_MUTATION_CAPTURE: passed",
    RUN_ROOT / "static-all-gates-hit-classification.log": "CHANNEL_PLAY_KHUFU_V10_STATIC_GATES result=passed",
    RUN_ROOT / "windows-build-hit-classification.log": "CHANNEL_PLAY_KHUFU_V10_WINDOWS_BUILD result=passed",
    RUN_ROOT / "windows-player-validation.md": "V10_WINDOWS_PLAYER_VALIDATION: passed",
    RUN_ROOT / "player-proof/v10-final-round-trip.md": "V10_WINDOWS_PLAYER_TRAVERSAL: passed",
    RUN_ROOT / "player-proof/v10-final-boundary-control.md": "V10_WINDOWS_PLAYER_BOUNDARY_CONTROL: passed",
    RUN_ROOT / "player-proof/v10-final-error-metric-mutation.md":
        "V10_WINDOWS_PLAYER_ERROR_METRIC_MUTATION: passed",
    RUN_ROOT / "performance-final/performance-validation.md": "PERFORMANCE_VERDICT: passed",
    RUN_ROOT / "legacy-regression.md": "V10_LEGACY_REGRESSION: passed",
    RUN_ROOT / "python-tests.md": "V10_PYTHON_TESTS: passed",
    RUN_ROOT / "manual-qa.md": "V10_MANUAL_QA: passed",
    RUN_ROOT / "debugging-audit.md": "V10_DEBUGGING_AUDIT: passed",
    RUN_ROOT / "clean-index-import.md": "V10_CLEAN_INDEX_IMPORT: passed",
}

EXPECTED_PNG_DIMENSIONS = {
    **{path: (1600, 1000) for path in CAPTURE_ARTIFACTS if path.suffix == ".png"},
    **{path: (1536, 1024) for path in PLAYER_ARTIFACTS if path.suffix == ".png"},
    **{path: (1536, 1024) for path in PERFORMANCE_ARTIFACTS if path.suffix == ".png"},
}

STRICT_PREFIXES = (
    "Assets/_Project/Art/Generated/PyramidReferenceMatchedV4",
    "Assets/_Project/Art/Generated/KhufuV10InteriorSpine",
    "Assets/_Project/Materials/KhufuV10Interior",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10",
    "Assets/_Project/Scripts/Gameplay/KhufuV10",
    "docs/khufu-v10-interior-spine/",
    "tools/validate_khufu_v10",
    "tools/tests/test_validate_khufu_v10",
    "work/fable-harness/khufu-v10-boundary-hit-classification-blocker",
    "work/fable-harness/khufu-v10-capture-blocker",
    "work/fable-harness/khufu-v10-interior-spine-final-review",
    "work/fable-harness/khufu-v10-traversal-blocker",
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    facts: dict[str, str | int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def file_record(root: Path, relative: Path) -> dict[str, str | int]:
    path = root / relative
    return {"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def runtime_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in (root / BUILD_ROOT).rglob("*") if path.is_file())


def read_allowlist(root: Path) -> set[str]:
    lines = (root / ALLOWLIST).read_text(encoding="utf-8").splitlines()
    normalized = (line.strip() for line in lines)
    return {line.replace("\\", "/") for line in normalized if line and not line.startswith("#")}


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def fable_verdict(text: str) -> str | None:
    if "FABLE_HARNESS_ERROR" in text:
        return None
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    verdicts = [line for line in lines if re.fullmatch(r"verdict:\s*(ship|revise)", line)]
    if len(verdicts) != 1 or verdicts[0] != lines[-1]:
        return None
    return verdicts[0].split(":", 1)[1].strip()


def write_binding(root: Path, output: Path, schema: str, artifacts: list[Path], include_runtime: bool) -> None:
    payload: dict[str, object] = {
        "schema": schema,
        "verdict": "passed",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scene": file_record(root, SCENE),
        "staged_scene": index_record(root, SCENE.as_posix()),
        "player": file_record(root, PLAYER),
        "built_level": file_record(root, BUILT_LEVEL),
        "managed_assembly": file_record(root, ASSEMBLY),
        "working_release_inputs": [file_record(root, path) for path in RELEASE_INPUT_FILES],
        "release_inputs": [index_record(root, path.as_posix()) for path in RELEASE_INPUT_FILES],
        "artifacts": [file_record(root, path) for path in artifacts],
    }
    if include_runtime:
        payload["runtime_files"] = [file_record(root, path) for path in runtime_files(root)]
    target = root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_record(root: Path, record: dict, label: str, result: ValidationResult) -> None:
    relative = Path(str(record.get("path", "")))
    path = root / relative
    if not path.is_file():
        result.errors.append(f"{label} missing file: {relative.as_posix()}")
        return
    if record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
        result.errors.append(f"{label} hash or size drifted: {relative.as_posix()}")


def check_binding(
    root: Path,
    path: Path,
    schema: str,
    artifacts: list[Path],
    include_runtime: bool,
    result: ValidationResult,
) -> None:
    target = root / path
    if not target.is_file():
        result.errors.append(f"binding missing: {path.as_posix()}")
        return
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("schema") != schema or payload.get("verdict") != "passed":
        result.errors.append(f"binding header invalid: {path.as_posix()}")
    for key in ("scene", "player", "built_level", "managed_assembly"):
        check_record(root, payload.get(key, {}), f"{path.as_posix()} {key}", result)
    check_index_record(root, payload.get("staged_scene", {}), f"{path.as_posix()} staged scene", result)
    working_records = payload.get("working_release_inputs", [])
    working_paths = {record.get("path") for record in working_records}
    expected_inputs = {item.as_posix() for item in RELEASE_INPUT_FILES}
    if working_paths != expected_inputs:
        result.errors.append(f"binding working release-input inventory drifted: {path.as_posix()}")
    for record in working_records:
        check_record(root, record, f"{path.as_posix()} working release input", result)
    input_records = payload.get("release_inputs", [])
    input_paths = {record.get("path") for record in input_records}
    if input_paths != expected_inputs:
        result.errors.append(f"binding release-input inventory drifted: {path.as_posix()}")
    for record in input_records:
        check_index_record(root, record, f"{path.as_posix()} release input", result)
    records = payload.get("artifacts", [])
    actual_paths = {record.get("path") for record in records}
    expected_paths = {item.as_posix() for item in artifacts}
    if actual_paths != expected_paths:
        result.errors.append(f"binding artifact inventory drifted: {path.as_posix()}")
    for record in records:
        check_record(root, record, path.as_posix(), result)
    if include_runtime:
        runtime_records = payload.get("runtime_files", [])
        runtime_paths = {record.get("path") for record in runtime_records}
        expected_runtime = {item.as_posix() for item in runtime_files(root)}
        if runtime_paths != expected_runtime:
            result.errors.append(f"binding runtime inventory drifted: {path.as_posix()}")
        for record in runtime_records:
            check_record(root, record, f"{path.as_posix()} runtime", result)


def git_paths(root: Path, *args: str) -> set[str]:
    process = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, check=True)
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in process.stdout.split(b"\0")
        if item
    }


def index_bytes(root: Path, path: str) -> bytes | None:
    process = subprocess.run(
        ["git", "show", f":{path}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process.stdout if process.returncode == 0 else None


def index_record(root: Path, path: str) -> dict[str, str | int]:
    content = index_bytes(root, path)
    if content is None:
        return {"path": path, "bytes": -1, "sha256": ""}
    return {"path": path, "bytes": len(content), "sha256": sha256_bytes(content)}


def check_index_record(root: Path, record: dict, label: str, result: ValidationResult) -> None:
    path = str(record.get("path", ""))
    content = index_bytes(root, path)
    if content is None:
        result.errors.append(f"{label} missing staged blob: {path}")
        return
    if record.get("bytes") != len(content) or record.get("sha256") != sha256_bytes(content):
        result.errors.append(f"{label} staged hash or size drifted: {path}")


def write_staged_inventory(root: Path) -> None:
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    payload = {
        "schema": "khufu-v10-staged-inventory-v1",
        "files": [index_record(root, path) for path in sorted(staged - helpers)],
    }
    target = root / STAGED_INVENTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_staged_inventory(root: Path, result: ValidationResult) -> list[dict]:
    target = root / STAGED_INVENTORY
    if not target.is_file():
        result.errors.append(f"staged inventory missing: {STAGED_INVENTORY.as_posix()}")
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        result.errors.append(f"staged inventory is invalid JSON: {STAGED_INVENTORY.as_posix()}")
        return []
    if payload.get("schema") != "khufu-v10-staged-inventory-v1":
        result.errors.append(f"staged inventory schema invalid: {STAGED_INVENTORY.as_posix()}")
    records = payload.get("files", [])
    if not isinstance(records, list):
        result.errors.append(f"staged inventory files invalid: {STAGED_INVENTORY.as_posix()}")
        return []
    return records


def status_paths(root: Path) -> set[str]:
    process = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        stdout=subprocess.PIPE,
        check=True,
    )
    paths: set[str] = set()
    for item in process.stdout.split(b"\0"):
        if not item:
            continue
        text = item.decode("utf-8")
        if len(text) >= 4:
            paths.add(text[3:].replace("\\", "/"))
    return paths


def check_staged(root: Path, result: ValidationResult) -> None:
    allowlist = read_allowlist(root)
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    dirty = status_paths(root)
    permitted = allowlist - {POSTCOMMIT_REPORT.as_posix()}
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    if not staged:
        result.errors.append("staged index is empty")
        return
    for path in sorted(staged - permitted):
        result.errors.append(f"unexpected staged path: {path}")
    required = dirty.intersection(permitted)
    for path in sorted(required - staged):
        result.errors.append(f"allowlisted release path is not staged: {path}")
    for path in sorted(helpers - staged):
        result.errors.append(f"staged release helper is not staged: {path}")
    for path in sorted(dirty - allowlist):
        if path == "Assets/_Project/Scripts/Gameplay/KhufuControllerHitRecorder.cs" or path.startswith(STRICT_PREFIXES):
            result.errors.append(f"unlisted V10 scope path: {path}")
    unstaged = git_paths(root, "diff", "--name-only", "-z")
    for path in sorted(staged.intersection(unstaged)):
        result.errors.append(f"staged path has an additional unstaged delta: {path}")

    records = read_staged_inventory(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    if inventory_paths != staged - helpers:
        result.errors.append("staged inventory path set differs from the exact release inventory")
    for record in records:
        check_index_record(root, record, "staged inventory", result)

    binding = json.loads((root / EDITOR_BINDING).read_text(encoding="utf-8"))
    bound_records = [binding.get("staged_scene", {}), *binding.get("release_inputs", [])]
    for record in bound_records:
        path = str(record.get("path", ""))
        check_index_record(root, record, "editor binding", result)
    result.facts["staged_files"] = len(staged)


def check_postcommit(root: Path, result: ValidationResult) -> None:
    allowlist = read_allowlist(root)
    committed = git_paths(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD")
    records = read_staged_inventory(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    expected = inventory_paths | {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    if not inventory_paths:
        result.errors.append("post-commit staged inventory is empty")
    for path in sorted(committed - expected):
        result.errors.append(f"post-commit path is outside exact staged inventory: {path}")
    for path in sorted(expected - committed):
        result.errors.append(f"staged inventory path is absent from HEAD commit: {path}")
    for path in sorted(expected - allowlist):
        result.errors.append(f"post-commit inventory path is outside V10 allowlist: {path}")
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    if staged:
        result.errors.append("staged index is not empty after commit")
    dirty = status_paths(root)
    for path in sorted(dirty.intersection(expected)):
        result.errors.append(f"post-commit release path has worktree drift: {path}")
    for record in records:
        check_index_record(root, record, "post-commit inventory", result)
    staged_report = (root / STAGED_REPORT).read_text(encoding="utf-8")
    report_tokens = (
        "- Staged index checked: `True`",
        f"- scene_sha256: `{sha256(root / SCENE)}`",
        f"- assembly_sha256: `{sha256(root / ASSEMBLY)}`",
        "V10_RELEASE_VERDICT: passed",
    )
    for token in report_tokens:
        if token not in staged_report:
            result.errors.append(f"post-commit staged receipt token missing: {token}")
    result.facts["committed_files"] = len(committed)


def check_material_references(root: Path, result: ValidationResult) -> None:
    scene_text = (root / SCENE).read_text(encoding="utf-8")
    dependency_metas = [path for path in MATERIAL_FILES if path.name.endswith(".mat.meta")]
    dependency_metas.extend(path for path in LEGACY_SCENE_DEPENDENCY_FILES if path.name.endswith(".asset.meta"))
    for relative in dependency_metas:
        text = (root / relative).read_text(encoding="utf-8")
        match = re.search(r"^guid:\s*([0-9a-f]{32})\s*$", text, re.MULTILINE)
        if match is None:
            result.errors.append(f"scene dependency metadata GUID missing: {relative.as_posix()}")
            continue
        if match.group(1) not in scene_text:
            result.errors.append(f"scene does not reference required dependency GUID: {relative.as_posix()}")


def check_forbidden_receipt_vocabulary(root: Path, files: list[Path], result: ValidationResult) -> None:
    forbidden = b"Well Shaft"
    for relative in sorted(set(files)):
        if forbidden in (root / relative).read_bytes():
            result.errors.append(f"forbidden receipt vocabulary: {relative.as_posix()}")


def validate(root: Path, require_reviews: bool, check_index: bool, postcommit: bool) -> ValidationResult:
    result = ValidationResult()
    required = [SCENE, PLAYER, BUILT_LEVEL, ASSEMBLY, *RELEASE_INPUT_FILES, *DOC_FILES,
                *EDITOR_ARTIFACTS, *PLAYER_ARTIFACTS, *PERFORMANCE_ARTIFACTS]
    if require_reviews:
        required.extend(REVIEW_FILES)
    for relative in required:
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            result.errors.append(f"required release file missing or empty: {relative.as_posix()}")
    if result.errors:
        return result

    check_material_references(root, result)
    for relative, token in REQUIRED_TOKENS.items():
        if token not in (root / relative).read_text(encoding="utf-8", errors="replace"):
            result.errors.append(f"required pass token missing: {relative.as_posix()} -> {token}")

    scene_hash = sha256(root / SCENE)
    player_hash = sha256(root / PLAYER)
    level_hash = sha256(root / BUILT_LEVEL)
    assembly_hash = sha256(root / ASSEMBLY)
    build_text = (root / RUN_ROOT / "windows-build.md").read_text(encoding="utf-8")
    for label, value in (("scene", scene_hash), ("player", player_hash), ("level", level_hash),
                         ("assembly", assembly_hash)):
        if value not in build_text:
            result.errors.append(f"Windows build receipt is not bound to current {label}")
    summary = (root / RUN_ROOT / "windows-player-validation.md").read_text(encoding="utf-8")
    if scene_hash not in summary or assembly_hash not in summary:
        result.errors.append("Windows player summary omits final scene or assembly hash")

    capture_manifest = (root / RUN_ROOT / "captures/manifest.md").read_text(encoding="utf-8")
    if scene_hash not in capture_manifest:
        result.errors.append("capture manifest is not bound to final scene")
    for relative, dimensions in EXPECTED_PNG_DIMENSIONS.items():
        path = root / relative
        try:
            observed = png_dimensions(path)
        except ValueError as error:
            result.errors.append(f"{relative.as_posix()}: {error}")
            continue
        if observed != dimensions:
            result.errors.append(f"PNG dimensions drifted: {relative.as_posix()} {observed} != {dimensions}")
        if path.stat().st_size < 65536:
            result.errors.append(f"PNG is too small: {relative.as_posix()}")
    hashes = [sha256(root / relative) for relative in EXPECTED_PNG_DIMENSIONS]
    if len(hashes) != len(set(hashes)):
        result.errors.append("required PNG evidence contains duplicate files")

    normal = (root / RUN_ROOT / "player-proof/v10-final-round-trip.md").read_text(encoding="utf-8")
    boundary = (root / RUN_ROOT / "player-proof/v10-final-boundary-control.md").read_text(encoding="utf-8")
    if normal.count("/ fresh `True` / semantic `True`") != 3:
        result.errors.append("normal traversal freshness/semantic count is not 3")
    if boundary.count("/ fresh `True` / semantic `True`") != 2:
        result.errors.append("boundary freshness/semantic count is not 2")
    if "Reached route anchors: `16/16`" not in normal or "Maximum step error: `0.150 m`" not in normal:
        result.errors.append("normal traversal metrics drifted")
    exact_wall = "V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary"
    ground = "V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp"
    if exact_wall not in boundary or ground not in boundary or "Blocked ambiguous collider: `none`" not in boundary:
        result.errors.append("Great Step side/ground identity proof drifted")

    check_binding(root, EDITOR_BINDING, EDITOR_SCHEMA, EDITOR_ARTIFACTS, False, result)
    check_binding(root, PLAYER_BINDING, PLAYER_SCHEMA, PLAYER_ARTIFACTS, True, result)
    check_binding(root, PERFORMANCE_BINDING, PERFORMANCE_SCHEMA, PERFORMANCE_ARTIFACTS, True, result)

    vocabulary_files = [*EDITOR_ARTIFACTS, *PLAYER_ARTIFACTS, *PERFORMANCE_ARTIFACTS]

    if require_reviews:
        verdict = fable_verdict((root / EXTERNAL_FABLE).read_text(encoding="utf-8"))
        if verdict != "ship":
            result.errors.append("external Fable final verdict is not ship")
        review_tokens = {
            RUN_ROOT / "external-fable-final-review.md": "V10_EXTERNAL_FABLE_REVIEW: addressed",
            RUN_ROOT / "local-fable-final.md": "V10_LOCAL_FABLE: ship",
            RUN_ROOT / "review-work.md": "V10_REVIEW_WORK: passed",
        }
        for relative, token in review_tokens.items():
            if token not in (root / relative).read_text(encoding="utf-8"):
                result.errors.append(f"review pass token missing: {relative.as_posix()}")
        vocabulary_files.extend(REVIEW_FILES)

    check_forbidden_receipt_vocabulary(root, vocabulary_files, result)

    if check_index:
        check_staged(root, result)
    if postcommit:
        check_postcommit(root, result)
    result.facts.update({
        "scene_sha256": scene_hash,
        "player_sha256": player_hash,
        "assembly_sha256": assembly_hash,
        "runtime_files": len(runtime_files(root)),
        "required_files": len(required),
        "png_files": len(EXPECTED_PNG_DIMENSIONS),
    })
    return result


def write_report(path: Path, result: ValidationResult, require_reviews: bool, check_index: bool,
                 postcommit: bool) -> None:
    lines = [
        "# Khufu V10 Release Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Reviews required: `{require_reviews}`",
        f"- Staged index checked: `{check_index}`",
        f"- Post-commit checked: `{postcommit}`",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(result.facts.items()))
    lines.extend(f"- Failure: `{error}`" for error in result.errors)
    lines.extend(["", f"V10_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh-bindings", action="store_true")
    parser.add_argument("--require-reviews", action="store_true")
    parser.add_argument("--check-staged", action="store_true")
    parser.add_argument("--postcommit", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    if args.refresh_bindings:
        write_binding(root, EDITOR_BINDING, EDITOR_SCHEMA, EDITOR_ARTIFACTS, False)
        write_binding(root, PLAYER_BINDING, PLAYER_SCHEMA, PLAYER_ARTIFACTS, True)
        write_binding(root, PERFORMANCE_BINDING, PERFORMANCE_SCHEMA, PERFORMANCE_ARTIFACTS, True)
    if args.check_staged:
        write_staged_inventory(root)
    result = validate(root, args.require_reviews, args.check_staged, args.postcommit)
    if args.check_staged and output.resolve() != (root / STAGED_REPORT).resolve():
        result.errors.append(f"staged validation output must be {STAGED_REPORT.as_posix()}")
    if args.postcommit and output.resolve() != (root / POSTCOMMIT_REPORT).resolve():
        result.errors.append(f"post-commit validation output must be {POSTCOMMIT_REPORT.as_posix()}")
    write_report(output, result, args.require_reviews, args.check_staged, args.postcommit)
    print(f"V10_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
