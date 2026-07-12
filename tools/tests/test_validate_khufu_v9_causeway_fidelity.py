from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_khufu_v9_causeway_fidelity as validator


def test_stale_scene_receipt_is_rejected() -> None:
    errors: list[str] = []
    validator._bound_scene_hash(f"- Scene SHA256: `{'a' * 64}`", "b" * 64, "receipt", errors)
    assert errors == [f"receipt is bound to stale scene {'a' * 64}, expected {'b' * 64}"]


def test_local_fable_requires_exactly_one_ship_decision() -> None:
    errors: list[str] = []
    validator._check_fable_text("LOCAL_FABLE_DECISION: ship\nLOCAL_FABLE_DECISION: ship\n", errors)
    assert errors == ["Local Fable final review has 2 ship decisions, expected exactly one"]


def test_binding_rejects_hash_mutation(tmp_path: Path) -> None:
    scene = tmp_path / validator.SCENE
    player = tmp_path / validator.PLAYER
    level = tmp_path / validator.BUILT_LEVEL
    managed = tmp_path / validator.MANAGED_ASSEMBLY
    artifact = tmp_path / "artifact.txt"
    for path, content in [(scene, "scene"), (player, "player"), (level, "level"), (managed, "managed"), (artifact, "proof")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "test-schema",
                "verdict": "passed",
                "baseline_commit": validator.SCENE_BASELINE_REVISION,
                "scene": validator._file_record(tmp_path, validator.SCENE),
                "player": {**validator._file_record(tmp_path, validator.PLAYER), "sha256": "0" * 64},
                "built_level": validator._file_record(tmp_path, validator.BUILT_LEVEL),
                "managed_assembly": validator._file_record(tmp_path, validator.MANAGED_ASSEMBLY),
                "sources": [],
                "artifacts": [validator._file_record(tmp_path, Path("artifact.txt"))],
            }
        ),
        encoding="utf-8",
    )
    result = validator.ValidationResult()
    validator._check_binding(
        tmp_path,
        Path("binding.json"),
        "test-schema",
        validator.sha256(scene),
        [Path("artifact.txt")],
        result,
    )
    assert any("binding hash mismatch" in error for error in result.errors)
    assert "binding runtime payload inventory mismatch: binding.json" in result.errors


def test_binding_rejects_missing_expected_artifact(tmp_path: Path) -> None:
    scene = tmp_path / validator.SCENE
    player = tmp_path / validator.PLAYER
    level = tmp_path / validator.BUILT_LEVEL
    managed = tmp_path / validator.MANAGED_ASSEMBLY
    for path, content in [(scene, "scene"), (player, "player"), (level, "level"), (managed, "managed")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    sources = [*validator.V9_SOURCES, *validator.GENERATED_MESHES, *validator.V9_ASSET_META]
    for path in sources:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path.as_posix(), encoding="utf-8")
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "test-schema",
                "verdict": "passed",
                "baseline_commit": validator.SCENE_BASELINE_REVISION,
                "scene": validator._file_record(tmp_path, validator.SCENE),
                "player": validator._file_record(tmp_path, validator.PLAYER),
                "built_level": validator._file_record(tmp_path, validator.BUILT_LEVEL),
                "managed_assembly": validator._file_record(tmp_path, validator.MANAGED_ASSEMBLY),
                "sources": [validator._file_record(tmp_path, path) for path in sources],
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    result = validator.ValidationResult()
    validator._check_binding(
        tmp_path,
        Path("binding.json"),
        "test-schema",
        validator.sha256(scene),
        [Path("missing.txt")],
        result,
    )
    assert "binding artifact inventory mismatch: binding.json" in result.errors


def test_scope_rejects_package_and_accepts_v9_paths() -> None:
    assert not validator._allowed_staged("Packages/manifest.json")
    assert not validator._allowed_staged("ProjectSettings/ProjectSettings.asset")
    assert not validator._allowed_staged("Assets/_Project/Materials/Point_Gold.mat")
    assert not validator._allowed_staged("runs/khufu-v9-causeway-fidelity/static-final-shape.log")
    assert validator._allowed_staged("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9WindowsBuild.cs")
    assert validator._allowed_staged("runs/khufu-v9-causeway-fidelity/validation.md")
    assert validator._allowed_staged("docs/khufu-v9-causeway-fidelity/GOAL.md")


def test_png_dimensions_rejects_non_png(tmp_path: Path) -> None:
    path = tmp_path / "bad.png"
    path.write_bytes(b"not a png")
    try:
        validator.png_dimensions(path)
    except ValueError as error:
        assert str(error) == "invalid PNG"
    else:
        raise AssertionError("invalid PNG was accepted")


def test_png_semantic_decode_rejects_trailing_padding(tmp_path: Path) -> None:
    def chunk(name: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(payload, zlib.crc32(name)) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    pixels = b"\x00\xff\x00\x00\x00\xff\x00" + b"\x00\x00\x00\xff\xff\xff\xff"
    payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
    valid = tmp_path / "valid.png"
    valid.write_bytes(payload)
    metrics = validator.png_semantic_metrics(valid)
    assert (metrics.width, metrics.height, metrics.unique_sampled_colors) == (2, 2, 1)

    padded = tmp_path / "padded.png"
    padded.write_bytes(payload + b"padded-junk")
    try:
        validator.png_semantic_metrics(padded)
    except ValueError as error:
        assert str(error) == "incomplete or padded PNG"
    else:
        raise AssertionError("padded PNG was accepted")


def test_renderer_whitelist_is_exactly_twenty_unique_names() -> None:
    assert len(validator.EXPECTED_DISABLED_RENDERERS) == 20
    assert "V5_Route_Segment_00_Floor" in validator.EXPECTED_DISABLED_RENDERERS
    assert "V5_Covered_Causeway_Lintel" in validator.EXPECTED_DISABLED_RENDERERS


def test_scene_inventory_finds_v9_owned_subtree() -> None:
    text = """%YAML 1.1
--- !u!1 &1
GameObject:
  m_Component:
  - component: {fileID: 2}
  m_Name: TraitorEscape_Runtime_Map
--- !u!4 &2
Transform:
  m_GameObject: {fileID: 1}
  m_Children:
  - {fileID: 4}
  m_Father: {fileID: 0}
--- !u!1 &3
GameObject:
  m_Component:
  - component: {fileID: 4}
  - component: {fileID: 5}
  m_Name: Runtime_Khufu_V9_Causeway_Fidelity
--- !u!4 &4
Transform:
  m_GameObject: {fileID: 3}
  m_Children: []
  m_Father: {fileID: 2}
--- !u!65 &5
BoxCollider:
  m_GameObject: {fileID: 3}
  m_Enabled: 1
"""
    inventory = validator._scene_inventory(text)
    assert inventory["v9_documents"] == {3, 4, 5}
    assert inventory["v9_root_transform"] == 4
    assert inventory["map_transform"] == 2


def test_enabled_normalization_preserves_all_other_fields() -> None:
    enabled = "MeshRenderer:\n  m_Enabled: 1\n  m_CastShadows: 1\n"
    disabled = "MeshRenderer:\n  m_Enabled: 0\n  m_CastShadows: 1\n"
    mutated = "MeshRenderer:\n  m_Enabled: 0\n  m_CastShadows: 0\n"
    assert validator._normalized_enabled(enabled) == validator._normalized_enabled(disabled)
    assert validator._normalized_enabled(enabled) != validator._normalized_enabled(mutated)
