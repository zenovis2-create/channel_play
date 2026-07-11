from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


RUN_ROOT = Path("runs/khufu-v8-temple-production-art")
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
SCENE_BASELINE_REVISION = "d8e4af4b172cebc3de56210efc04def543a82e3b"
SCENE_BASELINE_SHA256 = "a17075bcf6b21a5231edf32bb0247e3c755925a97c39c25a12dba506e40cf029"
PLAYER = Path("Builds/KhufuV8/ChannelPlayKhufuV8.exe")
BUILT_LEVEL = Path("Builds/KhufuV8/ChannelPlayKhufuV8_Data/level0")
PLAYER_BINDING = RUN_ROOT / "player-proof/binding.json"
PERFORMANCE_BINDING = RUN_ROOT / "performance-final/binding.json"

FROZEN_INPUTS = {
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs"): "0a9f7a1f071db40fbab05e955e41acfbfa98c6b22aa7ee9d059f454392184faf",
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs"): "405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd",
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs"): "ffa6fa51a20074760181db6c87319f2aad5afca443e37f80da657b17759c75f2",
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs"): "6ab23d70ce11c8c8e69352937150599352a821db55426e150935e0fec2a3cf1c",
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingBuilder.cs"): "3d7cd2f0542d2b3755ce449433b2c00e5a2261bcbe2df050401a0b8af77429f6",
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs"): "746130bbd87310bcad04be5914d5622cbed7a8cf3c84d29d95fb0002bf802a08",
    Path("Packages/manifest.json"): "7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38",
    Path("Packages/packages-lock.json"): "d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e",
    Path("Assets/_Project/Art/Maps/pyramid_temple_real/pyramid_temple_full_environment.fbx"): "234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d",
    Path("Assets/_Project/Art/Maps/pyramid_temple_real/pyramid_temple_full_environment.fbx.meta"): "6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094",
}

V8_SOURCES = [
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtAudit.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtPipeline.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtBuilder.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtScreenshotExporter.cs"),
    Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8WindowsBuild.cs"),
    Path("Assets/_Project/Scripts/Gameplay/KhufuV8TempleProofProbe.cs"),
]

PLAYER_ARTIFACTS = [
    RUN_ROOT / "windows-build.md",
    RUN_ROOT / "captures/manifest.md",
    RUN_ROOT / "captures/causeway_arrival.png",
    RUN_ROOT / "captures/court_wide.png",
    RUN_ROOT / "captures/court_to_pyramid.png",
    RUN_ROOT / "captures/temple_plan_oblique.png",
    RUN_ROOT / "captures/mutation_graybox_overlap.png",
    RUN_ROOT / "player-proof/v8-final-temple-proof.md",
    RUN_ROOT / "player-proof/v8-final-graybox-mutation.md",
    RUN_ROOT / "player-proof/v8-final-participant-temple.png",
    RUN_ROOT / "player-proof/v8-final-graybox-mutation.png",
    RUN_ROOT / "player-proof/normal-player-final.log",
    RUN_ROOT / "player-proof/mutation-player-final.log",
]

PERFORMANCE_ARTIFACTS = [
    RUN_ROOT / "performance-final/validation.md",
    RUN_ROOT / "performance-final/v8-final-performance.md",
    RUN_ROOT / "performance-final/v8-final.raw",
    RUN_ROOT / "performance-final/player.log",
    RUN_ROOT / "performance-final/v8-final-windows-player-initial.png",
    RUN_ROOT / "performance-final/v8-final-windows-player-operator.png",
]

REQUIRED_TEXT = {
    RUN_ROOT / "fbx-audit.md": "KHUFU_V8_SOURCE_ART_AUDIT: passed",
    RUN_ROOT / "pipeline-spike.md": "KHUFU_V8_PIPELINE_SPIKE: passed",
    RUN_ROOT / "validation.md": "V8_STATIC_VALIDATION: passed",
    RUN_ROOT / "idempotence.md": "V8_IDEMPOTENCE: passed",
    RUN_ROOT / "placement-mutation.md": "V8_PLACEMENT_MUTATION: passed",
    RUN_ROOT / "graybox-mutation.md": "V8_GRAYBOX_MUTATION: passed",
    RUN_ROOT / "pillar-intrusion-mutation.md": "V8_PILLAR_INTRUSION_MUTATION: passed",
    RUN_ROOT / "captures/manifest.md": "GRAYBOX_MUTATION_CAPTURE: passed",
    RUN_ROOT / "windows-build.md": "V8_WINDOWS_BUILD: passed",
    RUN_ROOT / "player-proof/v8-final-temple-proof.md": "V8_WINDOWS_PLAYER_TEMPLE_PROOF: passed",
    RUN_ROOT / "player-proof/v8-final-graybox-mutation.md": "V8_GRAYBOX_PLAYER_MUTATION: passed",
    RUN_ROOT / "performance-final/validation.md": "PERFORMANCE_VERDICT: passed",
    RUN_ROOT / "post-commit-validation.md": "V8_AGGREGATE_VERDICT: passed",
    Path("runs/khufu-mega-labyrinth-v5/gate4-acceptance.md"): "Verdict: **passed**",
    Path("runs/khufu-v7-entry-wayfinding/v5-playmode-regression.md"): "V7_V5_PLAYMODE_REGRESSION: passed",
}

REQUIRED_DOCS = [
    Path("docs/khufu-v8-temple-production-art/GOAL.md"),
    Path("docs/khufu-v8-temple-production-art/PLAN.md"),
    Path("docs/khufu-v8-temple-production-art/STATUS.md"),
    Path("docs/khufu-v8-temple-production-art/RULES.md"),
    Path("docs/khufu-v8-temple-production-art/TEST_PLAN.md"),
    Path("docs/khufu-v8-temple-production-art/RESEARCH_BRIEF.md"),
    Path("docs/khufu-v8-temple-production-art/performance-budget.json"),
]

FABLE_PLAN = Path("work/fable-harness/khufu-v8-temple-production-art-plan-critique.retry.fable.md")
FABLE_FINAL = Path("work/fable-harness/khufu-v8-temple-production-art-final-review.fable.md")
V8_ROOT_NAME = "Runtime_Khufu_V8_Temple_Hub_Art"
SCENE_ROOT_PATH = "TraitorEscape_Runtime_Map"


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


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG")
    return struct.unpack(">II", header[16:24])


def _bound_scene_hash(text: str, current: str, label: str, errors: list[str]) -> None:
    match = re.search(r"Scene(?: source)? SHA256: `([0-9a-f]{64})`", text)
    if match is None:
        errors.append(f"{label} has no scene hash")
    elif match.group(1) != current:
        errors.append(f"{label} is bound to stale scene {match.group(1)}, expected {current}")


def _check_fable_text(text: str, errors: list[str]) -> None:
    decisions = re.findall(r"^FINAL_REVIEW: ship\s*$", text, re.MULTILINE)
    if len(decisions) != 1:
        errors.append(f"Fable final review has {len(decisions)} ship decisions, expected exactly one")


def _file_record(root: Path, relative: Path) -> dict[str, str | int]:
    path = root / relative
    return {"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def _write_binding(root: Path, output: Path, schema: str, artifacts: list[Path]) -> None:
    payload = {
        "schema": schema,
        "verdict": "passed",
        "scene": _file_record(root, SCENE),
        "player": _file_record(root, PLAYER),
        "built_level": _file_record(root, BUILT_LEVEL),
        "sources": [_file_record(root, path) for path in V8_SOURCES],
        "artifacts": [_file_record(root, path) for path in artifacts],
    }
    target = root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _check_binding(root: Path, relative: Path, schema: str, scene_hash: str, result: ValidationResult) -> None:
    path = root / relative
    if not path.is_file():
        result.errors.append(f"missing binding: {relative.as_posix()}")
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        result.errors.append(f"invalid binding {relative.as_posix()}: {error}")
        return
    if payload.get("schema") != schema or payload.get("verdict") != "passed":
        result.errors.append(f"binding schema/verdict mismatch: {relative.as_posix()}")
    if payload.get("scene", {}).get("sha256") != scene_hash:
        result.errors.append(f"binding scene hash mismatch: {relative.as_posix()}")
    for record in [payload.get("scene"), payload.get("player"), payload.get("built_level"), *payload.get("sources", []), *payload.get("artifacts", [])]:
        if not isinstance(record, dict) or "path" not in record:
            result.errors.append(f"binding has malformed record: {relative.as_posix()}")
            continue
        actual = root / Path(record["path"])
        if not actual.is_file():
            result.errors.append(f"binding target missing: {record['path']}")
            continue
        if actual.stat().st_size != record.get("bytes") or sha256(actual) != record.get("sha256"):
            result.errors.append(f"binding hash mismatch: {record['path']}")


def _check_pngs(root: Path, paths: list[Path], result: ValidationResult) -> None:
    hashes: set[str] = set()
    for relative in paths:
        path = root / relative
        if not path.is_file():
            result.errors.append(f"missing PNG: {relative.as_posix()}")
            continue
        try:
            dimensions = png_dimensions(path)
        except ValueError as error:
            result.errors.append(f"{relative.as_posix()}: {error}")
            continue
        if dimensions != (1536, 1024):
            result.errors.append(f"wrong PNG dimensions: {relative.as_posix()} {dimensions}")
        if path.stat().st_size < 65536:
            result.errors.append(f"PNG too small: {relative.as_posix()}")
        hashes.add(sha256(path))
    if len(hashes) != len(paths):
        result.errors.append("required PNG evidence is missing or duplicated")


def _allowed_staged(path: str) -> bool:
    exact = {
        SCENE.as_posix(),
        "Assets/_Project/Art/Generated.meta",
        "Assets/_Project/Art/Maps.meta",
        "Assets/_Project/Art/Maps/pyramid_temple_real.meta",
        "Assets/_Project/Art/Maps/pyramid_temple_real/pyramid_temple_full_environment.fbx",
        "Assets/_Project/Art/Maps/pyramid_temple_real/pyramid_temple_full_environment.fbx.meta",
        "Assets/_Project/Art/Generated/KhufuV8TempleHub.meta",
        "runs/khufu-v7-entry-wayfinding/v5-playmode-regression.md",
        "tools/validate_khufu_v8_temple_production_art.py",
        "tools/tests/test_validate_khufu_v8_temple_production_art.py",
    }
    prefixes = (
        "Assets/_Project/Art/Generated/KhufuV8TempleHub/",
        "docs/khufu-v8-temple-production-art/",
        "runs/khufu-v8-temple-production-art/",
        "work/fable-harness/khufu-v8-temple-production-art-",
    )
    if path in exact or path.startswith(prefixes):
        return True
    return any(path == source.as_posix() or path == source.as_posix() + ".meta" for source in V8_SOURCES)


def _scene_documents(text: str) -> list[tuple[int, int, str]]:
    headers = list(re.finditer(r"^--- !u!(\d+) &(-?\d+)\s*$", text, re.MULTILINE))
    documents: list[tuple[int, int, str]] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        documents.append((int(header.group(1)), int(header.group(2)), text[header.end():end]))
    return documents


def _scene_semantics(text: str) -> tuple[Counter[str], Counter[int], Counter[tuple[str, int]], set[int], Counter[int]]:
    documents = _scene_documents(text)
    names_by_id: dict[int, str] = {}
    class_counts: Counter[int] = Counter(class_id for class_id, _, _ in documents)
    for class_id, file_id, body in documents:
        if class_id != 1:
            continue
        match = re.search(r"^  m_Name: (.*)$", body, re.MULTILINE)
        names_by_id[file_id] = match.group(1).strip() if match else ""
    v8_ids = {file_id for file_id, name in names_by_id.items() if name == "Runtime_Khufu_V8_Temple_Hub_Art" or name.startswith("V8_")}
    name_counts = Counter(names_by_id.values())
    renderer_states: Counter[tuple[str, int]] = Counter()
    v8_component_counts: Counter[int] = Counter()
    for class_id, file_id, body in documents:
        if class_id == 1:
            game_object_id = file_id
        else:
            match = re.search(r"^  m_GameObject: \{fileID: (-?\d+)\}", body, re.MULTILINE)
            game_object_id = int(match.group(1)) if match else 0
        if game_object_id in v8_ids:
            v8_component_counts[class_id] += 1
        if class_id == 23 and game_object_id in names_by_id:
            enabled_match = re.search(r"^  m_Enabled: (\d+)", body, re.MULTILINE)
            renderer_states[(names_by_id[game_object_id], int(enabled_match.group(1)) if enabled_match else -1)] += 1
    return name_counts, class_counts, renderer_states, v8_ids, v8_component_counts


def _canonical_scene_documents(text: str) -> tuple[dict[str, str], set[str]]:
    documents = _scene_documents(text)
    by_id = {file_id: (class_id, body) for class_id, file_id, body in documents}
    names: dict[int, str] = {}
    components_by_game_object: dict[int, list[int]] = {}
    game_object_by_transform: dict[int, int] = {}
    parent_by_transform: dict[int, int] = {}

    for class_id, file_id, body in documents:
        if class_id == 1:
            name = re.search(r"^  m_Name: (.*)$", body, re.MULTILINE)
            names[file_id] = name.group(1).strip() if name else ""
            components_by_game_object[file_id] = [
                int(value)
                for value in re.findall(r"^  - component: \{fileID: (-?\d+)\}", body, re.MULTILINE)
            ]
        elif class_id in (4, 224):
            game_object = re.search(r"^  m_GameObject: \{fileID: (-?\d+)\}", body, re.MULTILINE)
            parent = re.search(r"^  m_Father: \{fileID: (-?\d+)\}", body, re.MULTILINE)
            if game_object:
                game_object_by_transform[file_id] = int(game_object.group(1))
            if parent:
                parent_by_transform[file_id] = int(parent.group(1))

    transform_by_game_object = {game_object: transform for transform, game_object in game_object_by_transform.items()}
    parent_by_game_object = {
        game_object: game_object_by_transform.get(parent_by_transform.get(transform, 0), 0)
        for game_object, transform in transform_by_game_object.items()
    }
    paths: dict[int, str] = {}
    visiting: set[int] = set()

    def hierarchy_path(game_object: int) -> str:
        if game_object in paths:
            return paths[game_object]
        if game_object in visiting:
            raise ValueError("scene hierarchy contains a cycle")
        visiting.add(game_object)
        parent = parent_by_game_object.get(game_object, 0)
        prefix = hierarchy_path(parent) + "/" if parent else ""
        paths[game_object] = prefix + names.get(game_object, "")
        visiting.remove(game_object)
        return paths[game_object]

    path_counts = Counter(hierarchy_path(game_object) for game_object in names)
    duplicates = [path for path, count in path_counts.items() if count != 1]
    if duplicates:
        raise ValueError(f"scene hierarchy has duplicate canonical paths: {duplicates[:3]}")

    reference_labels: dict[int, str] = {0: "null"}
    document_keys: dict[int, str] = {}
    v8_keys: set[str] = set()
    for game_object in names:
        path = hierarchy_path(game_object)
        key = "go:" + path
        reference_labels[game_object] = key
        document_keys[game_object] = key
        if V8_ROOT_NAME in path.split("/"):
            v8_keys.add(key)

    for game_object, component_ids in components_by_game_object.items():
        class_occurrences: Counter[int] = Counter()
        path = hierarchy_path(game_object)
        for component_id in component_ids:
            if component_id not in by_id:
                raise ValueError(f"scene GameObject references missing component {component_id}")
            class_id = by_id[component_id][0]
            class_occurrences[class_id] += 1
            key = f"component:{path}:{class_id}:{class_occurrences[class_id]}"
            reference_labels[component_id] = key
            document_keys[component_id] = key
            if V8_ROOT_NAME in path.split("/"):
                v8_keys.add(key)

    global_occurrences: Counter[int] = Counter()
    for class_id, file_id, _ in documents:
        if file_id in document_keys:
            continue
        global_occurrences[class_id] += 1
        key = f"global:{class_id}:{global_occurrences[class_id]}"
        reference_labels[file_id] = key
        document_keys[file_id] = key

    def normalize_references(body: str) -> str:
        def replace_reference(match: re.Match[str]) -> str:
            file_id = int(match.group(1))
            return "{ref: " + reference_labels.get(file_id, f"unmapped:{file_id}") + "}"

        return re.sub(r"\{fileID: (-?\d+)\}", replace_reference, body)

    canonical = {
        document_keys[file_id]: normalize_references(body)
        for _, file_id, body in documents
    }
    return canonical, v8_keys


def _canonical_scene_delta(
    head: str,
    current: str,
    expected_v5: int = 5,
    expected_v6: int = 11,
    expected_v8_documents: int = 64,
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    head_documents, head_v8_keys = _canonical_scene_documents(head)
    current_documents, current_v8_keys = _canonical_scene_documents(current)
    head_keys = set(head_documents)
    current_keys = set(current_documents)
    removed = head_keys - current_keys
    added = current_keys - head_keys

    if head_v8_keys:
        errors.append("HEAD scene unexpectedly contains V8-owned documents")
    if removed:
        errors.append(f"scene removed {len(removed)} pre-existing canonical documents")
    if added != current_v8_keys:
        errors.append(
            "scene added canonical documents outside V8 ownership: "
            + ", ".join(sorted(added - current_v8_keys)[:3])
        )
    if len(current_v8_keys) != expected_v8_documents:
        errors.append(
            f"scene contains {len(current_v8_keys)} V8-owned documents, expected {expected_v8_documents}"
        )

    enabled_transitions: list[str] = []
    v8_parent_references = 0
    root_transform_key = f"component:{SCENE_ROOT_PATH}:4:1"
    for key in sorted(head_keys & current_keys):
        before = head_documents[key]
        after = current_documents[key]
        if key == root_transform_key:
            lines = after.splitlines(keepends=True)
            kept = [line for line in lines if not (V8_ROOT_NAME in line and "{ref: component:" in line)]
            v8_parent_references += len(lines) - len(kept)
            after = "".join(kept)
        if before == after:
            continue

        is_renderer = key.startswith("component:") and key.rsplit(":", 2)[1] == "23"
        before_enabled = re.search(r"^  m_Enabled: ([01])$", before, re.MULTILINE)
        after_enabled = re.search(r"^  m_Enabled: ([01])$", after, re.MULTILINE)
        normalized_before = re.sub(r"^  m_Enabled: [01]$", "  m_Enabled: <normalized>", before, flags=re.MULTILINE)
        normalized_after = re.sub(r"^  m_Enabled: [01]$", "  m_Enabled: <normalized>", after, flags=re.MULTILINE)
        if (
            is_renderer
            and before_enabled
            and after_enabled
            and before_enabled.group(1) == "1"
            and after_enabled.group(1) == "0"
            and normalized_before == normalized_after
        ):
            enabled_transitions.append(key)
            continue
        errors.append(f"pre-existing canonical scene document changed outside allowance: {key}")

    if v8_parent_references != 1:
        errors.append(f"scene root has {v8_parent_references} V8 child references, expected 1")
    v5_transitions = sum(
        1 for key in enabled_transitions
        if key[len("component:"):].rsplit(":", 2)[0].rsplit("/", 1)[-1].startswith("V5_")
    )
    v6_transitions = sum(
        1 for key in enabled_transitions
        if key[len("component:"):].rsplit(":", 2)[0].rsplit("/", 1)[-1].startswith("V6_")
    )
    if len(enabled_transitions) != expected_v5 + expected_v6 or v5_transitions != expected_v5 or v6_transitions != expected_v6:
        errors.append(
            "canonical renderer transitions are not the expected V5/V6 split: "
            f"total={len(enabled_transitions)}, V5={v5_transitions}, V6={v6_transitions}"
        )
    facts = {
        "scene_scope_existing_documents": len(head_documents),
        "scene_scope_added_v8_documents": len(current_v8_keys),
        "scene_scope_canonical_renderer_transitions": len(enabled_transitions),
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
        result.errors.append(
            f"scene baseline hash mismatch: {baseline_hash}, expected {SCENE_BASELINE_SHA256}"
        )
    head = baseline_bytes.decode("utf-8")
    if use_index:
        current = subprocess.run(
            ["git", "show", f":{SCENE.as_posix()}"], cwd=root, check=True, capture_output=True
        ).stdout.decode("utf-8")
    else:
        current = (root / SCENE).read_text(encoding="utf-8")
    try:
        canonical_errors, canonical_facts = _canonical_scene_delta(head, current)
    except ValueError as error:
        result.errors.append(f"canonical scene scope could not be evaluated: {error}")
    else:
        result.errors.extend(canonical_errors)
        result.facts.update(canonical_facts)
    head_names, head_classes, head_renderers, _, _ = _scene_semantics(head)
    current_names, current_classes, current_renderers, _, v8_components = _scene_semantics(current)
    current_non_v8_names = Counter(
        {name: count for name, count in current_names.items()
         if name != "Runtime_Khufu_V8_Temple_Hub_Art" and not name.startswith("V8_")}
    )
    if current_non_v8_names != head_names:
        result.errors.append("scene scope changed the non-V8 GameObject name multiset")
    for class_id in set(head_classes) | set(current_classes) | set(v8_components):
        delta = current_classes[class_id] - head_classes[class_id]
        if delta != v8_components[class_id]:
            result.errors.append(
                f"scene component delta outside V8 ownership for class {class_id}: delta={delta}, v8={v8_components[class_id]}"
            )
    current_non_v8_renderers = Counter(
        {(name, enabled): count for (name, enabled), count in current_renderers.items()
         if name != "Runtime_Khufu_V8_Temple_Hub_Art" and not name.startswith("V8_")}
    )
    removed = head_renderers - current_non_v8_renderers
    added = current_non_v8_renderers - head_renderers
    removed_enabled = Counter({name: count for (name, enabled), count in removed.items() if enabled == 1})
    added_disabled = Counter({name: count for (name, enabled), count in added.items() if enabled == 0})
    unexpected_removed = sum(count for (_, enabled), count in removed.items() if enabled != 1)
    unexpected_added = sum(count for (_, enabled), count in added.items() if enabled != 0)
    if unexpected_removed or unexpected_added or sum(removed.values()) != 16 or sum(added.values()) != 16:
        result.errors.append("scene renderer state delta is not exactly sixteen enabled-to-disabled changes")
    if removed_enabled != added_disabled:
        result.errors.append("scene renderer state changes do not preserve the exact renderer-name multiset")
    if sum(count for name, count in removed_enabled.items() if name.startswith("V5_")) != 5 or \
       sum(count for name, count in removed_enabled.items() if name.startswith("V6_")) != 11:
        result.errors.append("scene renderer state delta is not V5=5 and V6=11")
    v8_renderers = sum(count for (name, enabled), count in current_renderers.items()
                       if (name.startswith("V8_") or name == "Runtime_Khufu_V8_Temple_Hub_Art") and enabled == 1)
    if v8_renderers != 10:
        result.errors.append(f"scene contains {v8_renderers} enabled V8 MeshRenderers, expected 10")
    result.facts["scene_scope_v5_disabled"] = sum(count for name, count in removed_enabled.items() if name.startswith("V5_"))
    result.facts["scene_scope_v6_disabled"] = sum(count for name, count in removed_enabled.items() if name.startswith("V6_"))
    result.facts["scene_scope_v8_renderers"] = v8_renderers
    result.facts["scene_scope_baseline_revision"] = SCENE_BASELINE_REVISION


def _check_staged(root: Path, result: ValidationResult) -> None:
    command = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"], cwd=root, check=True, capture_output=True
    )
    staged = [item for item in command.stdout.decode("utf-8").split("\0") if item]
    if not staged:
        result.errors.append("staged-scope check requested but index is empty")
        return
    disallowed = [path for path in staged if not _allowed_staged(path)]
    result.errors.extend(f"out-of-scope staged path: {path}" for path in disallowed)
    required = {SCENE.as_posix(), *[path.as_posix() for path in V8_SOURCES],
                "tools/validate_khufu_v8_temple_production_art.py"}
    missing = sorted(required.difference(staged))
    result.errors.extend(f"required V8 path not staged: {path}" for path in missing)
    result.facts["staged_files"] = len(staged)


def validate(root: Path, require_fable: bool, check_staged: bool) -> ValidationResult:
    result = ValidationResult()
    for relative, expected in FROZEN_INPUTS.items():
        path = root / relative
        if not path.is_file() or sha256(path) != expected:
            result.errors.append(f"frozen input drifted: {relative.as_posix()}")
    for relative in [SCENE, PLAYER, BUILT_LEVEL, *V8_SOURCES, *REQUIRED_DOCS]:
        if not (root / relative).is_file():
            result.errors.append(f"missing required file: {relative.as_posix()}")
    for relative, token in REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            result.errors.append(f"missing evidence: {relative.as_posix()}")
        elif token not in path.read_text(encoding="utf-8", errors="replace"):
            result.errors.append(f"evidence token missing in {relative.as_posix()}: {token}")

    if not (root / SCENE).is_file():
        return result
    scene_hash = sha256(root / SCENE)
    result.facts["scene_sha256"] = scene_hash
    _check_scene_scope(root, check_staged, result)
    for relative in [RUN_ROOT / "windows-build.md", Path("runs/khufu-v7-entry-wayfinding/v5-playmode-regression.md"), RUN_ROOT / "captures/manifest.md"]:
        path = root / relative
        if path.is_file():
            _bound_scene_hash(path.read_text(encoding="utf-8", errors="replace"), scene_hash, relative.as_posix(), result.errors)

    build_text = (root / RUN_ROOT / "windows-build.md").read_text(encoding="utf-8", errors="replace") if (root / RUN_ROOT / "windows-build.md").is_file() else ""
    player_match = re.search(r"Player executable SHA256: `([0-9a-f]{64})`", build_text)
    if player_match is None or not (root / PLAYER).is_file() or player_match.group(1) != sha256(root / PLAYER):
        result.errors.append("Windows build receipt is not bound to the current player")

    _check_binding(root, PLAYER_BINDING, "khufu-v8-player-proof-binding-v1", scene_hash, result)
    _check_binding(root, PERFORMANCE_BINDING, "khufu-v8-performance-binding-v1", scene_hash, result)
    _check_pngs(root, [
        RUN_ROOT / "captures/causeway_arrival.png",
        RUN_ROOT / "captures/court_wide.png",
        RUN_ROOT / "captures/court_to_pyramid.png",
        RUN_ROOT / "captures/temple_plan_oblique.png",
        RUN_ROOT / "captures/mutation_graybox_overlap.png",
        RUN_ROOT / "player-proof/v8-final-participant-temple.png",
        RUN_ROOT / "player-proof/v8-final-graybox-mutation.png",
        RUN_ROOT / "performance-final/v8-final-windows-player-initial.png",
        RUN_ROOT / "performance-final/v8-final-windows-player-operator.png",
    ], result)

    plan_text = (root / FABLE_PLAN).read_text(encoding="utf-8", errors="replace") if (root / FABLE_PLAN).is_file() else ""
    if "PLAN_CRITIQUE: proceed" not in plan_text:
        result.errors.append("Fable corrected plan did not proceed")
    if require_fable:
        if not (root / FABLE_FINAL).is_file():
            result.errors.append("missing Fable final review")
        else:
            _check_fable_text((root / FABLE_FINAL).read_text(encoding="utf-8", errors="replace"), result.errors)
    if check_staged:
        _check_staged(root, result)
    result.facts["frozen_inputs"] = len(FROZEN_INPUTS)
    result.facts["player_sha256"] = sha256(root / PLAYER) if (root / PLAYER).is_file() else "missing"
    return result


def write_report(path: Path, result: ValidationResult, require_fable: bool, check_staged: bool) -> None:
    lines = [
        "# Khufu V8 Aggregate Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
        f"- Fable required: `{require_fable}`",
        f"- Staged scope checked: `{check_staged}`",
        f"- Facts: `{json.dumps(result.facts, sort_keys=True)}`",
    ]
    lines.extend(f"- Failure: `{error}`" for error in result.errors)
    lines.extend(["", f"V8_AGGREGATE_VERDICT: {'passed' if result.passed else 'failed'}", ""])
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
        _write_binding(root, PLAYER_BINDING, "khufu-v8-player-proof-binding-v1", PLAYER_ARTIFACTS)
        _write_binding(root, PERFORMANCE_BINDING, "khufu-v8-performance-binding-v1", PERFORMANCE_ARTIFACTS)
    result = validate(root, args.require_fable, args.check_staged)
    write_report(root / args.output, result, args.require_fable, args.check_staged)
    print(f"V8_AGGREGATE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"FAIL: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
