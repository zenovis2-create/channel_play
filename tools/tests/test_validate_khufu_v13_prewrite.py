from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess

import pytest

import tools.validate_khufu_v13_prewrite as prewrite


ROOT = Path(__file__).resolve().parents[2]
DESCENDANT_HEAD = "f" * 40


def load_classification() -> dict:
    return json.loads((ROOT / prewrite.CLASSIFICATION).read_text(encoding="utf-8"))


def load_performance() -> dict:
    return json.loads((ROOT / prewrite.PERFORMANCE).read_text(encoding="utf-8"))


def target(data: dict, suffix: str) -> dict:
    return next(
        item
        for item in data["ownership"]["targets"]
        if item["path"].endswith(suffix)
    )


def observation(data: dict, suffix: str) -> dict:
    return next(
        item
        for item in data["preserved_observations"]
        if item["path"].endswith(suffix)
    )


def contract_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / prewrite.DOC_ROOT, tmp_path / prewrite.DOC_ROOT)
    scene = tmp_path / prewrite.SCENE
    scene.parent.mkdir(parents=True)
    process = subprocess.run(
        [
            "git",
            "show",
            f"{prewrite.BASELINE_COMMIT}:{prewrite.SCENE.as_posix()}",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    scene.write_bytes(process.stdout)
    return tmp_path


def stub_git(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ancestor: bool = True,
    baseline_scene_hash: str = prewrite.SCENE_SHA256,
    committed_paths: set[str] | None = None,
    unity_paths: set[str] | None = None,
) -> None:
    monkeypatch.setattr(prewrite, "git_head", lambda _root: DESCENDANT_HEAD)
    monkeypatch.setattr(prewrite, "baseline_is_ancestor", lambda _root: ancestor)
    monkeypatch.setattr(
        prewrite,
        "git_blob_sha256",
        lambda _root, _revision, _relative: baseline_scene_hash,
    )
    monkeypatch.setattr(
        prewrite,
        "committed_paths_since_baseline",
        lambda _root: (
            set(prewrite.PREWRITE_COMMITTED_ALLOWED_PATHS)
            if committed_paths is None
            else committed_paths
        ),
    )
    monkeypatch.setattr(
        prewrite,
        "unity_worktree_paths",
        lambda _root: set() if unity_paths is None else unity_paths,
    )


def test_complete_v13_prewrite_contract_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = contract_root(tmp_path)
    stub_git(monkeypatch)
    result = prewrite.validate(root)
    assert result.errors == []
    assert result.facts == {
        "baseline_commit": prewrite.BASELINE_COMMIT,
        "head_commit": DESCENDANT_HEAD,
        "scene_sha256": prewrite.SCENE_SHA256,
        "v12_static_signature": prewrite.V12_STATIC_SIGNATURE,
        "v12_map_renderers": 834,
        "v12_map_colliders": 589,
        "v13_ownership_targets": 13,
        "v13_root_renderers": 5,
        "v13_root_colliders": 20,
    }


def test_non_ancestor_head_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = contract_root(tmp_path)
    stub_git(monkeypatch, ancestor=False)
    result = prewrite.validate(root)
    assert "V12 baseline is not an ancestor of HEAD" in result.errors


def test_scene_byte_mutation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shutil.copytree(ROOT / prewrite.DOC_ROOT, tmp_path / prewrite.DOC_ROOT)
    scene = tmp_path / prewrite.SCENE
    scene.parent.mkdir(parents=True)
    scene.write_text("mutated scene\n", encoding="utf-8")
    stub_git(monkeypatch)
    result = prewrite.validate(tmp_path)
    assert "baseline scene SHA256 drifted" in result.errors


def test_baseline_scene_blob_mutation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = contract_root(tmp_path)
    stub_git(monkeypatch, baseline_scene_hash="0" * 64)
    result = prewrite.validate(root)
    assert "V12 baseline scene blob SHA256 drifted" in result.errors


def test_disallowed_committed_path_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = contract_root(tmp_path)
    stub_git(monkeypatch, committed_paths={prewrite.SCENE.as_posix()})
    result = prewrite.validate(root)
    assert any("exceed the prewrite allowlist" in error for error in result.errors)


def test_disallowed_uncommitted_unity_path_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = contract_root(tmp_path)
    stub_git(
        monkeypatch,
        unity_paths={"Assets/_Project/Materials/Unexpected.mat"},
    )
    result = prewrite.validate(root)
    assert any(
        "exceed the prewrite audit allowlist" in error
        for error in result.errors
    )


def test_v12_signature_mutation_fails() -> None:
    data = load_classification()
    data["baseline"]["v12_static_signature"] = "0" * 64
    errors = prewrite.validate_classification(data)
    assert "classification baseline v12_static_signature drifted" in errors


def test_v12_map_metric_mutation_fails() -> None:
    data = load_performance()
    data["baseline_v12"]["map"]["colliders"] = 588
    errors = prewrite.validate_performance(data)
    assert "V12 map metrics budget binding drifted" in errors


def test_target_count_mutation_fails() -> None:
    data = load_classification()
    data["ownership"]["targets"].pop()
    errors = prewrite.validate_classification(data)
    assert "V13 ownership must contain exactly 13 targets" in errors


def test_target_path_mutation_fails() -> None:
    data = load_classification()
    data["ownership"]["targets"][0]["path"] += "_drift"
    errors = prewrite.validate_classification(data)
    assert "V13 ownership target set or order drifted" in errors


def test_set_active_mutation_fails() -> None:
    data = load_classification()
    target(data, "V4_Descending_Bedrock_Floor")["active_self_after"] = False
    errors = prewrite.validate_classification(data)
    assert any("ownership target state drifted" in error for error in errors)


def test_renderer_reenable_mutation_fails() -> None:
    data = load_classification()
    target(data, "V4_Subterranean_Level_Roof")["renderer_enabled_after"] = True
    errors = prewrite.validate_classification(data)
    assert any("ownership target state drifted" in error for error in errors)


def test_collider_pair_mutation_fails() -> None:
    data = load_classification()
    target(data, "V4_Subterranean_East")["collider_enabled_after"] = True
    errors = prewrite.validate_classification(data)
    assert any("ownership target state drifted" in error for error in errors)


def test_renderer_only_pit_cannot_gain_collider() -> None:
    data = load_classification()
    pit = target(data, "V4_Subterranean_Unfinished_Pit")
    pit["collider_count"] = 1
    pit["collider_enabled_before"] = True
    errors = prewrite.validate_classification(data)
    assert any("ownership target state drifted" in error for error in errors)


def test_marker_position_mutation_fails() -> None:
    data = load_classification()
    observation(data, "V4_Route_Subterranean_Chamber")["position"][0] = 0.9
    errors = prewrite.validate_classification(data)
    assert any("preserved observation drifted" in error for error in errors)


def test_v10_owned_glow_reenable_mutation_fails() -> None:
    data = load_classification()
    observation(data, "V4_Glow_Subterranean")["renderer_enabled"] = True
    errors = prewrite.validate_classification(data)
    assert any("preserved observation drifted" in error for error in errors)


def test_inherited_light_disable_mutation_fails() -> None:
    data = load_classification()
    observation(data, "V4_Light_Subterranean")["light_enabled"] = False
    errors = prewrite.validate_classification(data)
    assert any("preserved observation drifted" in error for error in errors)


def test_exclusion_mutation_fails() -> None:
    data = load_classification()
    data["excluded_scope"].remove("SCANPYRAMIDS_ANOMALIES")
    errors = prewrite.validate_classification(data)
    assert "V13 excluded scope drifted" in errors


def test_truth_class_mutation_fails() -> None:
    data = load_classification()
    next(
        item
        for item in data["segments"]
        if item["id"] == "Unfinished_Pit_Boundary"
    )["truth"] = "FACT"
    errors = prewrite.validate_classification(data)
    assert "segment truth drifted: Unfinished_Pit_Boundary" in errors


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("renderers_exact", 6, "V13 root renderer contract must be exactly 5"),
        ("colliders_exact", 19, "V13 root collider contract must be exactly 20"),
        ("colliders_max", 21, "V13 root collider ceiling must remain 20"),
    ),
)
def test_root_budget_mutations_fail(
    field: str,
    value: int,
    message: str,
) -> None:
    data = load_performance()
    data["root"][field] = value
    errors = prewrite.validate_performance(data)
    assert message in errors


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("renderers_exact", 838, "V13 map renderer contract must be exactly 839"),
        ("colliders_exact", 608, "V13 map collider contract must be exactly 609"),
        ("colliders_max", 613, "V13 map collider ceiling must remain 612"),
    ),
)
def test_map_budget_mutations_fail(
    field: str,
    value: int,
    message: str,
) -> None:
    data = load_performance()
    data["map"][field] = value
    errors = prewrite.validate_performance(data)
    assert message in errors


def test_unexpected_classification_field_fails() -> None:
    data = load_classification()
    mutated = copy.deepcopy(data)
    mutated["future_scope"] = []
    errors = prewrite.validate_classification(mutated)
    assert "classification root fields drifted" in errors


def test_malformed_contract_shapes_fail_closed() -> None:
    classification = load_classification()
    classification["ownership"] = []
    performance = load_performance()
    performance["root"] = []
    assert "V13 ownership contract is missing" in prewrite.validate_classification(
        classification
    )
    assert "V13 root budget is missing" in prewrite.validate_performance(performance)
