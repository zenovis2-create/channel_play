from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_khufu_v8_temple_production_art as validator


def test_stale_scene_receipt_is_rejected() -> None:
    errors: list[str] = []
    validator._bound_scene_hash(f"- Scene SHA256: `{'a' * 64}`", "b" * 64, "receipt", errors)
    assert errors == [f"receipt is bound to stale scene {'a' * 64}, expected {'b' * 64}"]


def test_fable_requires_exactly_one_ship_decision() -> None:
    errors: list[str] = []
    validator._check_fable_text("FINAL_REVIEW: ship\nFINAL_REVIEW: ship\n", errors)
    assert errors == ["Fable final review has 2 ship decisions, expected exactly one"]


def test_binding_rejects_hash_mutation(tmp_path: Path) -> None:
    scene = tmp_path / validator.SCENE
    player = tmp_path / validator.PLAYER
    level = tmp_path / validator.BUILT_LEVEL
    for path, content in [(scene, "scene"), (player, "player"), (level, "level")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "test-schema",
                "verdict": "passed",
                "scene": validator._file_record(tmp_path, validator.SCENE),
                "player": {**validator._file_record(tmp_path, validator.PLAYER), "sha256": "0" * 64},
                "built_level": validator._file_record(tmp_path, validator.BUILT_LEVEL),
                "sources": [],
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    result = validator.ValidationResult()
    validator._check_binding(tmp_path, Path("binding.json"), "test-schema", validator.sha256(scene), result)
    assert any("binding hash mismatch" in error for error in result.errors)


def test_scope_rejects_package_and_accepts_v8_paths() -> None:
    assert not validator._allowed_staged("Packages/manifest.json")
    assert validator._allowed_staged("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8WindowsBuild.cs")
    assert validator._allowed_staged("runs/khufu-v7-entry-wayfinding/v5-playmode-regression.md")
    assert validator._allowed_staged("runs/khufu-v8-temple-production-art/validation.md")


def test_png_dimensions_rejects_non_png(tmp_path: Path) -> None:
    path = tmp_path / "bad.png"
    path.write_bytes(b"not a png")
    try:
        validator.png_dimensions(path)
    except ValueError as error:
        assert str(error) == "invalid PNG"
    else:
        raise AssertionError("invalid PNG was accepted")


def test_scene_semantics_tracks_v8_renderer_ownership() -> None:
    text = """%YAML 1.1
--- !u!1 &10
GameObject:
  m_Name: Runtime_Khufu_V8_Temple_Hub_Art
--- !u!4 &11
Transform:
  m_GameObject: {fileID: 10}
--- !u!1 &20
GameObject:
  m_Name: V8_Donor_Test
--- !u!4 &21
Transform:
  m_GameObject: {fileID: 20}
--- !u!23 &22
MeshRenderer:
  m_GameObject: {fileID: 20}
  m_Enabled: 1
"""
    names, classes, renderers, v8_ids, v8_components = validator._scene_semantics(text)
    assert names["V8_Donor_Test"] == 1
    assert classes[23] == 1
    assert renderers[("V8_Donor_Test", 1)] == 1
    assert v8_ids == {10, 20}
    assert v8_components == {1: 2, 4: 2, 23: 1}


def test_canonical_scene_delta_ignores_file_id_churn_but_rejects_other_changes() -> None:
    head = """%YAML 1.1
--- !u!1 &1
GameObject:
  m_Component:
  - component: {fileID: 2}
  m_Name: TraitorEscape_Runtime_Map
--- !u!4 &2
Transform:
  m_GameObject: {fileID: 1}
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_Children:
  - {fileID: 4}
  m_Father: {fileID: 0}
--- !u!1 &3
GameObject:
  m_Component:
  - component: {fileID: 4}
  - component: {fileID: 5}
  m_Name: V5_Test_Renderer
--- !u!4 &4
Transform:
  m_GameObject: {fileID: 3}
  m_LocalPosition: {x: 1, y: 0, z: 0}
  m_Children: []
  m_Father: {fileID: 2}
--- !u!23 &5
MeshRenderer:
  m_GameObject: {fileID: 3}
  m_Enabled: 1
"""
    current = """%YAML 1.1
--- !u!1 &101
GameObject:
  m_Component:
  - component: {fileID: 102}
  m_Name: TraitorEscape_Runtime_Map
--- !u!4 &102
Transform:
  m_GameObject: {fileID: 101}
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_Children:
  - {fileID: 104}
  - {fileID: 107}
  m_Father: {fileID: 0}
--- !u!1 &103
GameObject:
  m_Component:
  - component: {fileID: 104}
  - component: {fileID: 105}
  m_Name: V5_Test_Renderer
--- !u!4 &104
Transform:
  m_GameObject: {fileID: 103}
  m_LocalPosition: {x: 1, y: 0, z: 0}
  m_Children: []
  m_Father: {fileID: 102}
--- !u!23 &105
MeshRenderer:
  m_GameObject: {fileID: 103}
  m_Enabled: 0
--- !u!1 &106
GameObject:
  m_Component:
  - component: {fileID: 107}
  m_Name: Runtime_Khufu_V8_Temple_Hub_Art
--- !u!4 &107
Transform:
  m_GameObject: {fileID: 106}
  m_LocalPosition: {x: 56, y: 1, z: 0}
  m_Children: []
  m_Father: {fileID: 102}
"""
    errors, facts = validator._canonical_scene_delta(
        head,
        current,
        expected_v5=1,
        expected_v6=0,
        expected_v8_documents=2,
    )
    assert errors == []
    assert facts["scene_scope_existing_documents"] == 5
    assert facts["scene_scope_added_v8_documents"] == 2

    mutated = current.replace(
        "m_LocalPosition: {x: 1, y: 0, z: 0}",
        "m_LocalPosition: {x: 2, y: 0, z: 0}",
    )
    errors, _ = validator._canonical_scene_delta(
        head,
        mutated,
        expected_v5=1,
        expected_v6=0,
        expected_v8_documents=2,
    )
    assert any("changed outside allowance" in error for error in errors)
