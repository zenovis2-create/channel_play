from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


RUN_ROOT = Path("runs/khufu-v9-causeway-fidelity")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
PLAYER = Path("Builds/KhufuV9/ChannelPlayKhufuV9.exe")
BUILT_LEVEL = Path("Builds/KhufuV9/ChannelPlayKhufuV9_Data/level0")
MANAGED_ASSEMBLY = Path("Builds/KhufuV9/ChannelPlayKhufuV9_Data/Managed/Assembly-CSharp.dll")
BUILD_ROOT = Path("Builds/KhufuV9")
EDITOR_BINDING = RUN_ROOT / "editor-binding.json"
PLAYER_BINDING = RUN_ROOT / "player-proof/binding.json"
PERFORMANCE_BINDING = RUN_ROOT / "performance-final/binding.json"
FABLE_REVIEW = RUN_ROOT / "local-fable-final.md"
SCENE_BASELINE_REVISION = "c63e0ec6"
SCENE_BASELINE_SHA256 = "4f15673e1de7eeb9f92dbfa058c40ae263549449c9ee2c5b98b59c7161a5d32f"
V9_ROOT_NAME = "Runtime_Khufu_V9_Causeway_Fidelity"
MAP_ROOT_NAME = "TraitorEscape_Runtime_Map"

EXPECTED_DISABLED_RENDERERS = {
    "V5_Valley_Gate_Floor",
    "V5_Valley_Gate_Lintel",
    "V5_Valley_Gate_Pylon_-1",
    "V5_Valley_Gate_Pylon_1",
    "V5_Covered_Causeway_Floor",
    "V5_Covered_Causeway_Lintel",
    "V5_Covered_Causeway_Pylon_-1",
    "V5_Covered_Causeway_Pylon_1",
    *{
        f"V5_Route_Segment_{segment:02d}_{part}"
        for segment in (0, 1, 23, 24)
        for part in ("Floor", "East_Wall", "West_Wall")
    },
}

V9_SOURCES = [
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayAudit.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayMeshPipeline.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityBuilder.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityValidator.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayScreenshotExporter.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9PlayModeRegressionRunner.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9WindowsBuild.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV9CausewayProofProbe.cs"),
]

GENERATED_MESHES = [
    Path(f"Assets/_Project/Art/Generated/KhufuV9CausewayFidelity/KhufuV9_{name}.asset")
    for name in (
        "Basalt_Floor",
        "Limestone_Structure",
        "Red_Granite_Rhythm",
        "Tura_Trim",
        "Route_Inlay",
    )
]

V9_ASSET_META = [
    *[Path(f"{path.as_posix()}.meta") for path in V9_SOURCES],
    Path("Assets/_Project/Art/Generated/KhufuV9CausewayFidelity.meta"),
    *[Path(f"{path.as_posix()}.meta") for path in GENERATED_MESHES],
]

DOC_FILES = [
    Path(f"docs/khufu-v9-causeway-fidelity/{name}")
    for name in (
        "README.md",
        "GOAL.md",
        "PLAN.md",
        "STATUS.md",
        "RULES.md",
        "TEST_PLAN.md",
        "LOOP.md",
        "RESEARCH_BRIEF.md",
    )
]

CAPTURE_ARTIFACTS = [
    RUN_ROOT / "captures/manifest.md",
    RUN_ROOT / "captures/valley_gate_procession.png",
    RUN_ROOT / "captures/causeway_long_axis.png",
    RUN_ROOT / "captures/covered_causeway_rhythm.png",
    RUN_ROOT / "captures/hub_open_fanout.png",
    RUN_ROOT / "captures/processional_oblique.png",
    RUN_ROOT / "captures/mutation_superseded_overlap.png",
]

EDITOR_ARTIFACTS = [
    RUN_ROOT / "audit.json",
    RUN_ROOT / "audit.md",
    RUN_ROOT / "audit-unity.log",
    RUN_ROOT / "validation.md",
    RUN_ROOT / "idempotence.md",
    RUN_ROOT / "pair-mutation.md",
    RUN_ROOT / "graybox-mutation.md",
    RUN_ROOT / "v5-playmode-regression.md",
    RUN_ROOT / "static-fable-hardening-final.log",
    RUN_ROOT / "v5-gate4-fable-hardening-final.log",
    RUN_ROOT / "v5-playmode-fable-hardening-final.log",
    RUN_ROOT / "capture-fable-hardening-final.log",
    RUN_ROOT / "python-tests.md",
    RUN_ROOT / "manual-qa.md",
    RUN_ROOT / "debugging-audit.md",
    RUN_ROOT / "external-fable-final-review.md",
    RUN_ROOT / "review-work.md",
    *CAPTURE_ARTIFACTS,
]

PLAYER_ARTIFACTS = [
    RUN_ROOT / "windows-build-final.log",
    RUN_ROOT / "windows-build.md",
    RUN_ROOT / "player-proof/normal-player-final.log",
    RUN_ROOT / "player-proof/mutation-player-final.log",
    RUN_ROOT / "player-proof/error-metric-player-final.log",
    RUN_ROOT / "player-proof/v9-final-causeway-traversal.md",
    RUN_ROOT / "player-proof/v9-final-proxy-mutation.md",
    RUN_ROOT / "player-proof/v9-final-error-metric-mutation.md",
    RUN_ROOT / "player-proof/v9-final-normal-valley_gate_start.png",
    RUN_ROOT / "player-proof/v9-final-normal-covered_causeway_midpoint.png",
    RUN_ROOT / "player-proof/v9-final-normal-v8_hub_arrival.png",
    RUN_ROOT / "player-proof/v9-final-mutation-valley_gate_start.png",
    RUN_ROOT / "player-proof/v9-final-mutation-mutation_blocked.png",
]

PERFORMANCE_ARTIFACTS = [
    Path("docs/khufu-v9-causeway-fidelity/performance-budget.json"),
    RUN_ROOT / "performance-final/validation.md",
    RUN_ROOT / "performance-final/v9-final-performance.md",
    RUN_ROOT / "performance-final/v9-final.raw",
    RUN_ROOT / "performance-final/player-final.log",
    RUN_ROOT / "performance-final/v9-final-windows-player-initial.png",
    RUN_ROOT / "performance-final/v9-final-windows-player-operator.png",
]

REQUIRED_FILES = [
    SCENE,
    *V9_SOURCES,
    *GENERATED_MESHES,
    *V9_ASSET_META,
    *DOC_FILES,
    *EDITOR_ARTIFACTS,
    *PLAYER_ARTIFACTS,
    *PERFORMANCE_ARTIFACTS,
    EDITOR_BINDING,
    PLAYER_BINDING,
    PERFORMANCE_BINDING,
]

REQUIRED_TOKENS = {
    RUN_ROOT / "audit.md": "KHUFU_V9_AUDIT: passed",
    RUN_ROOT / "validation.md": "V9_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "V9_IDEMPOTENCE: passed",
    RUN_ROOT / "pair-mutation.md": "V9_PAIR_MUTATION: passed",
    RUN_ROOT / "graybox-mutation.md": "V9_GRAYBOX_MUTATION: passed",
    RUN_ROOT / "v5-playmode-regression.md": "V9_V5_PLAYMODE_REGRESSION: passed",
    RUN_ROOT / "windows-build.md": "V9_WINDOWS_BUILD: passed",
    RUN_ROOT / "captures/manifest.md": "V9_GRAYBOX_MUTATION_CAPTURE: passed",
    RUN_ROOT / "player-proof/v9-final-causeway-traversal.md": "V9_WINDOWS_PLAYER_CAUSEWAY_TRAVERSAL: passed",
    RUN_ROOT / "player-proof/v9-final-proxy-mutation.md": "V9_WINDOWS_PLAYER_PROXY_MUTATION: passed",
    RUN_ROOT / "player-proof/v9-final-error-metric-mutation.md": "V9_WINDOWS_PLAYER_ERROR_METRIC_MUTATION: passed",
    RUN_ROOT / "performance-final/validation.md": "PERFORMANCE_VERDICT: passed",
    RUN_ROOT / "python-tests.md": "V9_PYTHON_TESTS: passed",
    RUN_ROOT / "manual-qa.md": "V9_MANUAL_QA: passed",
    RUN_ROOT / "debugging-audit.md": "V9_DEBUGGING_AUDIT: passed",
    RUN_ROOT / "external-fable-final-review.md": "EXTERNAL_FABLE_REVIEW: addressed",
    RUN_ROOT / "review-work.md": "V9_REVIEW_WORK: passed",
}

PNG_FILES = [
    path
    for path in REQUIRED_FILES
    if path.suffix.lower() == ".png"
]


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    facts: dict[str, str | int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class SceneDocument:
    class_id: int
    file_id: int
    body: str


@dataclass(frozen=True)
class PngMetrics:
    width: int
    height: int
    standard_deviation: float
    value_range: float
    unique_sampled_colors: int


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG")
    return struct.unpack(">II", header[16:24])


def png_semantic_metrics(path: Path) -> PngMetrics:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    offset = 8
    width = height = bit_depth = color_type = interlace = 0
    compressed = bytearray()
    saw_header = False
    saw_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if chunk_end > len(data):
            raise ValueError("truncated PNG payload")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(payload, zlib.crc32(chunk_type)) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("PNG CRC mismatch")
        if chunk_type == b"IHDR":
            if saw_header or length != 13:
                raise ValueError("invalid PNG IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if compression != 0 or filtering != 0:
                raise ValueError("unsupported PNG compression/filter method")
            saw_header = True
        elif chunk_type == b"IDAT":
            compressed.extend(payload)
        elif chunk_type == b"IEND":
            if length != 0:
                raise ValueError("invalid PNG IEND")
            saw_end = True
            offset = chunk_end
            break
        offset = chunk_end
    if not saw_header or not saw_end or offset != len(data):
        raise ValueError("incomplete or padded PNG")
    if width <= 0 or height <= 0 or bit_depth != 8 or color_type not in (2, 6) or interlace != 0:
        raise ValueError("unsupported PNG pixel format")

    bytes_per_pixel = 3 if color_type == 2 else 4
    stride = width * bytes_per_pixel
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as error:
        raise ValueError(f"invalid PNG IDAT: {error}") from error
    if len(raw) != (stride + 1) * height:
        raise ValueError("PNG scanline length mismatch")

    previous = bytearray(stride)
    rows: list[bytearray] = []
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        encoded = raw[cursor : cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                estimate = left + above - upper_left
                distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            else:
                raise ValueError("unsupported PNG row filter")
            row[index] = (value + predictor) & 0xFF
        rows.append(row)
        previous = row

    sampled: set[tuple[int, int, int]] = set()
    values: list[float] = []
    for y in range(0, height, 8):
        row = rows[y]
        for x in range(0, width, 8):
            pixel = x * bytes_per_pixel
            red, green, blue = row[pixel], row[pixel + 1], row[pixel + 2]
            sampled.add((red, green, blue))
            values.append((0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0)
    if not values:
        raise ValueError("PNG has no sampled pixels")
    mean = sum(values) / len(values)
    variance = max(0.0, sum(value * value for value in values) / len(values) - mean * mean)
    return PngMetrics(width, height, variance**0.5, max(values) - min(values), len(sampled))


def _bound_scene_hash(text: str, current: str, label: str, errors: list[str]) -> None:
    match = re.search(r"Scene(?: source)? SHA256: `([0-9a-f]{64})`", text)
    if not match:
        errors.append(f"{label} has no scene SHA256 binding")
    elif match.group(1) != current:
        errors.append(f"{label} is bound to stale scene {match.group(1)}, expected {current}")


def _check_fable_text(text: str, errors: list[str]) -> None:
    decisions = re.findall(r"^LOCAL_FABLE_DECISION: ship$", text, re.MULTILINE)
    if len(decisions) != 1:
        errors.append(f"Local Fable final review has {len(decisions)} ship decisions, expected exactly one")


def _file_record(root: Path, relative: Path) -> dict[str, str | int]:
    path = root / relative
    return {"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def _runtime_files(root: Path) -> list[Path]:
    build = root / BUILD_ROOT
    if not build.exists():
        return []
    return sorted(
        (
            path.relative_to(root)
            for path in build.rglob("*")
            if path.is_file() and all("DoNotShip" not in part for part in path.parts)
        ),
        key=lambda path: path.as_posix(),
    )


def _write_binding(root: Path, output: Path, schema: str, artifacts: list[Path]) -> None:
    sources = [*V9_SOURCES, *GENERATED_MESHES, *V9_ASSET_META]
    payload = {
        "schema": schema,
        "verdict": "passed",
        "baseline_commit": SCENE_BASELINE_REVISION,
        "scene": _file_record(root, SCENE),
        "player": _file_record(root, PLAYER),
        "built_level": _file_record(root, BUILT_LEVEL),
        "managed_assembly": _file_record(root, MANAGED_ASSEMBLY),
        "runtime_files": [_file_record(root, path) for path in _runtime_files(root)],
        "sources": [_file_record(root, path) for path in sources],
        "artifacts": [_file_record(root, path) for path in artifacts],
    }
    destination = root / output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _check_binding(
    root: Path,
    relative: Path,
    schema: str,
    scene_hash: str,
    expected_artifacts: list[Path],
    result: ValidationResult,
) -> None:
    path = root / relative
    if not path.exists():
        result.errors.append(f"missing binding: {relative.as_posix()}")
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        result.errors.append(f"invalid binding {relative.as_posix()}: {error}")
        return
    if payload.get("schema") != schema or payload.get("verdict") != "passed":
        result.errors.append(f"binding schema/verdict mismatch: {relative.as_posix()}")
    if payload.get("baseline_commit") != SCENE_BASELINE_REVISION:
        result.errors.append(f"binding baseline mismatch: {relative.as_posix()}")
    if payload.get("scene", {}).get("sha256") != scene_hash:
        result.errors.append(f"binding scene hash mismatch: {relative.as_posix()}")
    expected_sources = {path.as_posix() for path in (*V9_SOURCES, *GENERATED_MESHES, *V9_ASSET_META)}
    actual_sources = {
        record.get("path") for record in payload.get("sources", []) if isinstance(record, dict)
    }
    expected_evidence = {path.as_posix() for path in expected_artifacts}
    actual_evidence = {
        record.get("path") for record in payload.get("artifacts", []) if isinstance(record, dict)
    }
    if actual_sources != expected_sources:
        result.errors.append(f"binding source inventory mismatch: {relative.as_posix()}")
    if actual_evidence != expected_evidence:
        result.errors.append(f"binding artifact inventory mismatch: {relative.as_posix()}")
    expected_runtime = {path.as_posix() for path in _runtime_files(root)}
    actual_runtime = {
        record.get("path") for record in payload.get("runtime_files", []) if isinstance(record, dict)
    }
    if not expected_runtime or actual_runtime != expected_runtime:
        result.errors.append(f"binding runtime payload inventory mismatch: {relative.as_posix()}")
    records = [payload.get("scene"), payload.get("player"), payload.get("built_level"), payload.get("managed_assembly")]
    records.extend(payload.get("runtime_files", []))
    records.extend(payload.get("sources", []))
    records.extend(payload.get("artifacts", []))
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            result.errors.append(f"binding has malformed record: {relative.as_posix()}")
            continue
        target = root / record["path"]
        if not target.exists():
            result.errors.append(f"binding target missing: {record['path']}")
        elif record.get("sha256") != sha256(target) or record.get("bytes") != target.stat().st_size:
            result.errors.append(f"binding hash mismatch: {record['path']}")


def _scene_documents(text: str) -> dict[int, SceneDocument]:
    headers = list(re.finditer(r"^--- !u!(\d+) &(-?\d+)\s*$", text, re.MULTILINE))
    documents: dict[int, SceneDocument] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        document = SceneDocument(int(header.group(1)), int(header.group(2)), text[header.end():end])
        documents[document.file_id] = document
    return documents


def _scene_inventory(text: str) -> dict[str, object]:
    documents = _scene_documents(text)
    names: dict[int, str] = {}
    components: dict[int, list[int]] = {}
    transform_to_game_object: dict[int, int] = {}
    parent_by_transform: dict[int, int] = {}
    for document in documents.values():
        if document.class_id == 1:
            name = re.search(r"^  m_Name: (.*)$", document.body, re.MULTILINE)
            names[document.file_id] = name.group(1).strip() if name else ""
            components[document.file_id] = [
                int(value)
                for value in re.findall(r"^  - component: \{fileID: (-?\d+)\}", document.body, re.MULTILINE)
            ]
        elif document.class_id in (4, 224):
            game_object = re.search(r"^  m_GameObject: \{fileID: (-?\d+)\}", document.body, re.MULTILINE)
            parent = re.search(r"^  m_Father: \{fileID: (-?\d+)\}", document.body, re.MULTILINE)
            if game_object:
                transform_to_game_object[document.file_id] = int(game_object.group(1))
            if parent:
                parent_by_transform[document.file_id] = int(parent.group(1))
    transform_by_game_object = {game_object: transform for transform, game_object in transform_to_game_object.items()}
    roots = [game_object for game_object, name in names.items() if name == V9_ROOT_NAME]
    v9_game_objects: set[int] = set()
    v9_root_transform = 0
    if len(roots) == 1:
        v9_root_transform = transform_by_game_object.get(roots[0], 0)
        pending = [v9_root_transform]
        while pending:
            transform = pending.pop()
            game_object = transform_to_game_object.get(transform)
            if game_object is None or game_object in v9_game_objects:
                continue
            v9_game_objects.add(game_object)
            pending.extend(child for child, parent in parent_by_transform.items() if parent == transform)
    v9_documents = set(v9_game_objects)
    for game_object in v9_game_objects:
        v9_documents.update(components.get(game_object, []))
    map_roots = [game_object for game_object, name in names.items() if name == MAP_ROOT_NAME]
    map_transform = transform_by_game_object.get(map_roots[0], 0) if len(map_roots) == 1 else 0
    return {
        "documents": documents,
        "names": names,
        "components": components,
        "v9_documents": v9_documents,
        "v9_root_transform": v9_root_transform,
        "map_transform": map_transform,
    }


def _game_object_id(document: SceneDocument) -> int:
    if document.class_id == 1:
        return document.file_id
    match = re.search(r"^  m_GameObject: \{fileID: (-?\d+)\}", document.body, re.MULTILINE)
    return int(match.group(1)) if match else 0


def _normalized_enabled(body: str) -> str:
    return re.sub(r"^  m_Enabled: [01]$", "  m_Enabled: <normalized>", body, flags=re.MULTILINE)


def _scene_delta(baseline: str, current: str) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    before = _scene_inventory(baseline)
    after = _scene_inventory(current)
    before_documents = before["documents"]
    after_documents = after["documents"]
    assert isinstance(before_documents, dict) and isinstance(after_documents, dict)
    before_ids = set(before_documents)
    after_ids = set(after_documents)
    v9_documents = after["v9_documents"]
    assert isinstance(v9_documents, set)
    removed = before_ids - after_ids
    added = after_ids - before_ids
    if removed:
        errors.append(f"scene removed {len(removed)} V8-baseline documents")
    if added != v9_documents:
        errors.append("scene additions are not exactly the V9-owned document set")

    class_counts = Counter(after_documents[file_id].class_id for file_id in v9_documents)
    expected_classes = Counter({1: 63, 4: 63, 23: 5, 33: 5, 65: 23})
    if len(v9_documents) != 159 or class_counts != expected_classes:
        errors.append(f"V9 scene ownership inventory drifted: documents={len(v9_documents)} classes={dict(class_counts)}")

    names = after["names"]
    assert isinstance(names, dict)
    transitions: list[str] = []
    map_transform = after["map_transform"]
    v9_root_transform = after["v9_root_transform"]
    parent_references = 0
    for file_id in sorted(before_ids & after_ids):
        old = before_documents[file_id]
        new = after_documents[file_id]
        if old.class_id != new.class_id:
            errors.append(f"scene class changed for baseline document {file_id}")
            continue
        if old.body == new.body:
            continue
        if file_id == map_transform:
            line = f"  - {{fileID: {v9_root_transform}}}\n"
            parent_references = new.body.count(line)
            if new.body.replace(line, "") != old.body:
                errors.append("map root transform changed outside the V9 child reference")
            continue
        game_object = _game_object_id(new)
        name = names.get(game_object, "")
        old_enabled = re.search(r"^  m_Enabled: ([01])$", old.body, re.MULTILINE)
        new_enabled = re.search(r"^  m_Enabled: ([01])$", new.body, re.MULTILINE)
        if (
            new.class_id == 23
            and name in EXPECTED_DISABLED_RENDERERS
            and old_enabled
            and new_enabled
            and old_enabled.group(1) == "1"
            and new_enabled.group(1) == "0"
            and _normalized_enabled(old.body) == _normalized_enabled(new.body)
        ):
            transitions.append(name)
            continue
        errors.append(f"baseline scene document changed outside allowance: class={new.class_id} name={name}")
    if parent_references != 1:
        errors.append(f"map root has {parent_references} V9 child references, expected 1")
    if set(transitions) != EXPECTED_DISABLED_RENDERERS or len(transitions) != 20:
        errors.append(f"renderer transition whitelist drifted: {len(transitions)} transitions")
    facts = {
        "scene_baseline_documents": len(before_documents),
        "scene_v9_documents": len(v9_documents),
        "scene_renderer_transitions": len(transitions),
    }
    return errors, facts


def _check_scene_scope(root: Path, use_index: bool, result: ValidationResult) -> None:
    baseline_bytes = subprocess.run(
        ["git", "show", f"{SCENE_BASELINE_REVISION}:{SCENE.as_posix()}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()
    if baseline_hash != SCENE_BASELINE_SHA256:
        result.errors.append(f"scene baseline hash mismatch: {baseline_hash}, expected {SCENE_BASELINE_SHA256}")
    if use_index:
        current = subprocess.run(
            ["git", "show", f":{SCENE.as_posix()}"], cwd=root, check=True, capture_output=True
        ).stdout.decode("utf-8")
    else:
        current = (root / SCENE).read_text(encoding="utf-8")
    errors, facts = _scene_delta(baseline_bytes.decode("utf-8"), current)
    result.errors.extend(errors)
    result.facts.update(facts)
    result.facts["scene_scope_baseline_revision"] = SCENE_BASELINE_REVISION


def _allowed_staged(path: str) -> bool:
    exact = {
        *[item.as_posix() for item in REQUIRED_FILES],
        "tools/validate_khufu_v9_causeway_fidelity.py",
        "tools/tests/test_validate_khufu_v9_causeway_fidelity.py",
        FABLE_REVIEW.as_posix(),
        (RUN_ROOT / "pre-fable-validation.md").as_posix(),
        (RUN_ROOT / "post-fable-validation.md").as_posix(),
        (RUN_ROOT / "staged-index-validation.md").as_posix(),
        (RUN_ROOT / "post-commit-validation.md").as_posix(),
    }
    return path in exact


def _check_staged(root: Path, require_fable: bool, result: ValidationResult) -> None:
    command = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"], cwd=root, check=True, capture_output=True
    )
    staged = [item for item in command.stdout.decode("utf-8").split("\0") if item]
    if not staged:
        result.errors.append("staged-scope check requested but index is empty")
        return
    result.errors.extend(f"out-of-scope staged path: {path}" for path in staged if not _allowed_staged(path))
    required = {
        *[path.as_posix() for path in REQUIRED_FILES],
        "tools/validate_khufu_v9_causeway_fidelity.py",
        "tools/tests/test_validate_khufu_v9_causeway_fidelity.py",
    }
    if require_fable:
        required.add(FABLE_REVIEW.as_posix())
    missing = sorted(required.difference(staged))
    result.errors.extend(f"required V9 path not staged: {path}" for path in missing)
    worktree_drift = subprocess.run(
        ["git", "diff", "--name-only", "-z"], cwd=root, check=True, capture_output=True
    ).stdout.decode("utf-8").split("\0")
    drifted_staged = sorted(set(staged).intersection(path for path in worktree_drift if path))
    result.errors.extend(
        f"staged artifact differs from validated worktree: {path}" for path in drifted_staged
    )
    result.facts["staged_files"] = len(staged)
    result.facts["staged_worktree_drift"] = len(drifted_staged)


def _check_pngs(root: Path, result: ValidationResult) -> None:
    hashes: set[str] = set()
    minimum_standard_deviation = 1.0
    minimum_range = 1.0
    minimum_unique_colors = 2**31 - 1
    for relative in PNG_FILES:
        path = root / relative
        if not path.exists():
            continue
        try:
            metrics = png_semantic_metrics(path)
        except ValueError as error:
            result.errors.append(f"invalid PNG {relative.as_posix()}: {error}")
            continue
        if path.stat().st_size < 65536 or metrics.width < 1280 or metrics.height < 720:
            result.errors.append(f"undersized PNG evidence: {relative.as_posix()}")
        if metrics.standard_deviation < 0.03 or metrics.value_range < 0.20 or metrics.unique_sampled_colors < 64:
            result.errors.append(f"blank or low-information PNG evidence: {relative.as_posix()}")
        minimum_standard_deviation = min(minimum_standard_deviation, metrics.standard_deviation)
        minimum_range = min(minimum_range, metrics.value_range)
        minimum_unique_colors = min(minimum_unique_colors, metrics.unique_sampled_colors)
        digest = sha256(path)
        if digest in hashes:
            result.errors.append(f"duplicate PNG evidence hash: {relative.as_posix()}")
        hashes.add(digest)
    result.facts["png_evidence"] = len(hashes)
    result.facts["png_min_stddev"] = f"{minimum_standard_deviation:.4f}"
    result.facts["png_min_range"] = f"{minimum_range:.4f}"
    result.facts["png_min_unique_sampled_colors"] = minimum_unique_colors


def validate(root: Path, require_fable: bool, check_staged: bool) -> ValidationResult:
    result = ValidationResult()
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.exists() or path.stat().st_size == 0:
            result.errors.append(f"missing or empty required file: {relative.as_posix()}")
    for relative, token in REQUIRED_TOKENS.items():
        path = root / relative
        if path.exists() and token not in path.read_text(encoding="utf-8"):
            result.errors.append(f"missing pass token in {relative.as_posix()}: {token}")
    scene_hash = sha256(root / SCENE)
    for relative in (RUN_ROOT / "windows-build.md", RUN_ROOT / "captures/manifest.md", RUN_ROOT / "v5-playmode-regression.md"):
        path = root / relative
        if path.exists():
            _bound_scene_hash(path.read_text(encoding="utf-8"), scene_hash, relative.as_posix(), result.errors)
    build_receipt = root / RUN_ROOT / "windows-build.md"
    if build_receipt.exists():
        build_text = build_receipt.read_text(encoding="utf-8")
        if sha256(root / PLAYER) not in build_text:
            result.errors.append("Windows build receipt is not bound to the current player")
        missing_payload_hashes = [
            path.as_posix() for path in _runtime_files(root) if sha256(root / path) not in build_text
        ]
        result.errors.extend(
            f"Windows build receipt omits runtime payload hash: {path}" for path in missing_payload_hashes
        )
        result.facts["runtime_payload_files"] = len(_runtime_files(root))
    for relative, expected_fresh_captures in (
        (RUN_ROOT / "player-proof/v9-final-causeway-traversal.md", 3),
        (RUN_ROOT / "player-proof/v9-final-proxy-mutation.md", 2),
    ):
        path = root / relative
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text.count("/ fresh `True` / semantic `True`") != expected_fresh_captures:
                result.errors.append(f"runtime capture freshness/semantic proof mismatch: {relative.as_posix()}")
    _check_binding(root, EDITOR_BINDING, "khufu-v9-editor-evidence-binding-v1", scene_hash, EDITOR_ARTIFACTS, result)
    _check_binding(root, PLAYER_BINDING, "khufu-v9-player-proof-binding-v1", scene_hash, PLAYER_ARTIFACTS, result)
    _check_binding(
        root,
        PERFORMANCE_BINDING,
        "khufu-v9-performance-binding-v1",
        scene_hash,
        PERFORMANCE_ARTIFACTS,
        result,
    )
    _check_pngs(root, result)
    _check_scene_scope(root, check_staged, result)
    if require_fable:
        if not (root / FABLE_REVIEW).exists():
            result.errors.append("Local Fable final review is missing")
        else:
            _check_fable_text((root / FABLE_REVIEW).read_text(encoding="utf-8"), result.errors)
    if check_staged:
        _check_staged(root, require_fable, result)
    result.facts["required_files"] = len(REQUIRED_FILES)
    result.facts["scene_sha256"] = scene_hash
    return result


def write_report(path: Path, result: ValidationResult, require_fable: bool, check_staged: bool) -> None:
    lines = [
        "# Khufu V9 Aggregate Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Local Fable required: `{require_fable}`",
        f"- Staged scope checked: `{check_staged}`",
    ]
    for name, value in sorted(result.facts.items()):
        lines.append(f"- {name}: `{value}`")
    for error in result.errors:
        lines.append(f"- Failure: `{error}`")
    lines.extend(["", f"V9_AGGREGATE_VERDICT: {'passed' if result.passed else 'failed'}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh-bindings", action="store_true")
    parser.add_argument("--require-fable", action="store_true")
    parser.add_argument("--check-staged", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.refresh_bindings:
        _write_binding(root, EDITOR_BINDING, "khufu-v9-editor-evidence-binding-v1", EDITOR_ARTIFACTS)
        _write_binding(root, PLAYER_BINDING, "khufu-v9-player-proof-binding-v1", PLAYER_ARTIFACTS)
        _write_binding(root, PERFORMANCE_BINDING, "khufu-v9-performance-binding-v1", PERFORMANCE_ARTIFACTS)
    result = validate(root, args.require_fable, args.check_staged)
    write_report(root / args.output, result, args.require_fable, args.check_staged)
    print(f"V9_AGGREGATE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
