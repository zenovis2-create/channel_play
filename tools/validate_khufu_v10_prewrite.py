from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BASELINE_COMMIT = "a7ba20fd24034a0c5cf115d21d8d955797abe011"
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
DOC_ROOT = Path("docs/khufu-v10-interior-spine")
RUN_ROOT = Path("runs/khufu-v10-interior-spine")
MANIFEST = DOC_ROOT / "disable-manifest.json"
CLASSIFICATION = DOC_ROOT / "segment-classification.json"
FABLE_RECHECK = Path("work/fable-harness/khufu-v10-interior-spine-plan-recheck.fable.md")

REQUIRED_DOCS = (
    "GOAL.md",
    "PLAN.md",
    "RULES.md",
    "TEST_PLAN.md",
    "RESEARCH_BRIEF.md",
    "LOOP.md",
    "STATUS.md",
    "README.md",
    "performance-budget.json",
)

EXPECTED_SEGMENTS = {
    "North_Approach",
    "Entrance_To_Branch",
    "Branch_To_Gallery_Foot",
    "Grand_Gallery",
    "Queen_Branch_Threshold",
    "Great_Step_Boundary",
    "Historic_Service_Mouth",
    "HYBRID_Service_Return",
}

EXPECTED_MARKERS = {
    "V4_Route_Entrance": (-3.5, 5.0, -23.3),
    "V4_Route_Branch": (-2.5, 1.2, -18.3),
    "V4_Route_Subterranean_Approach": (0.0, -3.8, -5.6),
    "V4_Route_Subterranean_Chamber": (1.0, -3.6, 1.5),
    "V4_Route_Gallery_Foot": (0.0, 5.4, -7.0),
    "V4_Route_Queens_Chamber": (-1.8, 5.35, -2.8),
    "V4_Route_Grand_Gallery_Top": (3.5, 10.5, 4.5),
    "V4_Route_Kings_Chamber": (-2.0, 12.45, 7.5),
}

FORBIDDEN_TRANSITION_TOKENS = (
    "V5_KeyRoute_Crown",
    "V5_Critical_Route",
    "V4_Descending_Bedrock",
    "V4_Subterranean_Level",
    "V4_Queens_Horizontal",
    "V4_Subterranean_Chamber",
    "V4_Queens_Chamber",
    "V4_Kings_Embedded_Suite",
    "V4_Antechamber",
    "V4_Portcullis",
    "V4_Relieving",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_classification(data: dict) -> list[str]:
    failures: list[str] = []
    if data.get("schema") != "khufu-v10-interior-segment-classification-v1":
        failures.append("classification schema mismatch")
    if data.get("baseline_commit") != BASELINE_COMMIT:
        failures.append("classification baseline mismatch")
    clearance = data.get("clearance", {})
    if clearance.get("width_m") != 1.8 or clearance.get("height_m") != 2.2:
        failures.append("classification clearance contract mismatch")
    segments = data.get("segments", [])
    ids = [segment.get("id") for segment in segments]
    if set(ids) != EXPECTED_SEGMENTS or len(ids) != len(EXPECTED_SEGMENTS):
        failures.append("classification segment set mismatch")
    if len(ids) != len(set(ids)):
        failures.append("classification contains duplicate segment ids")
    for segment in segments:
        if segment.get("truth") not in {"FACT", "HYBRID"}:
            failures.append(f"invalid truth class: {segment.get('id')}")
        serialized = json.dumps(segment, ensure_ascii=True).lower()
        if "well shaft" in serialized:
            failures.append(f"banned runtime vocabulary in segment: {segment.get('id')}")
    return failures


def _vector(record: dict) -> tuple[float, float, float]:
    value = record.get("Position", {})
    return (float(value.get("x", 0.0)), float(value.get("y", 0.0)), float(value.get("z", 0.0)))


def validate_manifest(data: dict, scene_hash: str) -> list[str]:
    failures: list[str] = []
    if data.get("Schema") != "khufu-v10-interior-disable-manifest-v1":
        failures.append("disable manifest schema mismatch")
    if data.get("BaselineCommit") != BASELINE_COMMIT:
        failures.append("disable manifest baseline mismatch")
    if data.get("ScenePath") != SCENE.as_posix():
        failures.append("disable manifest scene path mismatch")
    if data.get("SceneSha256") != scene_hash:
        failures.append("disable manifest scene hash is stale")
    transitions = data.get("Transitions", [])
    paths = [item.get("Path") for item in transitions]
    if data.get("ExpectedRendererTransitions") != 45 or len(transitions) != 45:
        failures.append("disable manifest renderer count mismatch")
    collider_count = sum(bool(item.get("DisableCollider")) for item in transitions)
    if data.get("ExpectedColliderTransitions") != 39 or collider_count != 39:
        failures.append("disable manifest collider count mismatch")
    if len(paths) != len(set(paths)) or paths != sorted(paths):
        failures.append("disable manifest paths are not unique and sorted")
    if any(not item.get("DisableRenderer") for item in transitions):
        failures.append("disable manifest contains a non-renderer transition")
    if any(token in path for path in paths for token in FORBIDDEN_TRANSITION_TOKENS):
        failures.append("disable manifest crosses an excluded ownership boundary")
    if data.get("CrownIntersectionCount") != 0:
        failures.append("disable manifest intersects Crown dependencies")
    if data.get("CrownDependencyCount", 0) <= 0:
        failures.append("disable manifest Crown dependency inventory is empty")
    markers = data.get("Markers", [])
    marker_map = {item.get("Name"): _vector(item) for item in markers}
    if set(marker_map) != set(EXPECTED_MARKERS):
        failures.append("disable manifest marker set mismatch")
    for name, expected in EXPECTED_MARKERS.items():
        actual = marker_map.get(name)
        if actual is None or any(abs(left - right) > 0.001 for left, right in zip(actual, expected)):
            failures.append(f"disable manifest marker drift: {name}")
    return failures


def git_output(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def validate(root: Path) -> tuple[list[str], dict[str, str | int]]:
    failures: list[str] = []
    for name in REQUIRED_DOCS:
        path = root / DOC_ROOT / name
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"required document missing or empty: {path.relative_to(root)}")
    for path in (root / MANIFEST, root / CLASSIFICATION, root / FABLE_RECHECK,
                 root / RUN_ROOT / "audit.json", root / RUN_ROOT / "audit.md"):
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"required pre-write artifact missing or empty: {path.relative_to(root)}")
    if failures:
        return failures, {}

    scene_hash = sha256(root / SCENE)
    failures.extend(validate_classification(load_json(root / CLASSIFICATION)))
    failures.extend(validate_manifest(load_json(root / MANIFEST), scene_hash))

    audit_text = (root / RUN_ROOT / "audit.md").read_text(encoding="utf-8")
    if "KHUFU_V10_PREWRITE_AUDIT: passed" not in audit_text:
        failures.append("Unity pre-write audit pass token missing")
    fable_text = (root / FABLE_RECHECK).read_text(encoding="utf-8")
    if "FABLE_HARNESS_ERROR" in fable_text or "FABLE_PLAN_VERDICT: proceed" not in fable_text:
        failures.append("external Fable proceed verdict missing or invalid")

    head = git_output(root, "rev-parse", "HEAD")
    if head != BASELINE_COMMIT:
        failures.append(f"pre-write HEAD mismatch: {head}")
    scene_drift = git_output(root, "diff", "--name-only", "--", SCENE.as_posix())
    if scene_drift:
        failures.append("scene changed before the pre-write contract commit")

    metrics: dict[str, str | int] = {
        "baseline_commit": head,
        "scene_sha256": scene_hash,
        "renderer_transitions": 45,
        "collider_transitions": 39,
        "crown_intersection": 0,
        "segments": len(EXPECTED_SEGMENTS),
        "markers": len(EXPECTED_MARKERS),
    }
    return failures, metrics


def write_report(path: Path, failures: list[str], metrics: dict[str, str | int]) -> None:
    lines = ["# Khufu V10 Pre-Write Validation", "", f"- Verdict: **{'passed' if not failures else 'failed'}**"]
    for key, value in metrics.items():
        lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")
    for failure in failures:
        lines.append(f"- Failure: `{failure}`")
    lines.extend(["", f"KHUFU_V10_PREWRITE_VALIDATION: {'passed' if not failures else 'failed'}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    failures, metrics = validate(root)
    output = args.output if args.output.is_absolute() else root / args.output
    write_report(output, failures, metrics)
    print(f"KHUFU_V10_PREWRITE_VALIDATION: {'passed' if not failures else 'failed'}")
    for failure in failures:
        print(f"- {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
