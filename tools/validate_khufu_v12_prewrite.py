from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


BASELINE_COMMIT = "1dd7156b064a99eaa2d19ccca0ae605befae54fd"
SCENE = Path("Assets/_Project/Scenes/School_MVP.unity")
SCENE_SHA256 = "dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b"
DOC_ROOT = Path("docs/khufu-v12-queen-circuit")
AUDIT = Path("runs/khufu-v12-queen-circuit/prewrite-audit.json")
V11_SIGNATURE = "9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9"
V11_ASSETS = {
    "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit/KhufuV11_V10_Limestone_Open.asset":
        "1ae211817170a9ae846853b6313c4bdb1277553b7bcd6bc7f30760762a980e67",
    "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit/KhufuV11_V10_Limestone_Open.asset.meta":
        "2a579b2efd062b16370fe7e5a6f1aedc233fbd057b67de7c9a9fb8d3c8d2dd6c",
    "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit/KhufuV11_V10_Red_Granite_Open.asset":
        "1c2cca3af61aaf68e003f813274fd5890d9a88078147e2cd8abb5012481f7d02",
    "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit/KhufuV11_V10_Red_Granite_Open.asset.meta":
        "4aa71b58e1cdccdc27409da5149aa936095be87c247fb9c5163205cafe652bda",
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


def load_json(path: Path, result: Result) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exception:
        result.errors.append(f"invalid JSON {path.as_posix()}: {exception}")
        return {}
    if not isinstance(value, dict):
        result.errors.append(f"JSON root must be an object: {path.as_posix()}")
        return {}
    return value


def validate(root: Path) -> Result:
    result = Result()
    head = git_head(root)
    if head != BASELINE_COMMIT:
        result.errors.append(f"baseline HEAD drifted: {head}")

    scene = root / SCENE
    if not scene.is_file() or sha256(scene) != SCENE_SHA256:
        result.errors.append("baseline scene SHA256 drifted")

    required_docs = (
        "GOAL.md",
        "RULES.md",
        "RESEARCH_BRIEF.md",
        "PLAN.md",
        "TEST_PLAN.md",
        "STATUS.md",
        "segment-classification.json",
        "performance-budget.json",
    )
    for name in required_docs:
        if not (root / DOC_ROOT / name).is_file():
            result.errors.append(f"missing V12 contract file: {name}")

    classification = load_json(root / DOC_ROOT / "segment-classification.json", result)
    segments = classification.get("segments", [])
    if classification.get("schema") != "khufu-v12-queen-circuit-segments-v1":
        result.errors.append("segment classification schema drifted")
    if not isinstance(segments, list) or len(segments) != 6:
        result.errors.append("segment classification must contain exactly 6 records")
    elif any("Queens_Shaft" in str(item) for item in segments):
        result.errors.append("segment classification uses forbidden Queens_Shaft token")

    budget = load_json(root / DOC_ROOT / "performance-budget.json", result)
    if budget.get("schema") != "khufu-v12-queen-circuit-budget-v1":
        result.errors.append("performance budget schema drifted")
    if budget.get("root", {}).get("renderers_exact") != 5:
        result.errors.append("V12 root renderer contract must be exactly 5")
    if budget.get("root", {}).get("colliders_exact") != 22:
        result.errors.append("V12 root collider contract must be exactly 22")
    if budget.get("root", {}).get("colliders_max") != 33:
        result.errors.append("V12 collider ceiling must be frozen at 33")
    if budget.get("map", {}).get("renderers_exact") != 834:
        result.errors.append("map renderer contract must be exactly 834")
    if budget.get("map", {}).get("colliders_exact") != 589:
        result.errors.append("map collider contract must be exactly 589")
    if budget.get("map", {}).get("colliders_max") != 600:
        result.errors.append("map collider ceiling must remain 600")

    for relative, expected in V11_ASSETS.items():
        target = root / relative
        if not target.is_file() or sha256(target) != expected:
            result.errors.append(f"frozen V11-open asset drifted: {relative}")

    audit = load_json(root / AUDIT, result)
    if audit.get("schema") != "khufu-v12-prewrite-audit-v1":
        result.errors.append("prewrite audit schema drifted")
    if audit.get("scene_sha256") != SCENE_SHA256 or audit.get("scene_unchanged") is not True:
        result.errors.append("prewrite audit does not bind unchanged baseline scene bytes")
    targets = audit.get("v4_queen_targets", [])
    if audit.get("v4_queen_target_count") != 10 or not isinstance(targets, list) or len(targets) != 10:
        result.errors.append("prewrite audit must contain exactly 10 V4 Queen targets")
    elif any(
        item.get("active_self") is not True
        or item.get("active_in_hierarchy") is not True
        or item.get("renderer_count") != 1
        or item.get("collider_count") != 1
        or item.get("renderer_enabled") is not True
        or item.get("collider_enabled") is not True
        or item.get("is_trigger") is not False
        or not isinstance(item.get("local_position"), dict)
        or not isinstance(item.get("local_rotation"), dict)
        or not isinstance(item.get("local_scale"), dict)
        for item in targets
    ):
        result.errors.append("V4 Queen target baseline state drifted")
    elif len({item.get("path") for item in targets}) != 10:
        result.errors.append("V4 Queen target paths must be unique")
    if audit.get("v10_queen_gate_spec_count") != 1:
        result.errors.append("V10 Queen gate spec count drifted")
    if audit.get("v10_queen_gate_proxy_enabled") is not True:
        result.errors.append("V10 Queen gate proxy is not enabled at baseline")
    if audit.get("v10_great_step_proxy_enabled") is not False:
        result.errors.append("V10 Great Step proxy is not V11-open at baseline")
    threshold_proxies = audit.get("threshold_proxies", [])
    if not isinstance(threshold_proxies, list) or len(threshold_proxies) != 3:
        result.errors.append("prewrite audit must contain exactly 3 threshold proxies")
    elif any(
        item.get("active_self") is not True
        or item.get("active_in_hierarchy") is not True
        or item.get("collider_count") != 1
        or item.get("collider_enabled") is not True
        or item.get("is_trigger") is not False
        for item in threshold_proxies
    ):
        result.errors.append("V10 threshold proxy baseline state drifted")
    elif len({item.get("path") for item in threshold_proxies}) != 3:
        result.errors.append("V10 threshold proxy paths must be unique")
    marker_position = audit.get("marker_position", {})
    if (
        not isinstance(marker_position, dict)
        or abs(marker_position.get("x", 999.0) - -1.8) > 0.001
        or abs(marker_position.get("y", 999.0) - 5.35) > 0.001
        or abs(marker_position.get("z", 999.0) - -2.8) > 0.001
    ):
        result.errors.append("V4 Queen marker position drifted")
    if audit.get("marker_renderer_enabled") is not False or audit.get("glow_renderer_enabled") is not False:
        result.errors.append("V10-owned Queen marker/glow renderers are not disabled")
    if audit.get("inherited_light_enabled") is not True:
        result.errors.append("inherited V4 Queen light is not enabled")
    if audit.get("v11_signature") != V11_SIGNATURE:
        result.errors.append("V11 baseline signature drifted")
    metrics = audit.get("map_metrics", {})
    if metrics.get("renderers") != 829 or metrics.get("colliders") != 567:
        result.errors.append("baseline map component metrics drifted")

    result.facts.update(
        {
            "baseline_commit": head,
            "scene_sha256": sha256(scene) if scene.is_file() else "",
            "v4_queen_targets": len(targets) if isinstance(targets, list) else 0,
            "map_renderers": metrics.get("renderers", -1),
            "map_colliders": metrics.get("colliders", -1),
        }
    )
    return result


def write_report(path: Path, result: Result) -> None:
    lines = [
        "# Khufu V12 Prewrite Validation",
        "",
        f"- Verdict: **{'passed' if result.passed else 'failed'}**",
    ]
    for key, value in sorted(result.facts.items()):
        lines.append(f"- {key}: `{value}`")
    for error in result.errors:
        lines.append(f"- Failure: `{error}`")
    lines.extend(("", f"V12_PREWRITE_VERDICT: {'passed' if result.passed else 'failed'}", ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/khufu-v12-queen-circuit/prewrite-validation.md"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    result = validate(root)
    write_report(output, result)
    print(f"V12_PREWRITE_VERDICT: {'passed' if result.passed else 'failed'}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
