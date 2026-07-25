from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil

import tools.validate_khufu_v11_prewrite as validator


ROOT = Path(__file__).resolve().parents[2]


def test_v11_prewrite_contract_is_valid() -> None:
    failures, metrics = validator.validate(ROOT)
    assert failures == []
    assert metrics == {
        "segments": 8,
        "root_renderers_max": 5,
        "root_colliders_max": 66,
        "required_captures": 6,
    }


def test_classification_rejects_missing_segment() -> None:
    data = json.loads((ROOT / validator.CLASSIFICATION).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["segments"].pop()
    assert "classification segment set mismatch" in validator.validate_classification(mutated)


def test_display_segments_cannot_be_promoted_to_fact() -> None:
    data = json.loads((ROOT / validator.CLASSIFICATION).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    next(item for item in mutated["segments"] if item["id"] == "Stacked_Chamber_Display")["truth"] = "FACT"
    assert "display-only segment truth drifted: Stacked_Chamber_Display" in validator.validate_classification(mutated)


def test_hybrid_inlay_cannot_claim_factual_shape() -> None:
    data = json.loads((ROOT / validator.CLASSIFICATION).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    next(item for item in mutated["segments"] if item["id"] == "HYBRID_Royal_Route_Inlay")["factual_shape"] = True
    assert "hybrid route inlay claims a factual shape" in validator.validate_classification(mutated)


def test_performance_rejects_budget_below_v11_map_surface() -> None:
    data = json.loads((ROOT / validator.PERFORMANCE).read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["map"]["renderers_max"] = 828
    assert "map budget cannot contain the frozen V10 baseline plus V11" in validator.validate_performance(mutated)


def test_frozen_v10_hashes_match_accepted_assets() -> None:
    assert validator.validate_frozen_v10_hashes(ROOT) == []


def test_frozen_v10_hash_gate_rejects_content_mutation(tmp_path: Path) -> None:
    for relative in validator.FROZEN_V10_HASHES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    mutated = next(iter(validator.FROZEN_V10_HASHES))
    with (tmp_path / mutated).open("ab") as stream:
        stream.write(b"drift")
    failures = validator.validate_frozen_v10_hashes(tmp_path)
    assert f"frozen V10 source hash drifted: {mutated.as_posix()}" in failures


def test_all_v11_unity_sources_have_committed_meta_files() -> None:
    failures = validator.validate_sources(ROOT)
    assert not [failure for failure in failures if "required V11 source is missing" in failure]


def test_v11_meta_guids_are_valid_and_unique() -> None:
    assert validator.validate_meta_guids(ROOT) == []
