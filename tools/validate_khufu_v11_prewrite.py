from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


DOC_ROOT = Path("docs/khufu-v11-royal-circuit")
CLASSIFICATION = DOC_ROOT / "segment-classification.json"
PERFORMANCE = DOC_ROOT / "performance-budget.json"
GOAL = DOC_ROOT / "GOAL.md"
RULES = DOC_ROOT / "RULES.md"
TEST_PLAN = DOC_ROOT / "TEST_PLAN.md"
ROUTE_SOURCE = Path("Assets/_Project/Scripts/Gameplay/KhufuV11RoyalRouteContract.cs")
TAG_SOURCE = Path("Assets/_Project/Scripts/Gameplay/KhufuV11SegmentTag.cs")
PIPELINE_SOURCE = Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitMeshPipeline.cs")
BUILDER_SOURCE = Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitBuilder.cs")
VALIDATOR_SOURCE = Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs")
SCREENSHOT_SOURCE = Path("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitScreenshotExporter.cs")
RUN_REPORT = Path("runs/khufu-v11-royal-circuit/prewrite-validation.md")
V11_SOURCE_FILES = (ROUTE_SOURCE, TAG_SOURCE, PIPELINE_SOURCE, BUILDER_SOURCE, VALIDATOR_SOURCE, SCREENSHOT_SOURCE)

FROZEN_V10_HASHES = {
    Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Limestone_Structure.asset"):
        "0d8f1bd4344e3308e2bd6cb881359400796ba8bdd5a2d410665b591ff4d04cd1",
    Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Limestone_Structure.asset.meta"):
        "4123715868c6fc596cc57b74227a6ee74a6d458927c0348a31879027a51d2e2f",
    Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Red_Granite_Boundary.asset"):
        "e75e0101e120748489d756012eeb846588143de8f64552566dc9eb308c4e5916",
    Path("Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Red_Granite_Boundary.asset.meta"):
        "492531fbb372dd5ec908a005f50e0b342805aba2abf6efd66147a2cd0fdc6161",
}

EXPECTED_SEGMENTS = {
    "Great_Step_Transition",
    "Royal_Entry_Passage",
    "Antechamber_Portcullis",
    "Kings_Chamber",
    "Granite_Sarcophagus",
    "Shaft_Mouth_Boundaries",
    "Stacked_Chamber_Display",
    "HYBRID_Royal_Route_Inlay",
}
EXPECTED_TRUTH = {"FACT", "FACT/HYBRID", "FACT/DISPLAY", "HYBRID"}


def validate_classification(data: dict) -> list[str]:
    failures: list[str] = []
    if data.get("schema_version") != 1:
        failures.append("classification schema version mismatch")
    segments = data.get("segments")
    if not isinstance(segments, list):
        return failures + ["classification segments are missing"]
    ids = [item.get("id") for item in segments]
    if len(ids) != len(set(ids)):
        failures.append("classification contains duplicate segment IDs")
    if set(ids) != EXPECTED_SEGMENTS:
        failures.append("classification segment set mismatch")
    for item in segments:
        if item.get("truth") not in EXPECTED_TRUTH:
            failures.append(f"unknown truth class: {item.get('id')}")
        if not isinstance(item.get("factual_shape"), bool) or not isinstance(item.get("gameplay_scale"), bool):
            failures.append(f"classification flags are invalid: {item.get('id')}")
        if not str(item.get("note", "")).strip():
            failures.append(f"classification note is missing: {item.get('id')}")
    by_id = {item.get("id"): item for item in segments}
    for display_id in ("Shaft_Mouth_Boundaries", "Stacked_Chamber_Display"):
        if by_id.get(display_id, {}).get("truth") != "FACT/DISPLAY":
            failures.append(f"display-only segment truth drifted: {display_id}")
    if by_id.get("HYBRID_Royal_Route_Inlay", {}).get("factual_shape") is not False:
        failures.append("hybrid route inlay claims a factual shape")
    return failures


def validate_performance(data: dict) -> list[str]:
    failures: list[str] = []
    if data.get("schema_version") != 1:
        failures.append("performance schema version mismatch")
    root = data.get("root", {})
    map_budget = data.get("map", {})
    captures = data.get("captures", {})
    if root.get("renderers_max") != 5:
        failures.append("root renderer budget must match five combined buckets")
    if root.get("colliders_max", 0) <= 0 or root.get("colliders_max", 0) > 66:
        failures.append("root collider budget is invalid")
    if map_budget.get("renderers_max", 0) < 829 or map_budget.get("colliders_max", 0) < 600:
        failures.append("map budget cannot contain the frozen V10 baseline plus V11")
    if captures != {"required": 6, "width": 1600, "height": 1000}:
        failures.append("capture budget mismatch")
    return failures


def validate_sources(root: Path) -> list[str]:
    failures: list[str] = []
    required_files = V11_SOURCE_FILES + tuple(Path(f"{path}.meta") for path in V11_SOURCE_FILES)
    for relative in required_files:
        if not (root / relative).is_file():
            failures.append(f"required V11 source is missing: {relative.as_posix()}")
    if failures:
        return failures

    failures.extend(validate_meta_guids(root))
    pipeline = (root / PIPELINE_SOURCE).read_text(encoding="utf-8")
    hash_constants = dict(re.findall(
        r'public const string (V10Closed\w+Sha256)\s*=\s*"([0-9a-f]{64})"\s*;', pipeline
    ))
    if set(hash_constants.values()) != set(FROZEN_V10_HASHES.values()):
        failures.append("frozen V10 hash constants do not match the accepted asset set")
    failures.extend(validate_frozen_v10_hashes(root))
    return failures


def validate_meta_guids(root: Path) -> list[str]:
    failures: list[str] = []
    guids: list[str] = []
    for source in V11_SOURCE_FILES:
        meta = root / Path(f"{source}.meta")
        if not meta.is_file():
            continue
        match = re.search(r"^guid: ([0-9a-f]{32})$", meta.read_text(encoding="utf-8"), re.MULTILINE)
        if not match:
            failures.append(f"V11 meta GUID is invalid: {meta.relative_to(root).as_posix()}")
            continue
        guids.append(match.group(1))
    if len(guids) != len(set(guids)):
        failures.append("V11 meta GUIDs are not unique")
    return failures


def validate_frozen_v10_hashes(root: Path) -> list[str]:
    failures: list[str] = []
    for relative, expected in FROZEN_V10_HASHES.items():
        path = root / relative
        if not path.is_file():
            failures.append(f"frozen V10 source is missing: {relative.as_posix()}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f"frozen V10 source hash drifted: {relative.as_posix()}")
    return failures


def validate(root: Path) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    required_docs = (CLASSIFICATION, PERFORMANCE, GOAL, RULES, TEST_PLAN)
    for relative in required_docs:
        if not (root / relative).is_file():
            failures.append(f"required V11 contract is missing: {relative.as_posix()}")
    if failures:
        return failures, {}

    classification = json.loads((root / CLASSIFICATION).read_text(encoding="utf-8"))
    performance = json.loads((root / PERFORMANCE).read_text(encoding="utf-8"))
    failures.extend(validate_classification(classification))
    failures.extend(validate_performance(performance))
    failures.extend(validate_sources(root))

    goal = (root / GOAL).read_text(encoding="utf-8")
    rules = (root / RULES).read_text(encoding="utf-8")
    tests = (root / TEST_PLAN).read_text(encoding="utf-8")
    for token in ("False-Completion Conditions", "V10 source meshes remain untouched", "Unity import"):
        if token not in goal:
            failures.append(f"goal completion token is missing: {token}")
    for token in ("display-only", "immutable inputs", "non-traversable"):
        if token not in rules:
            failures.append(f"rules truth token is missing: {token}")
    required_capture_names = (
        "great_step_open_axis.png",
        "antechamber_portcullis_detail.png",
        "kings_chamber_wide.png",
        "sarcophagus_and_shaft_boundary.png",
        "relieving_stack_cutaway.png",
        "pyramid_royal_circuit_integration.png",
    )
    for capture in required_capture_names:
        if capture not in tests:
            failures.append(f"required capture is missing from test plan: {capture}")

    metrics = {
        "segments": len(classification.get("segments", [])),
        "root_renderers_max": performance.get("root", {}).get("renderers_max", 0),
        "root_colliders_max": performance.get("root", {}).get("colliders_max", 0),
        "required_captures": performance.get("captures", {}).get("required", 0),
    }
    return failures, metrics


def write_report(root: Path, failures: list[str], metrics: dict[str, int]) -> None:
    path = root / RUN_REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    passed = not failures
    lines = [
        "# Khufu V11 Prewrite Validation",
        "",
        f"- Verdict: **{'passed' if passed else 'failed'}**",
        f"- Segments: `{metrics.get('segments', 0)}`",
        f"- Root renderer budget: `{metrics.get('root_renderers_max', 0)}`",
        f"- Root collider budget: `{metrics.get('root_colliders_max', 0)}`",
        f"- Required captures: `{metrics.get('required_captures', 0)}`",
    ]
    if failures:
        lines.extend(("", "## Failures"))
        lines.extend(f"- {failure}" for failure in failures)
    lines.extend(("", f"KHUFU_V11_PREWRITE: {'passed' if passed else 'failed'}", ""))
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    failures, metrics = validate(root)
    write_report(root, failures, metrics)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("KHUFU_V11_PREWRITE: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
