from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


RUN_ROOT = Path("runs/khufu-v11-royal-circuit")
DOC_ROOT = Path("docs/khufu-v11-royal-circuit")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
BUILD_ROOT = Path("Builds/KhufuV11")
PLAYER = BUILD_ROOT / "ChannelPlayKhufuV11.exe"
BUILT_LEVEL = BUILD_ROOT / "ChannelPlayKhufuV11_Data/level0"
ASSEMBLY = BUILD_ROOT / "ChannelPlayKhufuV11_Data/Managed/Assembly-CSharp.dll"
ALLOWLIST = DOC_ROOT / "staging-allowlist.txt"
STAGED_INVENTORY = RUN_ROOT / "staged-inventory.json"
STAGED_REPORT = RUN_ROOT / "staged-index-validation.md"
POSTCOMMIT_REPORT = RUN_ROOT / "post-commit-validation.md"
FABLE_FINAL = Path("work/fable-harness/khufu-v11-release-final-review.opus.followup.md")

SOURCE_FILES = [
    SCENE,
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitBuilder.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitMeshPipeline.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitScreenshotExporter.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11LegacyRegression.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11WindowsBuild.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV11RoyalRouteContract.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV11SegmentTag.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV11TraversalProofProbe.cs"),
    Path("tools/validate_khufu_v11_prewrite.py"),
    Path("tools/validate_khufu_v11_release.py"),
    Path("tools/tests/test_validate_khufu_v11_prewrite.py"),
    Path("tools/tests/test_validate_khufu_v11_release.py"),
]

MATERIAL_METAS = [
    Path("Assets/_Project/Materials/KhufuV11RoyalCircuit") / name
    for name in (
        "V11_Royal_Amber.mat.meta",
        "V11_Royal_Deep_Shadow.mat.meta",
        "V11_Royal_Limestone.mat.meta",
        "V11_Royal_Red_Granite.mat.meta",
        "V11_Stacked_Display.mat.meta",
    )
]

CAPTURE_IMAGES = [
    RUN_ROOT / "captures" / name
    for name in (
        "great_step_open_axis.png",
        "antechamber_portcullis_detail.png",
        "kings_chamber_wide.png",
        "sarcophagus_and_shaft_boundary.png",
        "relieving_stack_cutaway.png",
        "pyramid_royal_circuit_integration.png",
    )
]

PLAYER_ARTIFACTS = [
    RUN_ROOT / "player-proof/v11-final-round-trip.md",
    RUN_ROOT / "player-proof/v11-final-boundary-control.md",
    RUN_ROOT / "player-proof/v11-final-normal-round-trip-movement-trace.csv",
    RUN_ROOT / "player-proof/v11-final-great-step-boundary-control-movement-trace.csv",
]

REQUIRED_TOKENS = {
    RUN_ROOT / "prewrite-validation.md": "KHUFU_V11_PREWRITE: passed",
    RUN_ROOT / "validation.md": "KHUFU_V11_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "KHUFU_V11_IDEMPOTENCE: passed",
    RUN_ROOT / "negative-controls.md": "KHUFU_V11_NEGATIVE_CONTROLS: passed",
    RUN_ROOT / "captures/manifest.md": "KHUFU_V11_REQUIRED_CAPTURES: passed",
    RUN_ROOT / "legacy-regression.md": "V11_LEGACY_REGRESSION: passed",
    RUN_ROOT / "python-tests.md": "V11_PYTHON_TESTS: passed",
    RUN_ROOT / "manual-qa.md": "V11_MANUAL_QA: passed",
    RUN_ROOT / "clean-package-import.md": "V11_CLEAN_PACKAGE_IMPORT: passed",
    RUN_ROOT / "windows-build.md": "V11_WINDOWS_BUILD: passed",
    PLAYER_ARTIFACTS[0]: "V11_WINDOWS_PLAYER_TRAVERSAL: passed",
    PLAYER_ARTIFACTS[1]: "V11_WINDOWS_PLAYER_BOUNDARY_CONTROL: passed",
}

STRICT_PREFIXES = (
    "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit",
    "Assets/_Project/Materials/KhufuV11RoyalCircuit",
    "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11",
    "Assets/_Project/Scripts/Gameplay/KhufuV11",
    "docs/khufu-v11-royal-circuit/",
    "tools/validate_khufu_v11",
    "tools/tests/test_validate_khufu_v11",
    "work/fable-harness/khufu-v11",
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


def read_allowlist(root: Path) -> set[str]:
    lines = (root / ALLOWLIST).read_text(encoding="utf-8").splitlines()
    normalized = (line.strip() for line in lines)
    return {line.replace("\\", "/") for line in normalized if line and not line.startswith("#")}


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
    paths = parse_status_paths(process.stdout)
    return paths


def write_staged_inventory(root: Path) -> None:
    staged = git_paths(root, "diff", "--cached", "--name-only", "-z")
    helpers = {STAGED_INVENTORY.as_posix(), STAGED_REPORT.as_posix()}
    payload = {
        "schema": "khufu-v11-staged-inventory-v1",
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
        result.errors.append("staged inventory is invalid JSON")
        return []
    if payload.get("schema") != "khufu-v11-staged-inventory-v1":
        result.errors.append("staged inventory schema is invalid")
    records = payload.get("files", [])
    if not isinstance(records, list):
        result.errors.append("staged inventory files are invalid")
        return []
    return records


def check_index_record(root: Path, record: dict, label: str, result: ValidationResult) -> None:
    path = str(record.get("path", ""))
    content = index_bytes(root, path)
    if content is None:
        result.errors.append(f"{label} missing staged blob: {path}")
    elif record.get("bytes") != len(content) or record.get("sha256") != sha256_bytes(content):
        result.errors.append(f"{label} staged hash or size drifted: {path}")


def check_staged(root: Path, result: ValidationResult) -> None:
    allowlist = read_allowlist(root)
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
        if path.startswith(STRICT_PREFIXES):
            result.errors.append(f"unlisted V11 scope path: {path}")
    unstaged = git_paths(root, "diff", "--name-only", "-z")
    for path in sorted(staged.intersection(unstaged)):
        result.errors.append(f"staged path has an additional unstaged delta: {path}")
    records = read_staged_inventory(root, result)
    inventory_paths = {str(record.get("path", "")) for record in records}
    if inventory_paths != staged - helpers:
        result.errors.append("staged inventory path set differs from the exact release inventory")
    for record in records:
        check_index_record(root, record, "staged inventory", result)
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
        result.errors.append(f"post-commit inventory path is outside V11 allowlist: {path}")
    if git_paths(root, "diff", "--cached", "--name-only", "-z"):
        result.errors.append("staged index is not empty after commit")
    for path in sorted(status_paths(root).intersection(expected)):
        result.errors.append(f"post-commit release path has worktree drift: {path}")
    result.facts["committed_files"] = len(committed)


def require_hash(text: str, root: Path, relative: Path, label: str, result: ValidationResult) -> None:
    if sha256(root / relative) not in text:
        result.errors.append(f"{label} is not bound to current {relative.as_posix()}")


def check_material_references(root: Path, result: ValidationResult) -> None:
    scene_text = (root / SCENE).read_text(encoding="utf-8")
    for relative in MATERIAL_METAS:
        text = (root / relative).read_text(encoding="utf-8")
        match = re.search(r"^guid:\s*([0-9a-f]{32})\s*$", text, re.MULTILINE)
        if match is None:
            result.errors.append(f"material metadata GUID missing: {relative.as_posix()}")
        elif match.group(1) not in scene_text:
            result.errors.append(f"scene does not reference V11 material: {relative.as_posix()}")


def validate(root: Path, require_reviews: bool, check_index: bool, postcommit: bool) -> ValidationResult:
    result = ValidationResult()
    required = [
        PLAYER,
        BUILT_LEVEL,
        ASSEMBLY,
        *SOURCE_FILES,
        *MATERIAL_METAS,
        *CAPTURE_IMAGES,
        *PLAYER_ARTIFACTS,
        *REQUIRED_TOKENS,
    ]
    if require_reviews:
        required.extend((FABLE_FINAL, RUN_ROOT / "review-resolution.md"))
    for relative in sorted(set(required)):
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            result.errors.append(f"required release file missing or empty: {relative.as_posix()}")
    if result.errors:
        return result

    check_material_references(root, result)
    for relative, token in REQUIRED_TOKENS.items():
        if token not in (root / relative).read_text(encoding="utf-8", errors="replace"):
            result.errors.append(f"required pass token missing: {relative.as_posix()} -> {token}")

    validation = (root / RUN_ROOT / "validation.md").read_text(encoding="utf-8")
    if "renderers=5_" not in validation:
        result.errors.append("V11 renderer budget is not recorded at the exact 5/5 ceiling")

    capture_manifest = (root / RUN_ROOT / "captures/manifest.md").read_text(encoding="utf-8")
    for relative in SOURCE_FILES[:5]:
        require_hash(capture_manifest, root, relative, "capture manifest", result)
    image_hashes: list[str] = []
    for relative in CAPTURE_IMAGES:
        path = root / relative
        try:
            observed = png_dimensions(path)
        except ValueError as error:
            result.errors.append(f"{relative.as_posix()}: {error}")
            continue
        if observed != (1600, 1000):
            result.errors.append(f"PNG dimensions drifted: {relative.as_posix()} {observed}")
        if path.stat().st_size < 65536:
            result.errors.append(f"PNG is too small: {relative.as_posix()}")
        image_hashes.append(sha256(path))
    if len(image_hashes) != len(set(image_hashes)):
        result.errors.append("required capture evidence contains duplicate PNG bytes")

    build = (root / RUN_ROOT / "windows-build.md").read_text(encoding="utf-8")
    for relative in (PLAYER, BUILT_LEVEL, ASSEMBLY, *SOURCE_FILES[:10]):
        require_hash(build, root, relative, "Windows build receipt", result)

    normal = (root / PLAYER_ARTIFACTS[0]).read_text(encoding="utf-8")
    boundary = (root / PLAYER_ARTIFACTS[1]).read_text(encoding="utf-8")
    assembly_hash = sha256(root / ASSEMBLY)
    if assembly_hash not in normal or assembly_hash not in boundary:
        result.errors.append("player traversal receipts are not bound to the current managed assembly")
    if "Reached route anchors: `15/15`" not in normal or "Grounded steps:" not in normal:
        result.errors.append("normal player receipt omits complete 15-anchor grounded round trip")
    blocker = "V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary"
    if blocker not in boundary or "Sides" not in boundary:
        result.errors.append("boundary control does not prove the named Great Step side collision")
    controller_metrics = "CharacterController radius / height / stepOffset / skinWidth: `0.450 / 2.000 / 0.300 / 0.050`"
    if controller_metrics not in normal or controller_metrics not in boundary:
        result.errors.append("player receipts omit the expected real CharacterController metrics")

    if require_reviews:
        if fable_verdict((root / FABLE_FINAL).read_text(encoding="utf-8")) != "ship":
            result.errors.append("external Fable final verdict is not ship")
        resolution = (root / RUN_ROOT / "review-resolution.md").read_text(encoding="utf-8")
        if "V11_REVIEW_RESOLUTION: passed" not in resolution:
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
        "# Khufu V11 Release Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Reviews required: `{require_reviews}`",
        f"- Staged index checked: `{check_index}`",
        f"- Post-commit checked: `{postcommit}`",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(result.facts.items()))
    lines.extend(f"- Failure: `{error}`" for error in result.errors)
    lines.extend(["", f"V11_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


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
    result = validate(root, args.require_reviews, args.check_staged, args.postcommit)
    if args.check_staged and output.resolve() != (root / STAGED_REPORT).resolve():
        result.errors.append(f"staged validation output must be {STAGED_REPORT.as_posix()}")
    if args.postcommit and output.resolve() != (root / POSTCOMMIT_REPORT).resolve():
        result.errors.append(f"post-commit validation output must be {POSTCOMMIT_REPORT.as_posix()}")
    write_report(output, result, args.require_reviews, args.check_staged, args.postcommit)
    print(f"V11_RELEASE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
