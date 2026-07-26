from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


RUN_ROOT = Path("runs/khufu-v12-queen-circuit")
DOC_ROOT = Path("docs/khufu-v12-queen-circuit")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
GIT_ATTRIBUTES = Path(".gitattributes")
BUILD_ROOT = Path("Builds/KhufuV12")
PLAYER = BUILD_ROOT / "ChannelPlayKhufuV12.exe"
BUILT_LEVEL = BUILD_ROOT / "ChannelPlayKhufuV12_Data/level0"
ASSEMBLY = BUILD_ROOT / "ChannelPlayKhufuV12_Data/Managed/Assembly-CSharp.dll"
ALLOWLIST = DOC_ROOT / "staging-allowlist.txt"
STAGED_INVENTORY = RUN_ROOT / "staged-inventory.json"
STAGED_REPORT = RUN_ROOT / "staged-index-validation.md"
POSTCOMMIT_REPORT = RUN_ROOT / "post-commit-validation.md"
FABLE_FINAL = Path(
    "work/fable-harness/khufu-v12-queen-circuit-final-review.opus.followup.md"
)
FABLE_RESOLUTION = Path(
    "work/fable-harness/khufu-v12-queen-circuit-final-review-resolution.md"
)

EXPECTED_SCENE_SHA256 = (
    "eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c"
)
EXPECTED_STATIC_SIGNATURE = (
    "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd"
)
EXPECTED_V11_RESTORED_SIGNATURE = (
    "9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9"
)
EXPECTED_GENERATED_SIGNATURE = (
    "33fbeb4df333143dcc417e18e09e3ee430826ce8d87b0004ef5d53a3108d0435"
)
RETIRED_MIGRATION_HASHES = {
    "aad904717bade91e91a7839a3a5bb53ddd60c7380e3959e18320f3719cacd9c5",
    "6b15448ade13932b6c9a968f4c44f421be56657272ab834e03bf4ab0b26c3644",
    "d23f207c2d621ff228e729dee826615b574820229b45d1db6377caf258241248",
}

EDITOR_SOURCES = [
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitAudit.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitBuilder.cs"),
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV12QueenCircuitLegacyRegression.cs"
    ),
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV12QueenCircuitMeshPipeline.cs"
    ),
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV12QueenCircuitScreenshotExporter.cs"
    ),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitValidator.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12WindowsBuild.cs"),
]
GAMEPLAY_SOURCES = [
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12ControllerHitRecorder.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12QueenRouteContract.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12SegmentTag.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12TransitionControl.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12TraversalProofProbe.cs"),
]
PYTHON_SOURCES = [
    Path("tools/validate_khufu_v12_prewrite.py"),
    Path("tools/validate_khufu_v12_release.py"),
    Path("tools/tests/test_validate_khufu_v12_prewrite.py"),
    Path("tools/tests/test_validate_khufu_v12_release.py"),
]
SOURCE_FILES = [
    SCENE,
    *EDITOR_SOURCES,
    *GAMEPLAY_SOURCES,
    *PYTHON_SOURCES,
    GIT_ATTRIBUTES,
]
UNITY_SCRIPT_METAS = [Path(str(path) + ".meta") for path in (*EDITOR_SOURCES, *GAMEPLAY_SOURCES)]

BUILD_BOUND_SOURCES = [
    SCENE,
    *GAMEPLAY_SOURCES,
    EDITOR_SOURCES[1],
    EDITOR_SOURCES[3],
    EDITOR_SOURCES[5],
    EDITOR_SOURCES[4],
    EDITOR_SOURCES[2],
    EDITOR_SOURCES[6],
]
CAPTURE_BOUND_SOURCES = [
    SCENE,
    EDITOR_SOURCES[1],
    EDITOR_SOURCES[3],
    EDITOR_SOURCES[4],
    EDITOR_SOURCES[5],
]

MATERIAL_METAS = [
    Path("Assets/_Project/Materials/KhufuV12QueenCircuit") / name
    for name in (
        "V12_Queen_Detail.mat.meta",
        "V12_Queen_Inspection.mat.meta",
        "V12_Queen_Limestone.mat.meta",
        "V12_Queen_Route_Amber.mat.meta",
        "V12_Queen_Shadow.mat.meta",
    )
]
MATERIAL_FILES = [Path(str(path).removesuffix(".meta")) for path in MATERIAL_METAS]
GENERATED_ROOT = Path("Assets/_Project/Art/Generated/KhufuV12QueenCircuit")
MATERIAL_ROOT = Path("Assets/_Project/Materials/KhufuV12QueenCircuit")
GENERATED_METAS = [
    GENERATED_ROOT / (name + ".meta")
    for name in (
        "KhufuV12_Limestone_Detail.asset",
        "KhufuV12_Limestone_Structure.asset",
        "KhufuV12_Queen_Inspection_Accent.asset",
        "KhufuV12_Queen_Route_Inlay.asset",
        "KhufuV12_Shadow_Recess.asset",
        "KhufuV12_V10_Limestone_Open.asset",
        "KhufuV12_V10_Red_Granite_Open.asset",
    )
]
GENERATED_ASSETS = [Path(str(path).removesuffix(".meta")) for path in GENERATED_METAS]
ROOT_METAS = [Path(str(GENERATED_ROOT) + ".meta"), Path(str(MATERIAL_ROOT) + ".meta")]
SERIALIZED_SCRIPT_METAS = [
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12SegmentTag.cs.meta"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV12TransitionControl.cs.meta"),
]

CAPTURE_IMAGES = [
    RUN_ROOT / "captures" / name
    for name in (
        "queen_threshold_open_axis.png",
        "horizontal_passage_low_axis.png",
        "chamber_doorway_release.png",
        "queens_chamber_gabled_wide.png",
        "east_niche_and_narrow_mouths.png",
        "queen_circuit_integration.png",
    )
]

PLAYER_ARTIFACTS = [
    RUN_ROOT / "player-proof/v12-final-round-trip.md",
    RUN_ROOT / "player-proof/v12-final-boundary-control.md",
    RUN_ROOT / "player-proof/v12-final-normal-round-trip-movement-trace.csv",
    RUN_ROOT
    / "player-proof/v12-final-queen-boundary-control-movement-trace.csv",
]

REQUIRED_TOKENS = {
    RUN_ROOT / "prewrite-audit.md": "KHUFU_V12_PREWRITE_AUDIT: passed",
    RUN_ROOT / "prewrite-validation.md": "V12_PREWRITE_VERDICT: passed",
    RUN_ROOT / "static-validation.md": "KHUFU_V12_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "KHUFU_V12_IDEMPOTENCE: passed",
    RUN_ROOT / "negative-controls.md": "KHUFU_V12_NEGATIVE_CONTROLS: passed",
    RUN_ROOT / "captures/manifest.md": "KHUFU_V12_REQUIRED_CAPTURES: passed",
    RUN_ROOT
    / "captures/manual-semantic-review.md": (
        "KHUFU_V12_CAPTURE_SEMANTIC_REVIEW: passed"
    ),
    RUN_ROOT / "legacy-regression.md": "KHUFU_V12_LEGACY_REGRESSION: passed",
    RUN_ROOT
    / "python-tests.md": (
        "KHUFU_V12_PYTHON_TESTS: passed_with_frozen_unrelated_failures"
    ),
    RUN_ROOT / "clean-index-import.md": "KHUFU_V12_CLEAN_INDEX_IMPORT: passed",
    RUN_ROOT / "windows-build.md": "V12_WINDOWS_BUILD: passed",
    PLAYER_ARTIFACTS[0]: "V12_WINDOWS_PLAYER_TRAVERSAL: passed",
    PLAYER_ARTIFACTS[1]: "V12_WINDOWS_PLAYER_BOUNDARY_CONTROL: passed",
}
EXTRA_REQUIRED_TOKENS = {
    RUN_ROOT / "captures/manifest.md": "CAPTURE_INTEGRITY: passed",
}
FROZEN_PYTHON_FAILURE_IDS = {
    "tools/tests/test_validate_khufu_v5_harness.py::"
    "KhufuV5HarnessValidatorTests::test_current_harness_passes",
    "tools/tests/test_validate_khufu_v5_harness.py::"
    "KhufuV5HarnessValidatorTests::test_document_edit_invalidates_revision_hash",
    "tools/tests/test_validate_khufu_v5_harness.py::"
    "KhufuV5HarnessValidatorTests::test_validator_edit_invalidates_revision_hash",
    "tools/tests/test_validate_khufu_v6_visual_slice.py::"
    "KhufuV6VisualSliceValidatorTests::test_complete_fixture_passes",
    "tools/studio/company/tests/test_agent_runner.py::"
    "AgentRunnerTests::test_adapter_health_matrix_reports_version_path_and_roles",
    "tools/studio/company/tests/test_agent_runner.py::"
    "AgentRunnerTests::test_codex_adapter_falls_back_to_cli_when_sdk_auth_fails",
    "tools/studio/company/tests/test_agent_runner.py::"
    "AgentRunnerTests::test_dry_run_writes_agent_run_without_external_process",
    "tools/studio/company/tests/test_agent_runner.py::"
    "AgentRunnerTests::test_review_dry_run_moves_to_evidence_step",
    "tools/studio/company/tests/test_company_core.py::"
    "CompanyCoreTests::test_review_checkpoint_moves_task_to_evidence",
    "tools/studio/company/tests/test_company_core.py::"
    "CompanyCoreTests::test_verify_accepts_studio_checkpoint_and_closes_task",
    "tools/studio/company/tests/test_worker_fleet.py::"
    "WorkerFleetTests::test_render_worker_fleet_includes_capabilities_and_recommended_jobs",
    "tools/studio/tests/test_workspace_server.py::"
    "WorkspaceServerTests::test_orchestrator_job_extracts_task_id_and_workflow_path",
    "tools/studio/tests/test_workspace_server.py::"
    "WorkspaceServerTests::test_run_command_creates_async_job_receipt",
}

STRICT_PREFIXES = (
    "Assets/_Project/Art/Generated/KhufuV12QueenCircuit",
    "Assets/_Project/Materials/KhufuV12QueenCircuit",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12",
    "Assets/_Project/Scripts/Gameplay/KhufuV12",
    "docs/khufu-v12-queen-circuit/",
    "tools/validate_khufu_v12",
    "tools/tests/test_validate_khufu_v12",
    "work/fable-harness/khufu-v12",
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


def generated_asset_signature(root: Path) -> str:
    roots = (GENERATED_ROOT, MATERIAL_ROOT)
    paths: list[Path] = []
    for relative_root in roots:
        absolute_root = root / relative_root
        paths.extend(
            path.relative_to(root)
            for path in absolute_root.rglob("*")
            if path.is_file()
        )
        root_meta = Path(str(relative_root) + ".meta")
        if (root / root_meta).is_file():
            paths.append(root_meta)
    lines = [
        f"{path.as_posix()}|{sha256(root / path)}"
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
    ):
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def fable_verdict(text: str) -> str | None:
    if "FABLE_HARNESS_ERROR" in text:
        return None
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    verdict_lines = [line for line in lines if line.startswith("verdict:")]
    if len(verdict_lines) != 1 or verdict_lines[0] != lines[-1]:
        return None
    match = re.fullmatch(
        r"verdict:\s*(ship|revise minimally|do not ship)", verdict_lines[0]
    )
    return match.group(1) if match else None


def read_allowlist(root: Path) -> set[str]:
    lines = (root / ALLOWLIST).read_text(encoding="utf-8-sig").splitlines()
    entries: list[str] = []
    for raw in lines:
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        if "\\" in entry:
            raise ValueError(f"unsafe allowlist entry: {entry}")
        path = Path(entry)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "." in path.parts
            or "//" in entry
        ):
            raise ValueError(f"unsafe allowlist entry: {entry}")
        entries.append(entry)
    if len(entries) != len(set(entries)):
        raise ValueError("allowlist contains duplicate entries")
    return set(entries)


def require_exact_token(
    text: str, token: str, label: str, result: ValidationResult
) -> None:
    count = len(re.findall(rf"(?m)^{re.escape(token)}\r?$", text))
    if count != 1:
        result.errors.append(
            f"{label} must contain exactly one complete pass token line: {token}"
        )


def git_paths(root: Path, *args: str) -> set[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in process.stdout.split(b"\0")
        if item
    }


def index_bytes(root: Path, path: str) -> bytes | None:
    return git_blob_bytes(root, f":{path}")


def git_blob_bytes(root: Path, spec: str) -> bytes | None:
    process = subprocess.run(
        ["git", "show", spec],
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


def parse_status_paths(payload: bytes) -> set[str]:
    paths: set[str] = set()
    items = payload.split(b"\0")
    index = 0
    while index < len(items):
        item = items[index]
        index += 1
        if len(item) < 4:
            continue
        status = item[:2].decode("ascii")
        paths.add(item[3:].decode("utf-8").replace("\\", "/"))
        if "R" in status or "C" in status:
            if index < len(items) and items[index]:
                paths.add(items[index].decode("utf-8").replace("\\", "/"))
            index += 1
    return paths


def status_paths(root: Path) -> set[str]:
    process = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return parse_status_paths(process.stdout)


def is_unlisted_release_scope(path: str) -> bool:
    if path.startswith(STRICT_PREFIXES):
        return True
    run_prefix = RUN_ROOT.as_posix() + "/"
    if not path.startswith(run_prefix):
        return False
    if path.endswith(".log") or path == (
        RUN_ROOT / "legacy-v10-raw.md"
    ).as_posix():
        return False
    return Path(path).suffix.lower() in {".md", ".json", ".png", ".csv"}


def write_staged_inventory(root: Path) -> None:
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()
    payload = {
        "schema": "khufu-v12-staged-inventory-v1",
        "base_commit": base_commit,
        "files": [index_record(root, path) for path in sorted(staged - helpers)],
    }
    target = root / STAGED_INVENTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_staged_inventory(root: Path, result: ValidationResult) -> list[dict]:
    target = root / STAGED_INVENTORY
    if not target.is_file():
        result.errors.append(
            f"staged inventory missing: {STAGED_INVENTORY.as_posix()}"
        )
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        result.errors.append("staged inventory is invalid JSON")
        return []
    if payload.get("schema") != "khufu-v12-staged-inventory-v1":
        result.errors.append("staged inventory schema is invalid")
    records = payload.get("files", [])
    if not isinstance(records, list):
        result.errors.append("staged inventory files are invalid")
        return []
    for record in records:
        if not isinstance(record, dict):
            result.errors.append("staged inventory record is invalid")
            return []
    return records


def read_staged_base_commit(root: Path, result: ValidationResult) -> str:
    target = root / STAGED_INVENTORY
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return ""
    base_commit = payload.get("base_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", str(base_commit)):
        result.errors.append("staged inventory base_commit is invalid")
        return ""
    return str(base_commit)


def check_index_record(
    root: Path, record: dict, label: str, result: ValidationResult
) -> None:
    path = str(record.get("path", ""))
    content = index_bytes(root, path)
    if content is None:
        result.errors.append(f"{label} missing staged blob: {path}")
    elif (
        record.get("bytes") != len(content)
        or record.get("sha256") != sha256_bytes(content)
    ):
        result.errors.append(f"{label} staged hash or size drifted: {path}")


def check_staged(root: Path, result: ValidationResult) -> None:
    try:
        allowlist = read_allowlist(root)
    except ValueError as error:
        result.errors.append(str(error))
        return
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    dirty = status_paths(root)
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    permitted = allowlist - {POSTCOMMIT_REPORT.as_posix()}
    if not staged:
        result.errors.append("staged index is empty")
        return
    for path in sorted(staged - permitted):
        result.errors.append(f"unexpected staged path: {path}")
    for path in sorted(dirty.intersection(permitted) - staged):
        result.errors.append(f"allowlisted release path is not staged: {path}")
    for path in sorted(helpers - staged):
        result.errors.append(f"staged release helper is not staged: {path}")
    for path in sorted(dirty - allowlist):
        if is_unlisted_release_scope(path):
            result.errors.append(f"unlisted V12 scope path: {path}")
    unstaged = git_paths(root, "diff", "--name-only", "-z")
    for path in sorted(staged.intersection(unstaged)):
        result.errors.append(f"staged path has an additional unstaged delta: {path}")
    records = read_staged_inventory(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    if inventory_paths != staged - helpers:
        result.errors.append(
            "staged inventory path set differs from the exact release inventory"
        )
    for record in records:
        check_index_record(root, record, "staged inventory", result)
    result.facts["staged_files"] = len(staged)


def check_postcommit(root: Path, result: ValidationResult) -> None:
    try:
        allowlist = read_allowlist(root)
    except ValueError as error:
        result.errors.append(str(error))
        return
    committed = git_paths(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"
    )
    records = read_staged_inventory(root, result)
    base_commit = read_staged_base_commit(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    expected = inventory_paths | {
        STAGED_INVENTORY.as_posix(),
        STAGED_REPORT.as_posix(),
    }
    if not inventory_paths:
        result.errors.append("post-commit staged inventory is empty")
    for path in sorted(committed - expected):
        result.errors.append(
            f"post-commit path is outside exact staged inventory: {path}"
        )
    for path in sorted(expected - committed):
        result.errors.append(f"staged inventory path is absent from HEAD commit: {path}")
    for path in sorted(expected - allowlist):
        result.errors.append(
            f"post-commit inventory path is outside V12 allowlist: {path}"
        )
    if git_paths(root, "diff", "--cached", "--name-only", "-z"):
        result.errors.append("staged index is not empty after commit")
    for path in sorted(status_paths(root).intersection(expected)):
        result.errors.append(f"post-commit release path has worktree drift: {path}")
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD^"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if parent.returncode != 0 or parent.stdout.strip() != base_commit:
        result.errors.append("post-commit parent differs from staged inventory base_commit")
    for record in records:
        path = str(record.get("path", ""))
        content = git_blob_bytes(root, f"HEAD:{path}")
        if content is None:
            result.errors.append(f"post-commit HEAD blob missing: {path}")
        elif (
            record.get("bytes") != len(content)
            or record.get("sha256") != sha256_bytes(content)
        ):
            result.errors.append(f"post-commit HEAD blob drifted from inventory: {path}")
    result.facts["committed_files"] = len(committed)


def require_hash(
    text: str,
    root: Path,
    relative: Path,
    label: str,
    result: ValidationResult,
) -> None:
    if sha256(root / relative) not in text:
        result.errors.append(
            f"{label} is not bound to current {relative.as_posix()}"
        )


def check_scene_guid_references(root: Path, result: ValidationResult) -> None:
    scene_text = (root / SCENE).read_text(encoding="utf-8")
    for relative in (*MATERIAL_METAS, *GENERATED_METAS, *SERIALIZED_SCRIPT_METAS):
        text = (root / relative).read_text(encoding="utf-8")
        match = re.search(r"^guid:\s*([0-9a-f]{32})\s*$", text, re.MULTILINE)
        if match is None:
            result.errors.append(
                f"Unity metadata GUID missing: {relative.as_posix()}"
            )
        elif match.group(1) not in scene_text:
            result.errors.append(
                f"scene does not reference V12 Unity object: {relative.as_posix()}"
            )


def check_allowlist_contract(root: Path, result: ValidationResult) -> None:
    try:
        allowlist = read_allowlist(root)
    except ValueError as error:
        result.errors.append(str(error))
        return
    required_paths = {
        relative.as_posix()
        for relative in (
            *SOURCE_FILES,
            *UNITY_SCRIPT_METAS,
            *GENERATED_ASSETS,
            *GENERATED_METAS,
            *MATERIAL_FILES,
            *MATERIAL_METAS,
            *ROOT_METAS,
            *CAPTURE_IMAGES,
            *PLAYER_ARTIFACTS,
            *REQUIRED_TOKENS,
            ALLOWLIST,
            STAGED_INVENTORY,
            STAGED_REPORT,
            POSTCOMMIT_REPORT,
            FABLE_FINAL,
            FABLE_RESOLUTION,
            RUN_ROOT / "review-resolution.md",
            RUN_ROOT / "release-validation.md",
        )
    }
    for path in sorted(required_paths - allowlist):
        result.errors.append(f"required release path is absent from allowlist: {path}")
    result.facts["allowlisted_files"] = len(allowlist)


def validate(
    root: Path, require_reviews: bool, check_index: bool, postcommit: bool
) -> ValidationResult:
    result = ValidationResult()
    required = [
        PLAYER,
        BUILT_LEVEL,
        ASSEMBLY,
        ALLOWLIST,
        *SOURCE_FILES,
        *UNITY_SCRIPT_METAS,
        *GENERATED_ASSETS,
        *GENERATED_METAS,
        *MATERIAL_FILES,
        *MATERIAL_METAS,
        *ROOT_METAS,
        *CAPTURE_IMAGES,
        *PLAYER_ARTIFACTS,
        *REQUIRED_TOKENS,
        *EXTRA_REQUIRED_TOKENS,
    ]
    if require_reviews:
        required.extend(
            (
                FABLE_FINAL,
                FABLE_RESOLUTION,
                RUN_ROOT / "review-resolution.md",
            )
        )
    if check_index or postcommit:
        required.append(STAGED_INVENTORY)
    if check_index:
        required.append(STAGED_REPORT)
    for relative in sorted(set(required)):
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            result.errors.append(
                f"required release file missing or empty: {relative.as_posix()}"
            )
    if result.errors:
        return result

    check_allowlist_contract(root, result)
    check_scene_guid_references(root, result)
    for relative, token in (*REQUIRED_TOKENS.items(), *EXTRA_REQUIRED_TOKENS.items()):
        receipt = (root / relative).read_text(encoding="utf-8", errors="replace")
        require_exact_token(receipt, token, relative.as_posix(), result)

    if sha256(root / SCENE) != EXPECTED_SCENE_SHA256:
        result.errors.append("V12 scene SHA256 drifted from the canonical release scene")

    static = (root / RUN_ROOT / "static-validation.md").read_text(encoding="utf-8")
    for token in (
        EXPECTED_STATIC_SIGNATURE,
        EXPECTED_V11_RESTORED_SIGNATURE,
        "renderers=5_vertices=1176_triangles=588_colliders=22",
        "renderers=834_vertices=67070_triangles=48560_colliders=589",
    ):
        if token not in static:
            result.errors.append(f"static validation contract missing: {token}")

    idempotence = (root / RUN_ROOT / "idempotence.md").read_text(encoding="utf-8")
    for token in (
        f"First / second signature: `{EXPECTED_STATIC_SIGNATURE} / "
        f"{EXPECTED_STATIC_SIGNATURE}`",
        f"First / second scene SHA256: `{EXPECTED_SCENE_SHA256} / "
        f"{EXPECTED_SCENE_SHA256}`",
        f"First / second generated signature: `{EXPECTED_GENERATED_SIGNATURE} / "
        f"{EXPECTED_GENERATED_SIGNATURE}`",
    ):
        if token not in idempotence:
            result.errors.append(f"idempotence contract missing: {token}")
    observed_generated = generated_asset_signature(root)
    if observed_generated != EXPECTED_GENERATED_SIGNATURE:
        result.errors.append("generated/material asset signature drifted")

    negative = (root / RUN_ROOT / "negative-controls.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Queen gate restored: `rejected`",
        "Gallery floor ramp restored: `rejected`",
        "Historic service frame restored: `rejected`",
        "V4 renderer restored: `rejected`",
        "Structural pair drift: `rejected`",
        "Enclosure proxy disabled: `rejected`",
        "Owned object deactivated: `rejected`",
        "V4 glow ownership drift: `rejected`",
        "Injected successor failure -> rollback verified: `rejected`",
        f"Rollback scene SHA256: `{EXPECTED_SCENE_SHA256}`",
        f"Rollback generated signature: `{EXPECTED_GENERATED_SIGNATURE}`",
    ):
        if token not in negative:
            result.errors.append(f"negative-control contract missing: {token}")

    legacy = (root / RUN_ROOT / "legacy-regression.md").read_text(
        encoding="utf-8"
    )
    if (
        legacy.count("Classified exact V12 transition delta:") != 19
        or "classified exact V12 transition deltas=19" not in legacy
    ):
        result.errors.append("legacy receipt does not contain the exact 19 V10 deltas")
    for token in (
        f"Scene SHA256 before / after: `{EXPECTED_SCENE_SHA256} / "
        f"{EXPECTED_SCENE_SHA256}`",
        f"V11: `passed` / signature `{EXPECTED_V11_RESTORED_SIGNATURE}`",
    ):
        if token not in legacy:
            result.errors.append(f"legacy-regression contract missing: {token}")
    legacy_sources = (
        Path(
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayPyramidReferenceMatchedV4Builder.cs"
        ),
        Path(
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs"
        ),
        Path(
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV8TempleProductionArtValidator.cs"
        ),
        Path(
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV9CausewayFidelityValidator.cs"
        ),
        Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs"),
        Path(
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV11RoyalCircuitValidator.cs"
        ),
    )
    for relative in legacy_sources:
        require_hash(legacy, root, relative, "legacy regression receipt", result)

    rules = (root / DOC_ROOT / "RULES.md").read_text(encoding="utf-8")
    builder = (root / EDITOR_SOURCES[1]).read_text(encoding="utf-8")
    for retired_hash in RETIRED_MIGRATION_HASHES:
        if retired_hash not in rules:
            result.errors.append(
                f"retired migration hash is absent from RULES.md: {retired_hash}"
            )
        if retired_hash in builder:
            result.errors.append(
                f"retired migration hash was reintroduced in Builder: {retired_hash}"
            )
    if EXPECTED_SCENE_SHA256 not in rules:
        result.errors.append("RULES.md omits the canonical V12 scene hash")

    python_receipt = (root / RUN_ROOT / "python-tests.md").read_text(
        encoding="utf-8"
    )
    recorded_failures = {
        match.group(1)
        for match in re.finditer(r"(?m)^- `([^`\r\n]+::[^`\r\n]+)`\r?$", python_receipt)
    }
    if recorded_failures != FROZEN_PYTHON_FAILURE_IDS:
        result.errors.append(
            "Python receipt failure IDs differ from the exact frozen 13-test set"
        )

    capture_manifest = (root / RUN_ROOT / "captures/manifest.md").read_text(
        encoding="utf-8"
    )
    for relative in CAPTURE_BOUND_SOURCES:
        require_hash(capture_manifest, root, relative, "capture manifest", result)
    require_hash(
        capture_manifest,
        root,
        RUN_ROOT / "static-validation.md",
        "capture manifest",
        result,
    )
    image_hashes: list[str] = []
    for relative in CAPTURE_IMAGES:
        path = root / relative
        try:
            observed = png_dimensions(path)
        except ValueError as error:
            result.errors.append(f"{relative.as_posix()}: {error}")
            continue
        if observed != (1600, 1000):
            result.errors.append(
                f"PNG dimensions drifted: {relative.as_posix()} {observed}"
            )
        if path.stat().st_size < 65536:
            result.errors.append(f"PNG is too small: {relative.as_posix()}")
        digest = sha256(path)
        if digest not in capture_manifest:
            result.errors.append(
                f"capture manifest is not bound to current {relative.as_posix()}"
            )
        image_hashes.append(digest)
    if len(image_hashes) != len(set(image_hashes)):
        result.errors.append("required capture evidence contains duplicate PNG bytes")

    build = (root / RUN_ROOT / "windows-build.md").read_text(encoding="utf-8")
    for relative in (PLAYER, BUILT_LEVEL, ASSEMBLY, *BUILD_BOUND_SOURCES):
        require_hash(build, root, relative, "Windows build receipt", result)
    if "Errors / warnings: `0 / 185`" not in build:
        result.errors.append("Windows build warning/error count is not the reviewed 0/185")
    protected_assets = (
        "Protected V12 generated/material signature before/after: "
        f"`{EXPECTED_GENERATED_SIGNATURE} / {EXPECTED_GENERATED_SIGNATURE}`"
    )
    if protected_assets not in build:
        result.errors.append(
            "Windows build did not preserve the canonical generated/material signature"
        )

    normal = (root / PLAYER_ARTIFACTS[0]).read_text(encoding="utf-8")
    boundary = (root / PLAYER_ARTIFACTS[1]).read_text(encoding="utf-8")
    assembly_hash = sha256(root / ASSEMBLY)
    if assembly_hash not in normal or assembly_hash not in boundary:
        result.errors.append(
            "player traversal receipts are not bound to the current managed assembly"
        )
    require_hash(normal, root, PLAYER_ARTIFACTS[2], "normal player receipt", result)
    require_hash(
        boundary, root, PLAYER_ARTIFACTS[3], "boundary player receipt", result
    )
    normal_trace_rows = len(
        (root / PLAYER_ARTIFACTS[2])
        .read_text(encoding="utf-8-sig")
        .splitlines()
    )
    boundary_trace_rows = len(
        (root / PLAYER_ARTIFACTS[3])
        .read_text(encoding="utf-8-sig")
        .splitlines()
    )
    if normal_trace_rows != 137 or "records `136`" not in normal:
        result.errors.append("normal movement trace does not contain exactly 136 records")
    if boundary_trace_rows != 15 or "records `14`" not in boundary:
        result.errors.append(
            "boundary movement trace does not contain exactly 14 records"
        )
    controller_metrics = (
        "CharacterController radius / height / stepOffset / skinWidth: "
        "`0.450 / 2.000 / 0.300 / 0.050`"
    )
    if controller_metrics not in normal or controller_metrics not in boundary:
        result.errors.append(
            "player receipts omit the expected real CharacterController metrics"
        )
    for token in (
        "Reached route anchors: `15/15`",
        "Grounded steps/fraction: `136/136 / 1.000`",
        "Root renderers / enabled colliders: `5 / 22`",
        "Queen gate seen during normal route: `False`",
        "Narrow mouths sealed (north/south): `True / True`",
        "Traversed distance / max error / final error: `20.520 / 0.050 / 0.030`",
    ):
        if token not in normal:
            result.errors.append(f"normal player receipt contract missing: {token}")
    for token in (
        "Control boundary start distance: `1.726 m`",
        "Control pre-Move overlap empty: `True`",
        "Control maximum requested step: `0.080 m`",
        "V10_PROXY_Queen_Branch_Threshold_Queen_Ownership_Gate / Sides",
        "Control predecessor granite rebound: `True`",
        "Control Queen proxy enabled: `True`",
    ):
        if token not in boundary:
            result.errors.append(f"boundary player receipt contract missing: {token}")
    callback = re.search(
        r"(?m)^- Control Move / callback frame: `(\d+) / (\d+)`\r?$",
        boundary,
    )
    if (
        callback is None
        or callback.group(1) != callback.group(2)
        or int(callback.group(1)) < 0
    ):
        result.errors.append(
            "boundary player receipt does not prove a same-frame controller callback"
        )

    clean = (root / RUN_ROOT / "clean-index-import.md").read_text(encoding="utf-8")
    for relative in (
        SCENE,
        EDITOR_SOURCES[1],
        EDITOR_SOURCES[3],
        EDITOR_SOURCES[4],
        EDITOR_SOURCES[5],
        PYTHON_SOURCES[1],
        ALLOWLIST,
        GIT_ATTRIBUTES,
    ):
        require_hash(clean, root, relative, "clean-index receipt", result)
    for token in (EXPECTED_STATIC_SIGNATURE, "Compiler errors: `0`"):
        if token not in clean:
            result.errors.append(f"clean-index receipt contract missing: {token}")

    if require_reviews:
        if fable_verdict((root / FABLE_FINAL).read_text(encoding="utf-8")) != "ship":
            result.errors.append("external Fable final verdict is not ship")
        resolution = (root / RUN_ROOT / "review-resolution.md").read_text(
            encoding="utf-8"
        )
        if "KHUFU_V12_REVIEW_RESOLUTION: passed" not in resolution:
            result.errors.append("review resolution pass token is missing")

    if check_index:
        check_staged(root, result)
    if postcommit:
        check_postcommit(root, result)
    result.facts.update(
        {
            "assembly_sha256": sha256(root / ASSEMBLY),
            "capture_pngs": len(CAPTURE_IMAGES),
            "required_files": len(set(required)),
            "scene_sha256": sha256(root / SCENE),
        }
    )
    return result


def write_report(
    path: Path,
    result: ValidationResult,
    require_reviews: bool,
    check_index: bool,
    postcommit: bool,
) -> None:
    lines = [
        "# Khufu V12 Release Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Reviews required: `{require_reviews}`",
        f"- Staged index checked: `{check_index}`",
        f"- Post-commit checked: `{postcommit}`",
    ]
    lines.extend(
        f"- {key}: `{value}`" for key, value in sorted(result.facts.items())
    )
    lines.extend(f"- Failure: `{error}`" for error in result.errors)
    lines.extend(
        ["", f"KHUFU_V12_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}", ""]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def effective_review_requirement(
    explicitly_required: bool, check_staged: bool, postcommit: bool
) -> bool:
    return explicitly_required or check_staged or postcommit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh-staged-inventory", action="store_true")
    parser.add_argument("--require-reviews", action="store_true")
    parser.add_argument("--check-staged", action="store_true")
    parser.add_argument("--postcommit", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    if args.refresh_staged_inventory:
        write_staged_inventory(root)
    require_reviews = effective_review_requirement(
        args.require_reviews, args.check_staged, args.postcommit
    )
    result = validate(root, require_reviews, args.check_staged, args.postcommit)
    if args.check_staged and output.resolve() != (root / STAGED_REPORT).resolve():
        result.errors.append(
            f"staged validation output must be {STAGED_REPORT.as_posix()}"
        )
    if args.postcommit and output.resolve() != (root / POSTCOMMIT_REPORT).resolve():
        result.errors.append(
            f"post-commit validation output must be {POSTCOMMIT_REPORT.as_posix()}"
        )
    write_report(output, result, require_reviews, args.check_staged, args.postcommit)
    print(f"KHUFU_V12_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
