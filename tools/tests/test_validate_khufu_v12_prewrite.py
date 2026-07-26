from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import tools.validate_khufu_v12_prewrite as prewrite


def git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout.strip()


@pytest.fixture
def contract_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "V12 Test")
    git(tmp_path, "config", "user.email", "v12@example.invalid")
    scene = tmp_path / prewrite.SCENE
    scene.parent.mkdir(parents=True)
    scene.write_text("baseline scene\n", encoding="utf-8")
    docs = tmp_path / prewrite.DOC_ROOT
    docs.mkdir(parents=True)
    for name in ("GOAL.md", "RULES.md", "RESEARCH_BRIEF.md", "PLAN.md", "TEST_PLAN.md", "STATUS.md"):
        (docs / name).write_text(name + "\n", encoding="utf-8")
    (docs / "segment-classification.json").write_text(
        json.dumps(
            {
                "schema": "khufu-v12-queen-circuit-segments-v1",
                "segments": [{"id": f"segment-{index}"} for index in range(6)],
            }
        ),
        encoding="utf-8",
    )
    (docs / "performance-budget.json").write_text(
        json.dumps(
            {
                "schema": "khufu-v12-queen-circuit-budget-v1",
                "root": {
                    "renderers_exact": 5,
                    "colliders_exact": 22,
                    "colliders_max": 33,
                },
                "map": {
                    "renderers_exact": 834,
                    "colliders_exact": 589,
                    "colliders_max": 600,
                },
            }
        ),
        encoding="utf-8",
    )
    asset_hashes: dict[str, str] = {}
    for index, relative in enumerate(prewrite.V11_ASSETS):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"asset {index}\n", encoding="utf-8")
        asset_hashes[relative] = prewrite.sha256(target)
    audit = tmp_path / prewrite.AUDIT
    audit.parent.mkdir(parents=True)
    audit.write_text(
        json.dumps(
            {
                "schema": "khufu-v12-prewrite-audit-v1",
                "scene_sha256": prewrite.sha256(scene),
                "scene_unchanged": True,
                "v4_queen_target_count": 10,
                "v4_queen_targets": [
                    {
                        "path": f"target-{index}",
                        "active_self": True,
                        "active_in_hierarchy": True,
                        "renderer_count": 1,
                        "collider_count": 1,
                        "renderer_enabled": True,
                        "collider_enabled": True,
                        "is_trigger": False,
                        "local_position": {"x": index, "y": 0, "z": 0},
                        "local_rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
                        "local_scale": {"x": 1, "y": 1, "z": 1},
                    }
                    for index in range(10)
                ],
                "v10_queen_gate_spec_count": 1,
                "v10_queen_gate_proxy_enabled": True,
                "v10_great_step_proxy_enabled": False,
                "threshold_proxies": [
                    {
                        "path": f"threshold-{index}",
                        "active_self": True,
                        "active_in_hierarchy": True,
                        "collider_count": 1,
                        "collider_enabled": True,
                        "is_trigger": False,
                    }
                    for index in range(3)
                ],
                "marker_position": {"x": -1.8, "y": 5.35, "z": -2.8},
                "marker_renderer_enabled": False,
                "glow_renderer_enabled": False,
                "inherited_light_enabled": True,
                "v11_signature": prewrite.V11_SIGNATURE,
                "map_metrics": {"renderers": 829, "colliders": 567},
            }
        ),
        encoding="utf-8",
    )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "baseline")
    monkeypatch.setattr(prewrite, "BASELINE_COMMIT", git(tmp_path, "rev-parse", "HEAD"))
    monkeypatch.setattr(prewrite, "SCENE_SHA256", prewrite.sha256(scene))
    monkeypatch.setattr(prewrite, "V11_ASSETS", asset_hashes)
    return tmp_path


def test_complete_prewrite_contract_passes(contract_root: Path) -> None:
    assert prewrite.validate(contract_root).passed


def test_target_count_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["v4_queen_targets"].pop()
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("exactly 10" in error for error in result.errors)


def test_set_active_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["v4_queen_targets"][0]["active_self"] = False
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("baseline state" in error for error in result.errors)


def test_renderer_budget_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.DOC_ROOT / "performance-budget.json"
    budget = json.loads(path.read_text(encoding="utf-8"))
    budget["map"]["renderers_exact"] = 829
    path.write_text(json.dumps(budget), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("exactly 834" in error for error in result.errors)


def test_v11_asset_hash_mutation_fails(contract_root: Path) -> None:
    relative = next(iter(prewrite.V11_ASSETS))
    (contract_root / relative).write_text("drift\n", encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("frozen V11-open asset drifted" in error for error in result.errors)


def test_gate_state_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["v10_great_step_proxy_enabled"] = True
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("Great Step proxy" in error for error in result.errors)


def test_trigger_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["v4_queen_targets"][0]["is_trigger"] = True
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("baseline state" in error for error in result.errors)


def test_threshold_proxy_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["threshold_proxies"][1]["collider_enabled"] = False
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("threshold proxy" in error for error in result.errors)


def test_marker_position_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.AUDIT
    audit = json.loads(path.read_text(encoding="utf-8"))
    audit["marker_position"]["x"] = -1.7
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("marker position" in error for error in result.errors)


def test_exact_collider_budget_mutation_fails(contract_root: Path) -> None:
    path = contract_root / prewrite.DOC_ROOT / "performance-budget.json"
    budget = json.loads(path.read_text(encoding="utf-8"))
    budget["root"]["colliders_exact"] = 21
    path.write_text(json.dumps(budget), encoding="utf-8")
    result = prewrite.validate(contract_root)
    assert any("exactly 22" in error for error in result.errors)
