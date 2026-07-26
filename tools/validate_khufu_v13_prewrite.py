from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASELINE_COMMIT = "787476b58044e78f0c5164df408680e50fee47a2"
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
SCENE_SHA256 = "eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c"
V12_STATIC_SIGNATURE = "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd"
V12_ROOT_METRICS = {
    "renderers": 5,
    "vertices": 1176,
    "triangles": 588,
    "colliders": 22,
}
V12_MAP_METRICS = {
    "renderers": 834,
    "vertices": 67070,
    "triangles": 48560,
    "colliders": 589,
}

DOC_ROOT = Path("docs/khufu-v13-subterranean-threshold")
CLASSIFICATION = DOC_ROOT / "segment-classification.json"
PERFORMANCE = DOC_ROOT / "performance-budget.json"
REQUIRED_DOCS = (
    DOC_ROOT / "GOAL.md",
    DOC_ROOT / "PLAN.md",
    DOC_ROOT / "RESEARCH_BRIEF.md",
    DOC_ROOT / "RULES.md",
    DOC_ROOT / "STATUS.md",
    DOC_ROOT / "TEST_PLAN.md",
    CLASSIFICATION,
    PERFORMANCE,
)
DEFAULT_REPORT = Path("runs/khufu-v13-subterranean-threshold/prewrite-validation.md")
PHASE1_ALLOWED_PATHS = frozenset(
    {
        *(relative.as_posix() for relative in REQUIRED_DOCS),
        "tools/validate_khufu_v13_prewrite.py",
        "tools/tests/test_validate_khufu_v13_prewrite.py",
    }
)
PREWRITE_AUDIT_ALLOWED_PATHS = frozenset(
    {
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdAudit.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdAudit.cs.meta"
        ),
    }
)
PREWRITE_EVIDENCE_ALLOWED_PATHS = frozenset(
    {
        "runs/khufu-v13-subterranean-threshold/prewrite-audit.json",
        "runs/khufu-v13-subterranean-threshold/prewrite-audit.md",
        "runs/khufu-v13-subterranean-threshold/prewrite-validation.md",
    }
)
SOURCE_GATE_ALLOWED_PATHS = frozenset(
    {
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.cs.meta"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs.meta"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdValidator.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdValidator.cs.meta"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression.cs.meta"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter.cs"
        ),
        (
            "Assets/_Project/Scripts/Editor/"
            "ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter.cs.meta"
        ),
        "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13WindowsBuild.cs",
        "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13WindowsBuild.cs.meta",
        "Assets/_Project/Scripts/Gameplay/KhufuV13ControllerHitRecorder.cs",
        "Assets/_Project/Scripts/Gameplay/KhufuV13ControllerHitRecorder.cs.meta",
        "Assets/_Project/Scripts/Gameplay/KhufuV13SegmentTag.cs",
        "Assets/_Project/Scripts/Gameplay/KhufuV13SegmentTag.cs.meta",
        (
            "Assets/_Project/Scripts/Gameplay/"
            "KhufuV13SubterraneanRouteContract.cs"
        ),
        (
            "Assets/_Project/Scripts/Gameplay/"
            "KhufuV13SubterraneanRouteContract.cs.meta"
        ),
        (
            "Assets/_Project/Scripts/Gameplay/"
            "KhufuV13SubterraneanThresholdControl.cs"
        ),
        (
            "Assets/_Project/Scripts/Gameplay/"
            "KhufuV13SubterraneanThresholdControl.cs.meta"
        ),
        "Assets/_Project/Scripts/Gameplay/KhufuV13TraversalProofProbe.cs",
        "Assets/_Project/Scripts/Gameplay/KhufuV13TraversalProofProbe.cs.meta",
        "runs/khufu-v13-subterranean-threshold/phase3-source-validation.md",
        "runs/khufu-v13-subterranean-threshold/phase4-source-validation.md",
        "runs/khufu-v13-subterranean-threshold/phase5-source-validation.md",
    }
)
PREWRITE_COMMITTED_ALLOWED_PATHS = (
    PHASE1_ALLOWED_PATHS
    | PREWRITE_AUDIT_ALLOWED_PATHS
    | PREWRITE_EVIDENCE_ALLOWED_PATHS
    | SOURCE_GATE_ALLOWED_PATHS
)

EXPECTED_SEGMENTS = (
    ("V10_Branch_Transition", "FACT/HYBRID", False, True),
    ("Descending_Bedrock_Passage", "FACT/HYBRID", True, True),
    ("Subterranean_Level_Approach", "FACT/HYBRID", True, True),
    ("Subterranean_Chamber", "FACT/HYBRID", True, True),
    ("Unfinished_Pit_Boundary", "FACT/DISPLAY", True, False),
    ("HYBRID_Subterranean_Route_Inlay", "HYBRID", False, True),
)

V4_INTERIOR = (
    "Runtime_Pyramid_Reference_Matched_V4/"
    "V4_Embedded_Interior_Architecture/"
)
EXPECTED_TARGETS = (
    V4_INTERIOR + "V4_Descending_Bedrock_Floor",
    V4_INTERIOR + "V4_Descending_Bedrock_East",
    V4_INTERIOR + "V4_Descending_Bedrock_West",
    V4_INTERIOR + "V4_Descending_Bedrock_Roof",
    V4_INTERIOR + "V4_Subterranean_Level_Floor",
    V4_INTERIOR + "V4_Subterranean_Level_East",
    V4_INTERIOR + "V4_Subterranean_Level_West",
    V4_INTERIOR + "V4_Subterranean_Level_Roof",
    V4_INTERIOR + "V4_Subterranean_Chamber/V4_Subterranean_Floor",
    V4_INTERIOR + "V4_Subterranean_Chamber/V4_Subterranean_Back",
    V4_INTERIOR + "V4_Subterranean_Chamber/V4_Subterranean_West",
    V4_INTERIOR + "V4_Subterranean_Chamber/V4_Subterranean_East",
    V4_INTERIOR + "V4_Subterranean_Chamber/V4_Subterranean_Unfinished_Pit",
)

EXPECTED_OBSERVATIONS: tuple[dict[str, Any], ...] = (
    {
        "path": "Runtime_Khufu_V10_Interior_Spine/V10_Metadata/V10_Anchor_Ascending_Branch",
        "kind": "anchor",
        "owner": "V10",
        "position": [-2.5, 3.8, -19.2],
    },
    {
        "path": "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/V4_Route_Branch",
        "kind": "marker",
        "owner": "V10",
        "position": [-2.5, 1.2, -18.3],
        "renderer_enabled": False,
    },
    {
        "path": (
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/"
            "V4_Route_Subterranean_Approach"
        ),
        "kind": "marker",
        "owner": "V10",
        "position": [0.0, -3.8, -5.6],
        "renderer_enabled": False,
    },
    {
        "path": (
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/"
            "V4_Route_Subterranean_Chamber"
        ),
        "kind": "marker",
        "owner": "V10",
        "position": [1.0, -3.6, 1.5],
        "renderer_enabled": False,
    },
    {
        "path": (
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/"
            "V4_Glow_Descending"
        ),
        "kind": "glow",
        "owner": "V10",
        "renderer_enabled": False,
    },
    {
        "path": (
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/"
            "V4_Glow_Subterranean"
        ),
        "kind": "glow",
        "owner": "V10",
        "renderer_enabled": False,
    },
    {
        "path": (
            "Runtime_Pyramid_Reference_Matched_V4/V4_Lighting/"
            "V4_Light_Subterranean"
        ),
        "kind": "light",
        "owner": "V4-inherited",
        "light_enabled": True,
    },
)

EXPECTED_EXCLUSIONS = (
    "SCANPYRAMIDS_ANOMALIES",
    "SP_BV",
    "SP_NFC",
    "QUEEN_AND_ROYAL_CIRCUITS",
    "WELL_SHAFT_CLAIMS",
    "UNDERWORLD_FICTION",
    "EARTH_KEY_ROUTE",
    "GLOBAL_LIGHTING",
    "VFX",
    "PRODUCTION_AUDIO",
    "ENEMIES",
    "OBJECTIVES",
    "FRESH_PLAYER_USABILITY",
)

EXPECTED_BASELINE = {
    "commit": BASELINE_COMMIT,
    "scene_sha256": SCENE_SHA256,
    "v12_static_signature": V12_STATIC_SIGNATURE,
    "v12_root_metrics": V12_ROOT_METRICS,
    "v12_map_metrics": V12_MAP_METRICS,
}

EXPECTED_PERFORMANCE = {
    "schema": "khufu-v13-subterranean-threshold-budget-v1",
    "baseline_v12": {
        "static_signature": V12_STATIC_SIGNATURE,
        "root": V12_ROOT_METRICS,
        "map": V12_MAP_METRICS,
    },
    "root": {
        "renderers_exact": 5,
        "colliders_exact": 20,
        "colliders_max": 20,
        "vertices_max": 20000,
        "triangles_max": 10000,
    },
    "map": {
        "renderers_exact": 839,
        "colliders_exact": 609,
        "colliders_max": 612,
    },
    "captures": {
        "required": 6,
        "width": 1600,
        "height": 1000,
    },
}

DOC_TOKENS = {
    "GOAL.md": (
        "False Completion",
        "same-route return",
        "ScanPyramids",
    ),
    "PLAN.md": (
        "V10 branch",
        "Disable components only",
        "V4_Light_Subterranean",
    ),
    "RESEARCH_BRIEF.md": (
        "unfinished bedrock",
        "2.751 m",
        "Project Adaptation",
    ),
    "RULES.md": (
        BASELINE_COMMIT,
        SCENE_SHA256,
        V12_STATIC_SIGNATURE,
        "exactly five renderers and 20 non-trigger colliders",
    ),
    "STATUS.md": (
        "Phase 1",
        "Unity scene/assets: unchanged",
        "13 V4 targets",
    ),
    "TEST_PLAN.md": (
        "SetActive(false)",
        "v10_v13_junction.png",
        "alternate-index",
    ),
}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    facts: dict[str, str | int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(root: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout.strip()


def baseline_is_ancestor(root: Path) -> bool:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode not in (0, 1):
        raise subprocess.CalledProcessError(
            process.returncode,
            process.args,
            process.stdout,
            process.stderr,
        )
    return process.returncode == 0


def git_blob_sha256(root: Path, revision: str, relative: Path) -> str:
    process = subprocess.run(
        ["git", "show", f"{revision}:{relative.as_posix()}"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return hashlib.sha256(process.stdout).hexdigest()


def committed_paths_since_baseline(root: Path) -> set[str]:
    process = subprocess.run(
        ["git", "diff", "--name-only", f"{BASELINE_COMMIT}..HEAD", "--"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {line.strip() for line in process.stdout.splitlines() if line.strip()}


def unity_worktree_paths(root: Path) -> set[str]:
    process = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            "Assets/_Project",
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    records = process.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status = record[:2]
        paths.add(record[3:])
        if "R" in status or "C" in status:
            if index < len(records) and records[index]:
                paths.add(records[index])
                index += 1
    return paths


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exception:
        errors.append(f"invalid JSON {path.as_posix()}: {exception}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path.as_posix()}")
        return {}
    return value


def expected_target(path: str) -> dict[str, Any]:
    renderer_only = path.endswith("/V4_Subterranean_Unfinished_Pit")
    return {
        "path": path,
        "renderer_count": 1,
        "collider_count": 0 if renderer_only else 1,
        "active_self_before": True,
        "active_self_after": True,
        "renderer_enabled_before": True,
        "renderer_enabled_after": False,
        "collider_enabled_before": None if renderer_only else True,
        "collider_enabled_after": None if renderer_only else False,
    }


def validate_classification(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_root_keys = {
        "schema",
        "baseline",
        "segments",
        "ownership",
        "preserved_observations",
        "excluded_scope",
    }
    if set(data) != expected_root_keys:
        errors.append("classification root fields drifted")
    if data.get("schema") != "khufu-v13-subterranean-threshold-segments-v1":
        errors.append("segment classification schema drifted")

    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("classification baseline is missing")
    else:
        for field_name, expected in EXPECTED_BASELINE.items():
            if baseline.get(field_name) != expected:
                errors.append(f"classification baseline {field_name} drifted")
        if set(baseline) != set(EXPECTED_BASELINE):
            errors.append("classification baseline fields drifted")

    segments = data.get("segments")
    if not isinstance(segments, list):
        errors.append("segment classification records are missing")
    else:
        expected_ids = [item[0] for item in EXPECTED_SEGMENTS]
        ids = [item.get("id") if isinstance(item, dict) else None for item in segments]
        if ids != expected_ids:
            errors.append("segment classification set or order drifted")
        if all(isinstance(segment_id, str) for segment_id in ids) and len(ids) != len(set(ids)):
            errors.append("segment classification contains duplicate IDs")
        expected_by_id = {item[0]: item[1:] for item in EXPECTED_SEGMENTS}
        for item in segments:
            if not isinstance(item, dict):
                errors.append("segment classification record must be an object")
                continue
            segment_id = item.get("id")
            expected = expected_by_id.get(segment_id)
            if expected is None:
                continue
            truth, factual_shape, gameplay_scale = expected
            if item.get("truth") != truth:
                errors.append(f"segment truth drifted: {segment_id}")
            if item.get("factual_shape") is not factual_shape:
                errors.append(f"segment factual-shape flag drifted: {segment_id}")
            if item.get("gameplay_scale") is not gameplay_scale:
                errors.append(f"segment gameplay-scale flag drifted: {segment_id}")
            if not isinstance(item.get("note"), str) or not item["note"].strip():
                errors.append(f"segment note is missing: {segment_id}")
            if set(item) != {"id", "truth", "factual_shape", "gameplay_scale", "note"}:
                errors.append(f"segment fields drifted: {segment_id}")

    ownership = data.get("ownership")
    if not isinstance(ownership, dict):
        errors.append("V13 ownership contract is missing")
    else:
        if set(ownership) != {"transition_policy", "targets"}:
            errors.append("V13 ownership fields drifted")
        if ownership.get("transition_policy") != "component-disable-only":
            errors.append("V13 transition policy must remain component-disable-only")
        targets = ownership.get("targets")
        if not isinstance(targets, list) or len(targets) != 13:
            errors.append("V13 ownership must contain exactly 13 targets")
        else:
            paths = [item.get("path") if isinstance(item, dict) else None for item in targets]
            if paths != list(EXPECTED_TARGETS):
                errors.append("V13 ownership target set or order drifted")
            if all(isinstance(path, str) for path in paths) and len(paths) != len(set(paths)):
                errors.append("V13 ownership target paths are not unique")
            for index, path in enumerate(EXPECTED_TARGETS):
                actual = targets[index]
                expected = expected_target(path)
                if actual != expected:
                    errors.append(f"V13 ownership target state drifted: {path}")

    observations = data.get("preserved_observations")
    if not isinstance(observations, list) or len(observations) != len(EXPECTED_OBSERVATIONS):
        errors.append("preserved observation count drifted")
    else:
        paths = [item.get("path") if isinstance(item, dict) else None for item in observations]
        expected_paths = [item["path"] for item in EXPECTED_OBSERVATIONS]
        if paths != expected_paths:
            errors.append("preserved observation set or order drifted")
        for index, expected in enumerate(EXPECTED_OBSERVATIONS):
            if observations[index] != expected:
                errors.append(f"preserved observation drifted: {expected['path']}")

    exclusions = data.get("excluded_scope")
    if exclusions != list(EXPECTED_EXCLUSIONS):
        errors.append("V13 excluded scope drifted")
    return errors


def validate_performance(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != EXPECTED_PERFORMANCE["schema"]:
        errors.append("performance budget schema drifted")

    baseline = data.get("baseline_v12")
    expected_baseline = EXPECTED_PERFORMANCE["baseline_v12"]
    if not isinstance(baseline, dict):
        errors.append("V12 performance baseline is missing")
    else:
        if baseline.get("static_signature") != V12_STATIC_SIGNATURE:
            errors.append("V12 static signature budget binding drifted")
        if baseline.get("root") != V12_ROOT_METRICS:
            errors.append("V12 root metrics budget binding drifted")
        if baseline.get("map") != V12_MAP_METRICS:
            errors.append("V12 map metrics budget binding drifted")
        if baseline != expected_baseline:
            errors.append("V12 performance baseline fields drifted")

    root_budget = data.get("root")
    if not isinstance(root_budget, dict):
        errors.append("V13 root budget is missing")
    else:
        if root_budget.get("renderers_exact") != 5:
            errors.append("V13 root renderer contract must be exactly 5")
        if root_budget.get("colliders_exact") != 20:
            errors.append("V13 root collider contract must be exactly 20")
        if root_budget.get("colliders_max") != 20:
            errors.append("V13 root collider ceiling must remain 20")
        if root_budget != EXPECTED_PERFORMANCE["root"]:
            errors.append("V13 root budget fields drifted")

    map_budget = data.get("map")
    if not isinstance(map_budget, dict):
        errors.append("V13 map budget is missing")
    else:
        if map_budget.get("renderers_exact") != 839:
            errors.append("V13 map renderer contract must be exactly 839")
        if map_budget.get("colliders_exact") != 609:
            errors.append("V13 map collider contract must be exactly 609")
        if map_budget.get("colliders_max") != 612:
            errors.append("V13 map collider ceiling must remain 612")
        if map_budget != EXPECTED_PERFORMANCE["map"]:
            errors.append("V13 map budget fields drifted")

    if data.get("captures") != EXPECTED_PERFORMANCE["captures"]:
        errors.append("V13 capture budget drifted")
    if set(data) != set(EXPECTED_PERFORMANCE):
        errors.append("performance budget root fields drifted")
    return errors


def validate_documents(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_DOCS:
        if not (root / relative).is_file():
            errors.append(f"missing V13 contract file: {relative.name}")
    for name, tokens in DOC_TOKENS.items():
        path = root / DOC_ROOT / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exception:
            errors.append(f"invalid V13 document {name}: {exception}")
            continue
        for token in tokens:
            if token not in text:
                errors.append(f"required V13 document token missing from {name}: {token}")
    return errors


def validate(root: Path) -> Result:
    result = Result()
    try:
        git_head(root)
        ancestor_ok = baseline_is_ancestor(root)
        baseline_scene_hash = git_blob_sha256(root, BASELINE_COMMIT, SCENE)
        committed_paths = committed_paths_since_baseline(root)
        unity_paths = unity_worktree_paths(root)
    except (OSError, subprocess.CalledProcessError) as exception:
        ancestor_ok = False
        baseline_scene_hash = ""
        committed_paths = set()
        unity_paths = set()
        result.errors.append(f"cannot resolve prewrite Git state: {exception}")
    if not ancestor_ok:
        result.errors.append("V12 baseline is not an ancestor of HEAD")
    if baseline_scene_hash != SCENE_SHA256:
        result.errors.append("V12 baseline scene blob SHA256 drifted")
    unexpected_committed = sorted(
        committed_paths - PREWRITE_COMMITTED_ALLOWED_PATHS
    )
    if unexpected_committed:
        result.errors.append(
            "committed paths since V12 exceed the prewrite allowlist: "
            + ", ".join(unexpected_committed)
        )
    unexpected_unity = sorted(unity_paths - PREWRITE_AUDIT_ALLOWED_PATHS)
    if unexpected_unity:
        result.errors.append(
            "uncommitted Unity paths exceed the prewrite audit allowlist: "
            + ", ".join(unexpected_unity)
        )

    scene = root / SCENE
    scene_hash = sha256(scene) if scene.is_file() else ""
    if scene_hash != SCENE_SHA256:
        result.errors.append("baseline scene SHA256 drifted")

    result.errors.extend(validate_documents(root))
    classification = load_json(root / CLASSIFICATION, result.errors)
    performance = load_json(root / PERFORMANCE, result.errors)
    result.errors.extend(validate_classification(classification))
    result.errors.extend(validate_performance(performance))

    ownership = classification.get("ownership")
    targets = ownership.get("targets", []) if isinstance(ownership, dict) else []
    root_budget = performance.get("root")
    root_budget = root_budget if isinstance(root_budget, dict) else {}
    result.facts.update(
        {
            "baseline_commit": BASELINE_COMMIT,
            "scene_sha256": scene_hash,
            "v12_static_signature": V12_STATIC_SIGNATURE,
            "v12_map_renderers": V12_MAP_METRICS["renderers"],
            "v12_map_colliders": V12_MAP_METRICS["colliders"],
            "v13_ownership_targets": len(targets) if isinstance(targets, list) else 0,
            "v13_root_renderers": root_budget.get("renderers_exact", -1),
            "v13_root_colliders": root_budget.get("colliders_exact", -1),
        }
    )
    return result


def write_report(path: Path, result: Result) -> None:
    lines = [
        "# Khufu V13 Prewrite Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
    ]
    for key, value in sorted(result.facts.items()):
        lines.append(f"- {key}: `{value}`")
    for error in result.errors:
        lines.append(f"- Failure: `{error}`")
    lines.extend(
        (
            "",
            f"V13_PREWRITE_VERDICT: {'passed' if result.passed else 'failed'}",
            "",
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    result = validate(root)
    write_report(output, result)
    print(f"V13_PREWRITE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
