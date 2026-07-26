from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


BASELINE_COMMIT = "787476b58044e78f0c5164df408680e50fee47a2"
BASELINE_SCENE_SHA256 = (
    "eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c"
)
V12_STATIC_SIGNATURE = (
    "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd"
)
V11_RESTORED_SIGNATURE = (
    "9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9"
)

RUN_ROOT = Path("runs/khufu-v13-subterranean-threshold")
DOC_ROOT = Path("docs/khufu-v13-subterranean-threshold")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
GIT_ATTRIBUTES = Path(".gitattributes")
BUILD_ROOT = Path("Builds/KhufuV13")
PLAYER = BUILD_ROOT / "ChannelPlayKhufuV13.exe"
UNITY_PLAYER = BUILD_ROOT / "UnityPlayer.dll"
BUILT_LEVEL = BUILD_ROOT / "ChannelPlayKhufuV13_Data/level0"
ASSEMBLY = BUILD_ROOT / "ChannelPlayKhufuV13_Data/Managed/Assembly-CSharp.dll"

ALLOWLIST = DOC_ROOT / "staging-allowlist.txt"
STAGED_INVENTORY = RUN_ROOT / "staged-inventory.json"
STAGED_REPORT = RUN_ROOT / "staged-index-validation.md"
POSTCOMMIT_REPORT = RUN_ROOT / "post-commit-validation.md"
RELEASE_REPORT = RUN_ROOT / "release-validation.md"

FABLE_PROMPT = Path(
    "work/fable-harness/khufu-v13-subterranean-threshold-final-review.md"
)
FABLE_FINAL = Path(
    "work/fable-harness/khufu-v13-subterranean-threshold-final-review.fable.md"
)
FABLE_META = Path(str(FABLE_FINAL) + ".meta.json")
FABLE_RESOLUTION = Path(
    "work/fable-harness/khufu-v13-subterranean-threshold-final-review-resolution.md"
)

AUDIT = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdAudit.cs"
)
BUILDER = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs"
)
LEGACY = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression.cs"
)
PIPELINE = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.cs"
)
EXPORTER = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter.cs"
)
VALIDATOR = Path(
    "Assets/_Project/Scripts/Editor/"
    "ChannelPlayKhufuV13SubterraneanThresholdValidator.cs"
)
WINDOWS_BUILD = Path(
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13WindowsBuild.cs"
)
EDITOR_SOURCES = (
    AUDIT,
    BUILDER,
    LEGACY,
    PIPELINE,
    EXPORTER,
    VALIDATOR,
    WINDOWS_BUILD,
)

ROUTE_CONTRACT = Path(
    "Assets/_Project/Scripts/Gameplay/KhufuV13SubterraneanRouteContract.cs"
)
SEGMENT_TAG = Path("Assets/_Project/Scripts/Gameplay/KhufuV13SegmentTag.cs")
THRESHOLD_CONTROL = Path(
    "Assets/_Project/Scripts/Gameplay/KhufuV13SubterraneanThresholdControl.cs"
)
HIT_RECORDER = Path(
    "Assets/_Project/Scripts/Gameplay/KhufuV13ControllerHitRecorder.cs"
)
TRAVERSAL_PROBE = Path(
    "Assets/_Project/Scripts/Gameplay/KhufuV13TraversalProofProbe.cs"
)
GAMEPLAY_SOURCES = (
    ROUTE_CONTRACT,
    SEGMENT_TAG,
    THRESHOLD_CONTROL,
    HIT_RECORDER,
    TRAVERSAL_PROBE,
)
UNITY_SOURCES = (*EDITOR_SOURCES, *GAMEPLAY_SOURCES)
UNITY_SCRIPT_METAS = tuple(Path(str(path) + ".meta") for path in UNITY_SOURCES)
SERIALIZED_SCRIPT_METAS = (
    Path(str(SEGMENT_TAG) + ".meta"),
    Path(str(THRESHOLD_CONTROL) + ".meta"),
)

PYTHON_SOURCES = (
    Path("tools/validate_khufu_v13_prewrite.py"),
    Path("tools/validate_khufu_v13_release.py"),
    Path("tools/tests/test_validate_khufu_v13_prewrite.py"),
    Path("tools/tests/test_validate_khufu_v13_release.py"),
)
DOC_FILES = (
    DOC_ROOT / "GOAL.md",
    DOC_ROOT / "PLAN.md",
    DOC_ROOT / "RESEARCH_BRIEF.md",
    DOC_ROOT / "RULES.md",
    DOC_ROOT / "STATUS.md",
    DOC_ROOT / "TEST_PLAN.md",
    DOC_ROOT / "performance-budget.json",
    DOC_ROOT / "segment-classification.json",
    ALLOWLIST,
)

GENERATED_ROOT = Path(
    "Assets/_Project/Art/Generated/KhufuV13SubterraneanThreshold"
)
MATERIAL_ROOT = Path(
    "Assets/_Project/Materials/KhufuV13SubterraneanThreshold"
)
GENERATED_ASSETS = tuple(
    GENERATED_ROOT / f"KhufuV13_{name}.asset"
    for name in (
        "Bedrock_Structure",
        "Passage_Detail",
        "Subterranean_Shadow",
        "Evidence_Limit_Accent",
        "Subterranean_Route_Inlay",
    )
)
MATERIAL_FILES = tuple(
    MATERIAL_ROOT / name
    for name in (
        "V13_Bedrock_Structure.mat",
        "V13_Passage_Detail.mat",
        "V13_Subterranean_Shadow.mat",
        "V13_Evidence_Limit.mat",
        "V13_Route_Inlay.mat",
    )
)
GENERATED_METAS = tuple(Path(str(path) + ".meta") for path in GENERATED_ASSETS)
MATERIAL_METAS = tuple(Path(str(path) + ".meta") for path in MATERIAL_FILES)
ROOT_METAS = (
    Path(str(GENERATED_ROOT) + ".meta"),
    Path(str(MATERIAL_ROOT) + ".meta"),
)

CAPTURE_IMAGES = tuple(
    RUN_ROOT / "captures" / name
    for name in (
        "v10_v13_junction.png",
        "descending_long_axis.png",
        "bedrock_landing.png",
        "chamber_doorway_release.png",
        "subterranean_chamber_pit.png",
        "below_grade_integration.png",
    )
)
PLAYER_ARTIFACTS = (
    RUN_ROOT / "player-proof/v13-subterranean-final-round-trip.md",
    RUN_ROOT / "player-proof/v13-subterranean-final-boundary-control.md",
    RUN_ROOT
    / "player-proof/v13-subterranean-final-normal-round-trip-movement-trace.csv",
    RUN_ROOT
    / "player-proof/v13-subterranean-final-outside-wall-control-movement-trace.csv",
)

PHASE_RECEIPTS = (
    RUN_ROOT / "phase3-source-validation.md",
    RUN_ROOT / "phase4-source-validation.md",
    RUN_ROOT / "phase5-source-validation.md",
)
REQUIRED_TOKENS = {
    RUN_ROOT / "prewrite-audit.md": "KHUFU_V13_PREWRITE_AUDIT: passed",
    RUN_ROOT / "prewrite-validation.md": "V13_PREWRITE_VERDICT: passed",
    RUN_ROOT / "static-validation.md": "KHUFU_V13_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "KHUFU_V13_IDEMPOTENCE: passed",
    RUN_ROOT / "negative-controls.md": "KHUFU_V13_NEGATIVE_CONTROLS: passed",
    RUN_ROOT / "legacy-regression.md": "KHUFU_V13_LEGACY_REGRESSION: passed",
    RUN_ROOT / "captures/manifest.md": "KHUFU_V13_REQUIRED_CAPTURES: passed",
    RUN_ROOT
    / "captures/manual-semantic-review.md": (
        "KHUFU_V13_CAPTURE_SEMANTIC_REVIEW: passed"
    ),
    RUN_ROOT / "windows-build.md": "V13_WINDOWS_BUILD: passed",
    PLAYER_ARTIFACTS[0]: "V13_WINDOWS_PLAYER_TRAVERSAL: passed",
    PLAYER_ARTIFACTS[1]: "V13_WINDOWS_PLAYER_BOUNDARY_CONTROL: passed",
    RUN_ROOT / "python-tests.md": "KHUFU_V13_PYTHON_TESTS: passed",
    RUN_ROOT / "clean-index-import.md": "KHUFU_V13_CLEAN_INDEX_IMPORT: passed",
}
EXTRA_REQUIRED_TOKENS = {
    RUN_ROOT / "captures/manifest.md": "CAPTURE_INTEGRITY: passed",
}

LEGACY_SOURCES = (
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayPyramidReferenceMatchedV4Builder.cs"
    ),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs"),
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV6VisualFidelityValidator.cs"
    ),
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV7EntryWayfindingValidator.cs"
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
    Path(
        "Assets/_Project/Scripts/Editor/"
        "ChannelPlayKhufuV12QueenCircuitValidator.cs"
    ),
)
BUILD_BOUND_SOURCES = (SCENE, *UNITY_SOURCES)
CAPTURE_BOUND_SOURCES = (SCENE, BUILDER, PIPELINE, EXPORTER, VALIDATOR)
CLEAN_BOUND_SOURCES = (
    SCENE,
    BUILDER,
    PIPELINE,
    EXPORTER,
    VALIDATOR,
    LEGACY,
    WINDOWS_BUILD,
    PYTHON_SOURCES[1],
    ALLOWLIST,
    GIT_ATTRIBUTES,
)

FORBIDDEN_IMPLEMENTATION_TERMS = (
    "ScanPyramids",
    "SP_BV",
    "SP-BV",
    "SP_NFC",
    "SP-NFC",
    "Well Shaft",
    "WELL_SHAFT",
    "Underworld",
    "EARTH_KEY",
    "Earth-key",
    "Earth Key",
    "GLOBAL_LIGHTING",
)
STRICT_PREFIXES = (
    "Assets/_Project/Art/Generated/KhufuV13SubterraneanThreshold",
    "Assets/_Project/Materials/KhufuV13SubterraneanThreshold",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13",
    "Assets/_Project/Scripts/Gameplay/KhufuV13",
    "docs/khufu-v13-subterranean-threshold/",
    "tools/validate_khufu_v13",
    "tools/tests/test_validate_khufu_v13",
    "work/fable-harness/khufu-v13",
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


def generated_asset_signature(root: Path) -> str:
    paths: list[Path] = []
    for relative_root in (GENERATED_ROOT, MATERIAL_ROOT):
        absolute = root / relative_root
        if absolute.is_dir():
            paths.extend(
                path.relative_to(root) for path in absolute.rglob("*") if path.is_file()
            )
        root_meta = Path(str(relative_root) + ".meta")
        if (root / root_meta).is_file():
            paths.append(root_meta)
    lines = [
        f"{path.as_posix()}|{sha256(root / path)}"
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def fable_verdict(text: str) -> str | None:
    if "FABLE_HARNESS_ERROR" in text:
        return None
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    verdicts = [line for line in lines if line.startswith("verdict:")]
    if len(verdicts) != 1 or verdicts[0] != lines[-1]:
        return None
    match = re.fullmatch(
        r"verdict:\s*(ship|revise minimally|do not ship)", verdicts[0]
    )
    return match.group(1) if match else None


def require_exact_token(
    text: str, token: str, label: str, result: ValidationResult
) -> None:
    count = len(re.findall(rf"(?m)^{re.escape(token)}\r?$", text))
    if count != 1:
        result.errors.append(
            f"{label} must contain exactly one complete pass token line: {token}"
        )


def require_text(
    text: str, token: str, label: str, result: ValidationResult
) -> None:
    if token not in text:
        result.errors.append(f"{label} contract missing: {token}")


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


def extract_single(
    text: str, pattern: str, label: str, result: ValidationResult
) -> str:
    matches = re.findall(pattern, text, re.MULTILINE)
    if len(matches) != 1:
        result.errors.append(f"{label} must occur exactly once")
        return ""
    value = matches[0]
    return value if isinstance(value, str) else value[0]


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


def expected_allowlist() -> set[str]:
    paths: Iterable[Path] = (
        SCENE,
        *EDITOR_SOURCES,
        *GAMEPLAY_SOURCES,
        *UNITY_SCRIPT_METAS,
        *PYTHON_SOURCES,
        *DOC_FILES,
        *GENERATED_ASSETS,
        *GENERATED_METAS,
        *MATERIAL_FILES,
        *MATERIAL_METAS,
        *ROOT_METAS,
        RUN_ROOT / "prewrite-audit.json",
        *PHASE_RECEIPTS,
        *REQUIRED_TOKENS,
        *EXTRA_REQUIRED_TOKENS,
        *CAPTURE_IMAGES,
        *PLAYER_ARTIFACTS,
        RUN_ROOT / "review-resolution.md",
        RELEASE_REPORT,
        STAGED_INVENTORY,
        STAGED_REPORT,
        POSTCOMMIT_REPORT,
        FABLE_PROMPT,
        FABLE_FINAL,
        FABLE_META,
        FABLE_RESOLUTION,
    )
    return {path.as_posix() for path in paths}


def git_process(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_paths(root: Path, *args: str) -> set[str]:
    process = git_process(root, *args)
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in process.stdout.split(b"\0")
        if item
    }


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
    return parse_status_paths(
        git_process(
            root, "status", "--porcelain=v1", "-z", "--untracked-files=all"
        ).stdout
    )


def git_blob_bytes(root: Path, spec: str) -> bytes | None:
    process = git_process(root, "show", spec, check=False)
    return process.stdout if process.returncode == 0 else None


def index_bytes(root: Path, path: str) -> bytes | None:
    return git_blob_bytes(root, f":{path}")


def index_record(root: Path, path: str) -> dict[str, str | int]:
    content = index_bytes(root, path)
    if content is None:
        return {"path": path, "bytes": -1, "sha256": ""}
    return {"path": path, "bytes": len(content), "sha256": sha256_bytes(content)}


def check_baseline_ancestry(root: Path, result: ValidationResult) -> None:
    exists = git_process(
        root, "cat-file", "-e", f"{BASELINE_COMMIT}^{{commit}}", check=False
    )
    if exists.returncode != 0:
        result.errors.append("immutable V12 baseline commit is unavailable")
        return
    ancestor = git_process(
        root, "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD", check=False
    )
    if ancestor.returncode != 0:
        result.errors.append("HEAD does not descend from the immutable V12 baseline")
        return
    changed = git_paths(
        root, "diff", "--name-only", "-z", f"{BASELINE_COMMIT}..HEAD"
    )
    for path in sorted(changed - expected_allowlist()):
        result.errors.append(f"committed path since V12 baseline is outside allowlist: {path}")
    result.facts["baseline_commit"] = BASELINE_COMMIT
    result.facts["committed_since_baseline"] = len(changed)


def is_unlisted_release_scope(path: str) -> bool:
    if path.startswith(STRICT_PREFIXES):
        return True
    prefix = RUN_ROOT.as_posix() + "/"
    if not path.startswith(prefix):
        return False
    if path.endswith(".log"):
        return False
    return Path(path).suffix.lower() in {".md", ".json", ".png", ".csv"}


def write_staged_inventory(root: Path) -> None:
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    base_commit = git_process(root, "rev-parse", "HEAD").stdout.decode().strip()
    payload = {
        "schema": "khufu-v13-staged-inventory-v1",
        "base_commit": base_commit,
        "files": [index_record(root, path) for path in sorted(staged - helpers)],
    }
    target = root / STAGED_INVENTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_staged_payload(root: Path, result: ValidationResult) -> dict:
    target = root / STAGED_INVENTORY
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.errors.append(
            f"staged inventory missing: {STAGED_INVENTORY.as_posix()}"
        )
        return {}
    except json.JSONDecodeError:
        result.errors.append("staged inventory is invalid JSON")
        return {}
    if not isinstance(payload, dict):
        result.errors.append("staged inventory root is invalid")
        return {}
    if payload.get("schema") != "khufu-v13-staged-inventory-v1":
        result.errors.append("staged inventory schema is invalid")
    return payload


def read_staged_inventory(root: Path, result: ValidationResult) -> list[dict]:
    payload = read_staged_payload(root, result)
    records = payload.get("files", [])
    if not isinstance(records, list):
        result.errors.append("staged inventory files are invalid")
        return []
    for record in records:
        if not isinstance(record, dict):
            result.errors.append("staged inventory record is invalid")
            return []
        if set(record) != {"path", "bytes", "sha256"}:
            result.errors.append("staged inventory record keys are invalid")
            return []
        if (
            not isinstance(record["path"], str)
            or not isinstance(record["bytes"], int)
            or not re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"]))
        ):
            result.errors.append("staged inventory record values are invalid")
            return []
    paths = [record["path"] for record in records]
    if len(paths) != len(set(paths)):
        result.errors.append("staged inventory contains duplicate paths")
    return records


def read_staged_base_commit(root: Path, result: ValidationResult) -> str:
    payload = read_staged_payload(root, result)
    value = str(payload.get("base_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        result.errors.append("staged inventory base_commit is invalid")
        return ""
    return value


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
    except (FileNotFoundError, ValueError) as error:
        result.errors.append(str(error))
        return
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    dirty = status_paths(root)
    unstaged = git_paths(root, "diff", "--name-only", "-z")
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
            result.errors.append(f"unlisted V13 scope path: {path}")
    for path in sorted(staged.intersection(unstaged)):
        result.errors.append(f"staged path has an additional unstaged delta: {path}")
    records = read_staged_inventory(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    if inventory_paths != staged - helpers:
        result.errors.append(
            "staged inventory path set differs from the exact staged release inventory"
        )
    for record in records:
        check_index_record(root, record, "staged inventory", result)
    result.facts["staged_files"] = len(staged)


def check_postcommit(root: Path, result: ValidationResult) -> None:
    try:
        allowlist = read_allowlist(root)
    except (FileNotFoundError, ValueError) as error:
        result.errors.append(str(error))
        return
    committed = git_paths(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"
    )
    records = read_staged_inventory(root, result)
    base_commit = read_staged_base_commit(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    expected = inventory_paths | helpers
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
            f"post-commit inventory path is outside V13 allowlist: {path}"
        )
    if git_paths(root, "diff", "--cached", "--name-only", "-z"):
        result.errors.append("staged index is not empty after commit")
    for path in sorted(status_paths(root).intersection(expected)):
        result.errors.append(f"post-commit release path has worktree drift: {path}")
    parent = git_process(root, "rev-parse", "HEAD^", check=False)
    if parent.returncode != 0 or parent.stdout.decode().strip() != base_commit:
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


def check_allowlist_contract(root: Path, result: ValidationResult) -> None:
    try:
        observed = read_allowlist(root)
    except (FileNotFoundError, ValueError) as error:
        result.errors.append(str(error))
        return
    expected = expected_allowlist()
    for path in sorted(expected - observed):
        result.errors.append(f"required release path is absent from allowlist: {path}")
    for path in sorted(observed - expected):
        result.errors.append(f"unexpected path is present in exact allowlist: {path}")
    result.facts["allowlisted_files"] = len(observed)


def exact_files(root: Path, directory: Path) -> set[Path]:
    absolute = root / directory
    if not absolute.is_dir():
        return set()
    return {
        path.relative_to(root)
        for path in absolute.rglob("*")
        if path.is_file()
    }


def check_source_and_asset_inventory(root: Path, result: ValidationResult) -> None:
    expected_editor = {
        *EDITOR_SOURCES,
        *(Path(str(path) + ".meta") for path in EDITOR_SOURCES),
    }
    expected_gameplay = {
        *GAMEPLAY_SOURCES,
        *(Path(str(path) + ".meta") for path in GAMEPLAY_SOURCES),
    }
    editor_dir = root / "Assets/_Project/Scripts/Editor"
    gameplay_dir = root / "Assets/_Project/Scripts/Gameplay"
    actual_editor = {
        path.relative_to(root)
        for path in editor_dir.glob("ChannelPlayKhufuV13*")
        if path.is_file()
    }
    actual_gameplay = {
        path.relative_to(root)
        for path in gameplay_dir.glob("KhufuV13*")
        if path.is_file()
    }
    if actual_editor != expected_editor:
        result.errors.append("V13 editor source/meta inventory drifted")
    if actual_gameplay != expected_gameplay:
        result.errors.append("V13 gameplay source/meta inventory drifted")
    if exact_files(root, GENERATED_ROOT) != {*GENERATED_ASSETS, *GENERATED_METAS}:
        result.errors.append("V13 generated asset/meta inventory drifted")
    if exact_files(root, MATERIAL_ROOT) != {*MATERIAL_FILES, *MATERIAL_METAS}:
        result.errors.append("V13 material/meta inventory drifted")

    guid_paths = (*UNITY_SCRIPT_METAS, *GENERATED_METAS, *MATERIAL_METAS, *ROOT_METAS)
    guids: list[str] = []
    for relative in guid_paths:
        text = (root / relative).read_text(encoding="utf-8", errors="replace")
        matches = re.findall(r"(?m)^guid:\s*([0-9a-f]{32})\s*$", text)
        if len(matches) != 1:
            result.errors.append(f"Unity metadata GUID invalid: {relative.as_posix()}")
        else:
            guids.append(matches[0])
    if len(guids) != len(set(guids)):
        result.errors.append("V13 Unity metadata GUIDs are not unique")


def check_scene_guid_references(root: Path, result: ValidationResult) -> None:
    scene = (root / SCENE).read_text(encoding="utf-8", errors="replace")
    for relative in (*GENERATED_METAS, *MATERIAL_METAS, *SERIALIZED_SCRIPT_METAS):
        text = (root / relative).read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^guid:\s*([0-9a-f]{32})\s*$", text)
        if match is not None and match.group(1) not in scene:
            result.errors.append(
                f"scene does not reference V13 Unity object: {relative.as_posix()}"
            )


def check_forbidden_terms(root: Path, result: ValidationResult) -> None:
    paths = (*UNITY_SOURCES, *GENERATED_ASSETS, *MATERIAL_FILES)
    for relative in paths:
        content = (root / relative).read_bytes().lower()
        for term in FORBIDDEN_IMPLEMENTATION_TERMS:
            if term.lower().encode("utf-8") in content:
                result.errors.append(
                    f"forbidden V13 scope term found in {relative.as_posix()}: {term}"
                )


def check_prewrite(root: Path, result: ValidationResult) -> None:
    audit = (root / RUN_ROOT / "prewrite-audit.md").read_text(encoding="utf-8")
    prewrite = (root / RUN_ROOT / "prewrite-validation.md").read_text(
        encoding="utf-8"
    )
    for text, label in ((audit, "prewrite audit"), (prewrite, "prewrite gate")):
        for token in (
            BASELINE_SCENE_SHA256,
            V12_STATIC_SIGNATURE,
            "renderers=5_vertices=1176_triangles=588_colliders=22",
            "renderers=834_vertices=67070_triangles=48560_colliders=589",
        ):
            require_text(text, token, label, result)
    for token in ("Exact V4 ownership targets: `13/13`", "Exact preserved observations: `7/7`"):
        require_text(audit, token, "prewrite audit", result)


def check_static_idempotence_negative(
    root: Path, scene_hash: str, generated_hash: str, result: ValidationResult
) -> str:
    static = (root / RUN_ROOT / "static-validation.md").read_text(encoding="utf-8")
    signature = extract_single(
        static,
        r"^- V13 signature: `([0-9a-f]{64})`\r?$",
        "static V13 signature",
        result,
    )
    for token in (
        f"V12 restored-context signature: `{V12_STATIC_SIGNATURE}`",
        "Root metrics: `renderers=5_vertices=792_triangles=396_colliders=20`",
        "Map metrics: `renderers=839_vertices=67862_triangles=48956_colliders=609`",
    ):
        require_text(static, token, "static validation", result)

    idempotence = (root / RUN_ROOT / "idempotence.md").read_text(encoding="utf-8")
    for token in (
        f"First / second signature: `{signature} / {signature}`",
        f"First / second scene SHA256: `{scene_hash} / {scene_hash}`",
        f"First / second generated signature: `{generated_hash} / {generated_hash}`",
    ):
        require_text(idempotence, token, "idempotence receipt", result)

    negative = (root / RUN_ROOT / "negative-controls.md").read_text(encoding="utf-8")
    for token in (
        "V4 renderer restored: `rejected`",
        "V4 target deactivated: `rejected`",
        "Structural pair drift: `rejected`",
        "Chamber ceiling proxy disabled: `rejected`",
        "Pit backing disabled: `rejected`",
        "V10-owned marker moved: `rejected`",
        "Inherited light disabled: `rejected`",
        "Junction inner wall trim reverted: `rejected`",
        "V10 branch bypass floor proxy restored: `rejected`",
        "Injected successor failure -> rollback verified: `rejected`",
        f"Rollback scene SHA256: `{scene_hash}`",
        f"Rollback generated signature: `{generated_hash}`",
    ):
        require_text(negative, token, "negative-control receipt", result)
    return signature


def check_legacy(
    root: Path, scene_hash: str, static_signature: str, result: ValidationResult
) -> None:
    legacy = (root / RUN_ROOT / "legacy-regression.md").read_text(encoding="utf-8")
    for label in ("V4", "V5", "V8", "V9", "V10", "V11", "V12"):
        require_text(legacy, f"- {label}: `passed`", "legacy regression", result)
    for token in (
        f"V13 canonical return: `passed` / signature `{static_signature}`",
        f"Scene SHA256 before / after: `{scene_hash} / {scene_hash}`",
        "Scene bytes unchanged: `True`",
        f"V11: `passed` / signature `{V11_RESTORED_SIGNATURE}`",
        f"V12: `passed` / signature `{V12_STATIC_SIGNATURE}`",
        "classified exact V12 transition deltas=19",
    ):
        require_text(legacy, token, "legacy regression", result)
    if legacy.count("Classified exact V12 transition delta:") != 19:
        result.errors.append("legacy receipt does not contain exactly 19 V10 deltas")
    for relative in (*LEGACY_SOURCES, BUILDER, LEGACY):
        require_hash(legacy, root, relative, "legacy regression receipt", result)


def check_captures(root: Path, scene_hash: str, result: ValidationResult) -> None:
    manifest_path = RUN_ROOT / "captures/manifest.md"
    review_path = RUN_ROOT / "captures/manual-semantic-review.md"
    manifest = (root / manifest_path).read_text(encoding="utf-8")
    review = (root / review_path).read_text(encoding="utf-8")
    for token in (
        "Resolution: `1600x1000`",
        "Required captures: `6`",
        "Inherited `V4_Light_Subterranean`: `enabled and disclosed`",
        f"Scene SHA256: `{scene_hash}`",
    ):
        require_text(manifest, token, "capture manifest", result)
    for relative in CAPTURE_BOUND_SOURCES:
        require_hash(manifest, root, relative, "capture manifest", result)
    require_hash(
        manifest,
        root,
        RUN_ROOT / "static-validation.md",
        "capture manifest",
        result,
    )
    image_hashes: list[str] = []
    for relative in CAPTURE_IMAGES:
        path = root / relative
        try:
            dimensions = png_dimensions(path)
        except ValueError as error:
            result.errors.append(f"{relative.as_posix()}: {error}")
            continue
        if dimensions != (1600, 1000):
            result.errors.append(
                f"PNG dimensions drifted: {relative.as_posix()} {dimensions}"
            )
        if path.stat().st_size < 60000:
            result.errors.append(f"PNG is too small: {relative.as_posix()}")
        digest = sha256(path)
        stem = relative.stem
        require_text(manifest, f"## {stem}", "capture manifest", result)
        if digest not in manifest:
            result.errors.append(
                f"capture manifest is not bound to current {relative.as_posix()}"
            )
        if relative.name not in review or digest not in review:
            result.errors.append(
                f"semantic review is not bound to current {relative.as_posix()}"
            )
        image_hashes.append(digest)
    if len(image_hashes) != len(set(image_hashes)):
        result.errors.append("required capture evidence contains duplicate PNG bytes")


def check_build(
    root: Path, scene_hash: str, generated_hash: str, result: ValidationResult
) -> None:
    build = (root / RUN_ROOT / "windows-build.md").read_text(encoding="utf-8")
    for token in (
        "Build target: `StandaloneWindows64` Development Player",
        "Output: `Builds/KhufuV13/ChannelPlayKhufuV13.exe`",
        f"Scene source SHA256: `{scene_hash}`",
        (
            "Protected V13 generated/material signature before/after: "
            f"`{generated_hash} / {generated_hash}`"
        ),
    ):
        require_text(build, token, "Windows build receipt", result)
    if not re.search(r"(?m)^- Errors / warnings: `0 / \d+`\r?$", build):
        result.errors.append("Windows build receipt does not prove zero errors")
    for relative in (PLAYER, UNITY_PLAYER, BUILT_LEVEL, ASSEMBLY, *BUILD_BOUND_SOURCES):
        require_hash(build, root, relative, "Windows build receipt", result)


def parse_float_field(
    text: str, pattern: str, label: str, result: ValidationResult
) -> tuple[float, ...]:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        result.errors.append(f"{label} is missing")
        return ()
    try:
        return tuple(float(value) for value in match.groups())
    except ValueError:
        result.errors.append(f"{label} is invalid")
        return ()


def check_trace(
    root: Path,
    receipt: str,
    expected_path: Path,
    label: str,
    result: ValidationResult,
) -> None:
    match = re.search(
        r"(?m)^- Movement trace: `([^`]+)` / records `(\d+)` / "
        r"SHA256 `([0-9a-f]{64})`\r?$",
        receipt,
    )
    if match is None:
        result.errors.append(f"{label} movement trace binding is missing")
        return
    path, records, digest = match.groups()
    if path != expected_path.as_posix():
        result.errors.append(f"{label} movement trace path drifted")
    lines = (root / expected_path).read_text(encoding="utf-8-sig").splitlines()
    if not lines or not lines[0].startswith("segment,step,move_frame,"):
        result.errors.append(f"{label} movement trace header is invalid")
    if int(records) != max(0, len(lines) - 1):
        result.errors.append(f"{label} movement trace record count drifted")
    if digest != sha256(root / expected_path):
        result.errors.append(f"{label} movement trace hash drifted")


def check_traversal(root: Path, result: ValidationResult) -> None:
    normal = (root / PLAYER_ARTIFACTS[0]).read_text(encoding="utf-8")
    boundary = (root / PLAYER_ARTIFACTS[1]).read_text(encoding="utf-8")
    assembly_hash = sha256(root / ASSEMBLY)
    for receipt, label in ((normal, "normal"), (boundary, "boundary")):
        require_text(
            receipt,
            f"Assembly-CSharp SHA256: `{assembly_hash}`",
            f"{label} player receipt",
            result,
        )
    for token in (
        "Mode: `normal-round-trip`",
        "V10 branch -> landing -> door -> chamber/pit -> return: `passed`",
        "Reached route anchors: `11/11`",
        "Serialized anchors match: `True`",
        "Root renderers / enabled colliders: `5 / 20`",
        "Pit overlap / cast solid backing: `True / True`",
    ):
        require_text(normal, token, "normal player receipt", result)
    distances = parse_float_field(
        normal,
        r"(?m)^- Traversed distance / max error / final error: "
        r"`([0-9.]+) / ([0-9.]+) / ([0-9.]+)`\r?$",
        "normal traversal error metrics",
        result,
    )
    if distances and (distances[1] > 0.40 or distances[2] > 0.40):
        result.errors.append("normal traversal anchor error exceeds 0.40 m")
    grounded = parse_float_field(
        normal,
        r"(?m)^- Grounded steps/fraction: `\d+/\d+ / ([0-9.]+)`\r?$",
        "normal grounded fraction",
        result,
    )
    if grounded and grounded[0] < 0.90:
        result.errors.append("normal grounded fraction is below 0.90")

    for token in (
        "Mode: `outside-wall-control`",
        "Outside-wall control: `passed`",
        "Control pre-Move overlap empty: `True`",
        "Control blocked collider / flags: `V13_Proxy_Chamber_East_Wall / Sides`",
        "Control callback: `OnControllerColliderHit` / exact `True`",
    ):
        require_text(boundary, token, "boundary player receipt", result)
    start = parse_float_field(
        boundary,
        r"(?m)^- Control boundary start distance: `([0-9.]+) m`\r?$",
        "boundary start distance",
        result,
    )
    if start and start[0] < 1.50:
        result.errors.append("boundary start distance is below 1.50 m")
    step = parse_float_field(
        boundary,
        r"(?m)^- Control maximum requested step: `([0-9.]+) m`\r?$",
        "boundary maximum requested step",
        result,
    )
    if step and step[0] > 0.10:
        result.errors.append("boundary requested step exceeds 0.10 m")
    callback = re.search(
        r"(?m)^- Control Move / callback frame: `(\d+) / (\d+)`\r?$", boundary
    )
    if (
        callback is None
        or callback.group(1) != callback.group(2)
        or int(callback.group(1)) < 0
    ):
        result.errors.append("boundary receipt lacks same-frame controller callback proof")
    check_trace(root, normal, PLAYER_ARTIFACTS[2], "normal", result)
    check_trace(root, boundary, PLAYER_ARTIFACTS[3], "boundary", result)


def check_clean_index(
    root: Path, static_signature: str, result: ValidationResult
) -> None:
    clean = (root / RUN_ROOT / "clean-index-import.md").read_text(encoding="utf-8")
    for token in (static_signature, "Compiler errors: `0`"):
        require_text(clean, token, "clean-index receipt", result)
    for relative in CLEAN_BOUND_SOURCES:
        require_hash(clean, root, relative, "clean-index receipt", result)


def validate(
    root: Path, require_reviews: bool, check_index: bool, postcommit: bool
) -> ValidationResult:
    result = ValidationResult()
    required = {
        PLAYER,
        UNITY_PLAYER,
        BUILT_LEVEL,
        ASSEMBLY,
        SCENE,
        GIT_ATTRIBUTES,
        *EDITOR_SOURCES,
        *GAMEPLAY_SOURCES,
        *UNITY_SCRIPT_METAS,
        *PYTHON_SOURCES,
        *LEGACY_SOURCES,
        *DOC_FILES,
        *GENERATED_ASSETS,
        *GENERATED_METAS,
        *MATERIAL_FILES,
        *MATERIAL_METAS,
        *ROOT_METAS,
        *CAPTURE_IMAGES,
        *PLAYER_ARTIFACTS,
        *PHASE_RECEIPTS,
        *REQUIRED_TOKENS,
        *EXTRA_REQUIRED_TOKENS,
        RUN_ROOT / "prewrite-audit.json",
    }
    if require_reviews:
        required.update(
            {
                FABLE_PROMPT,
                FABLE_FINAL,
                FABLE_META,
                FABLE_RESOLUTION,
                RUN_ROOT / "review-resolution.md",
            }
        )
    if check_index or postcommit:
        required.add(STAGED_INVENTORY)
    if check_index:
        required.add(STAGED_REPORT)
    for relative in sorted(required, key=lambda item: item.as_posix()):
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            result.errors.append(
                f"required release file missing or empty: {relative.as_posix()}"
            )
    if result.errors:
        return result

    check_baseline_ancestry(root, result)
    check_allowlist_contract(root, result)
    check_source_and_asset_inventory(root, result)
    check_scene_guid_references(root, result)
    check_forbidden_terms(root, result)
    for relative, token in (*REQUIRED_TOKENS.items(), *EXTRA_REQUIRED_TOKENS.items()):
        text = (root / relative).read_text(encoding="utf-8", errors="replace")
        require_exact_token(text, token, relative.as_posix(), result)

    scene_hash = sha256(root / SCENE)
    generated_hash = generated_asset_signature(root)
    check_prewrite(root, result)
    static_signature = check_static_idempotence_negative(
        root, scene_hash, generated_hash, result
    )
    check_legacy(root, scene_hash, static_signature, result)
    check_captures(root, scene_hash, result)
    check_build(root, scene_hash, generated_hash, result)
    check_traversal(root, result)
    check_clean_index(root, static_signature, result)

    rules = (root / DOC_ROOT / "RULES.md").read_text(encoding="utf-8")
    for token in (BASELINE_COMMIT, BASELINE_SCENE_SHA256, V12_STATIC_SIGNATURE):
        require_text(rules, token, "RULES.md", result)

    if require_reviews:
        if fable_verdict((root / FABLE_FINAL).read_text(encoding="utf-8")) != "ship":
            result.errors.append("external Fable final verdict is not ship")
        resolution = (root / RUN_ROOT / "review-resolution.md").read_text(
            encoding="utf-8"
        )
        require_exact_token(
            resolution,
            "KHUFU_V13_REVIEW_RESOLUTION: passed",
            "review resolution",
            result,
        )
        for relative in (
            FABLE_PROMPT,
            FABLE_FINAL,
            FABLE_META,
            FABLE_RESOLUTION,
        ):
            require_hash(resolution, root, relative, "review resolution", result)

    if check_index:
        check_staged(root, result)
    if postcommit:
        check_postcommit(root, result)
    result.facts.update(
        {
            "assembly_sha256": sha256(root / ASSEMBLY),
            "capture_pngs": len(CAPTURE_IMAGES),
            "generated_signature": generated_hash,
            "required_files": len(required),
            "scene_sha256": scene_hash,
            "static_signature": static_signature,
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
        "# Khufu V13 Release Validation",
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
        [
            "",
            f"KHUFU_V13_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}",
            "",
        ]
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
    print(f"KHUFU_V13_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
