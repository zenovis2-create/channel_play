from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_khufu_v7_entry_wayfinding as validator


def test_stale_scene_receipt_is_rejected() -> None:
    errors: list[str] = []
    stale = "a" * 64
    current = "b" * 64
    validator._bound_scene_hash(f"- Scene SHA256: `{stale}`", current, "test receipt", errors)
    assert errors == [f"test receipt is bound to stale scene {stale}, expected {current}"]


def test_off_route_mutation_requires_observed_placement_failure() -> None:
    errors: list[str] = []
    validator._check_off_route_text(
        "V7_OFF_ROUTE_MUTATION: passed\nV7_Entry_Guide_01 + 3m on world Z\n",
        errors,
    )
    assert any("Guide placement mismatch" in error for error in errors)


def test_entry_receipts_accept_normal_and_reject_mutated_blocker() -> None:
    normal = """
Harness verdict: **passed**
Entry proof: `passed`
Mutation enabled: `False`
Active Valley Gate pylons: `1`
Visible candidate occluders: `0`
Look-ahead offset: `-7.000,0.000,0.000`
Player in frame: `True`
Guides in viewport: `2`
Center environment hit: `V5_Route_Segment_24_Floor`
Route center clear: `True`
V7_ENTRY_PROOF: passed
"""
    mutation = """
Harness verdict: **passed**
Entry proof: `failed-as-expected`
Mutation enabled: `True`
Active Valley Gate pylons: `0`
Center environment hit: `V5_Valley_Gate_Pylon_-1_MUTATED_BLOCKING_CONTROL`
Route center clear: `False`
V7_BLOCKED_PYLON_MUTATION: passed
"""
    errors: list[str] = []
    validator._check_entry_receipt_text(normal, mutation, errors)
    assert errors == []


def test_entry_receipt_rejects_false_done_route_center() -> None:
    normal = """
Harness verdict: **passed**
Entry proof: `passed`
Mutation enabled: `False`
Active Valley Gate pylons: `1`
Visible candidate occluders: `0`
Look-ahead offset: `-7.000,0.000,0.000`
Player in frame: `True`
Guides in viewport: `2`
Center environment hit: `V5_Valley_Gate_Pylon_1`
Route center clear: `True`
V7_ENTRY_PROOF: passed
"""
    errors: list[str] = []
    validator._check_entry_receipt_text(normal, "", errors)
    assert any("center is not a route surface" in error for error in errors)


def test_binding_rejects_hash_mutation(tmp_path: Path) -> None:
    scene = tmp_path / validator.SCENE
    scene.parent.mkdir(parents=True)
    scene.write_text("scene", encoding="utf-8")
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("evidence", encoding="utf-8")
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "test-schema",
                "verdict": "passed",
                "scene": {
                    "path": validator.SCENE.as_posix(),
                    "bytes": scene.stat().st_size,
                    "sha256": validator.sha256(scene),
                },
                "player": {
                    "path": "artifact.txt",
                    "bytes": artifact.stat().st_size,
                    "sha256": "0" * 64,
                },
                "built_level": {
                    "path": "artifact.txt",
                    "bytes": artifact.stat().st_size,
                    "sha256": validator.sha256(artifact),
                },
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    result = validator.ValidationResult()
    validator._check_binding(tmp_path, Path("binding.json"), "test-schema", validator.sha256(scene), result)
    assert any("binding hash mismatch: artifact.txt" in error for error in result.errors)


def test_fable_requires_exactly_one_ship_decision() -> None:
    errors: list[str] = []
    validator._check_fable_text("FINAL_REVIEW: ship\nFINAL_REVIEW: ship\n", errors)
    assert errors == ["Fable final review has 2 ship decisions, expected exactly one"]
