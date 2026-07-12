from __future__ import annotations

import copy
import json
from pathlib import Path

import tools.validate_khufu_v10_prewrite as validator


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_prewrite_contract_remains_valid() -> None:
    failures, metrics = validator.validate(ROOT, enforce_workspace_state=False)
    assert failures == []
    assert metrics["renderer_transitions"] == 60
    assert metrics["collider_transitions"] == 39


def test_manifest_rejects_crown_intersection() -> None:
    data = json.loads((ROOT / validator.MANIFEST).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["CrownIntersectionCount"] = 1
    failures = validator.validate_manifest(mutated, data["SceneSha256"])
    assert "disable manifest intersects Crown dependencies" in failures


def test_manifest_rejects_excluded_ownership_path() -> None:
    data = json.loads((ROOT / validator.MANIFEST).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["Transitions"][0]["Path"] = "Runtime_Pyramid_Reference_Matched_V4/V4_Queens_Chamber/Floor"
    failures = validator.validate_manifest(mutated, data["SceneSha256"])
    assert "disable manifest crosses an excluded ownership boundary" in failures


def test_classification_rejects_banned_runtime_vocabulary() -> None:
    data = json.loads((ROOT / validator.CLASSIFICATION).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["segments"][0]["note"] = "Playable Well Shaft"
    failures = validator.validate_classification(mutated)
    assert any("banned runtime vocabulary" in failure for failure in failures)


def test_classification_rejects_missing_segment() -> None:
    data = json.loads((ROOT / validator.CLASSIFICATION).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["segments"].pop()
    failures = validator.validate_classification(mutated)
    assert "classification segment set mismatch" in failures
