from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

import pytest

import tools.validate_khufu_v10_release as release
from tools.validate_khufu_v10_release import ValidationResult, fable_verdict, png_dimensions, read_allowlist


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def configure_gate_repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.name", "V10 Test")
    git(root, "config", "user.email", "v10@example.invalid")
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "baseline")

    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("staged-inventory.json"))
    monkeypatch.setattr(release, "STAGED_REPORT", Path("staged-index-validation.md"))
    monkeypatch.setattr(release, "POSTCOMMIT_REPORT", Path("post-commit-validation.md"))
    monkeypatch.setattr(release, "EDITOR_BINDING", Path("editor-binding.json"))
    monkeypatch.setattr(release, "STRICT_PREFIXES", ("scope/",))
    monkeypatch.setattr(release, "SCENE", Path("scope/scene.unity"))
    monkeypatch.setattr(release, "ASSEMBLY", Path("scope/source.cs"))

    scope = root / "scope"
    scope.mkdir()
    scene = scope / "scene.unity"
    source = scope / "source.cs"
    scene.write_text("scene\n", encoding="utf-8")
    source.write_text("source v1\n", encoding="utf-8")
    git(root, "add", "scope/scene.unity", "scope/source.cs")
    binding = {
        "scene": release.file_record(root, Path("scope/scene.unity")),
        "staged_scene": release.index_record(root, "scope/scene.unity"),
        "working_release_inputs": [release.file_record(root, Path("scope/source.cs"))],
        "release_inputs": [release.index_record(root, "scope/source.cs")],
    }
    (root / "editor-binding.json").write_text(json.dumps(binding), encoding="utf-8")
    (root / "allowlist.txt").write_text(
        "\n".join(
            (
                "scope/scene.unity",
                "scope/source.cs",
                "editor-binding.json",
                "staged-inventory.json",
                "staged-index-validation.md",
                "post-commit-validation.md",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    git(root, "add", "editor-binding.json")
    release.write_staged_inventory(root)
    (root / "staged-index-validation.md").write_text(
        "\n".join(
            (
                "- Staged index checked: `True`",
                f"- scene_sha256: `{release.sha256(scene)}`",
                f"- assembly_sha256: `{release.sha256(source)}`",
                "V10_RELEASE_VERDICT: passed",
                "",
            )
        ),
        encoding="utf-8",
    )
    git(root, "add", "staged-inventory.json", "staged-index-validation.md")
    release.write_staged_inventory(root)
    git(root, "add", "staged-inventory.json")


def test_fable_ship_must_be_the_only_final_verdict() -> None:
    assert fable_verdict("No blockers.\nVERDICT: ship\n") == "ship"
    assert fable_verdict("VERDICT: ship\nTrailing text\n") is None
    assert fable_verdict("VERDICT: revise\nVERDICT: ship\n") is None


def test_fable_harness_error_is_never_a_verdict() -> None:
    assert fable_verdict("FABLE_HARNESS_ERROR\nVERDICT: ship\n") is None


def test_png_dimensions_reads_ihdr(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1600, 1000))
    assert png_dimensions(path) == (1600, 1000)


def test_png_dimensions_rejects_invalid_signature(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="invalid PNG"):
        png_dimensions(path)


def test_allowlist_normalizes_and_ignores_comments(tmp_path: Path) -> None:
    path = tmp_path / "docs/khufu-v10-interior-spine/staging-allowlist.txt"
    path.parent.mkdir(parents=True)
    path.write_text("# comment\nfoo\\bar.txt\n\nfoo/baz.txt\n", encoding="utf-8")
    assert read_allowlist(tmp_path) == {"foo/bar.txt", "foo/baz.txt"}


def test_allowlist_ignores_indented_comments(tmp_path: Path) -> None:
    path = tmp_path / "docs/khufu-v10-interior-spine/staging-allowlist.txt"
    path.parent.mkdir(parents=True)
    path.write_text("  # comment\nfoo.txt\n", encoding="utf-8")
    assert read_allowlist(tmp_path) == {"foo.txt"}


def test_binding_detects_release_input_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "V10 Test")
    git(tmp_path, "config", "user.email", "v10@example.invalid")
    paths = [Path(name) for name in ("scene", "player", "level", "assembly", "source", "artifact")]
    for path in paths:
        (tmp_path / path).write_text(path.name, encoding="utf-8")
    git(tmp_path, "add", *(path.as_posix() for path in paths))
    monkeypatch.setattr(release, "SCENE", Path("scene"))
    monkeypatch.setattr(release, "PLAYER", Path("player"))
    monkeypatch.setattr(release, "BUILT_LEVEL", Path("level"))
    monkeypatch.setattr(release, "ASSEMBLY", Path("assembly"))
    monkeypatch.setattr(release, "RELEASE_INPUT_FILES", [Path("source")])

    release.write_binding(tmp_path, Path("binding.json"), "test-schema", [Path("artifact")], False)
    passing = ValidationResult()
    release.check_binding(tmp_path, Path("binding.json"), "test-schema", [Path("artifact")], False, passing)
    assert passing.passed

    (tmp_path / "source").write_text("drifted", encoding="utf-8")
    failing = ValidationResult()
    release.check_binding(tmp_path, Path("binding.json"), "test-schema", [Path("artifact")], False, failing)
    assert any("release input" in error and "drifted" in error for error in failing.errors)


def test_material_guid_must_be_referenced_by_scene(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scene = Path("scene.unity")
    material_meta = Path("material.mat.meta")
    guid = "0123456789abcdef0123456789abcdef"
    (tmp_path / scene).write_text(f"m_Materials: {{fileID: 2100000, guid: {guid}, type: 2}}\n", encoding="utf-8")
    (tmp_path / material_meta).write_text(f"fileFormatVersion: 2\nguid: {guid}\n", encoding="utf-8")
    monkeypatch.setattr(release, "SCENE", scene)
    monkeypatch.setattr(release, "MATERIAL_FILES", [material_meta])
    monkeypatch.setattr(release, "LEGACY_SCENE_DEPENDENCY_FILES", [])
    passing = ValidationResult()
    release.check_material_references(tmp_path, passing)
    assert passing.passed

    (tmp_path / scene).write_text("no material\n", encoding="utf-8")
    failing = ValidationResult()
    release.check_material_references(tmp_path, failing)
    assert any("does not reference" in error for error in failing.errors)


def test_staged_gate_binds_exact_source_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    passing = ValidationResult()
    release.check_staged(tmp_path, passing)
    assert passing.passed

    (tmp_path / "scope/source.cs").write_text("source v2\n", encoding="utf-8")
    git(tmp_path, "add", "scope/source.cs")
    release.write_staged_inventory(tmp_path)
    git(tmp_path, "add", "staged-inventory.json")
    failing = ValidationResult()
    release.check_staged(tmp_path, failing)
    assert any("editor binding staged hash or size drifted" in error for error in failing.errors)


def test_postcommit_requires_exact_inventory_and_rejects_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    git(tmp_path, "commit", "-q", "-m", "release")
    passing = ValidationResult()
    release.check_postcommit(tmp_path, passing)
    assert passing.passed

    (tmp_path / "scope/source.cs").write_text("worktree drift\n", encoding="utf-8")
    failing = ValidationResult()
    release.check_postcommit(tmp_path, failing)
    assert any("worktree drift" in error for error in failing.errors)


def test_postcommit_rejects_empty_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    git(tmp_path, "commit", "-q", "-m", "release")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "empty")
    result = ValidationResult()
    release.check_postcommit(tmp_path, result)
    assert any("absent from HEAD commit" in error for error in result.errors)


def test_postcommit_rejects_subset_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    git(tmp_path, "restore", "--staged", "scope/source.cs")
    git(tmp_path, "commit", "-q", "-m", "subset")
    result = ValidationResult()
    release.check_postcommit(tmp_path, result)
    assert any("scope/source.cs" in error and "absent" in error for error in result.errors)


def test_postcommit_rejects_extra_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    (tmp_path / "extra.txt").write_text("extra\n", encoding="utf-8")
    git(tmp_path, "add", "extra.txt")
    git(tmp_path, "commit", "-q", "-m", "extra")
    result = ValidationResult()
    release.check_postcommit(tmp_path, result)
    assert any("outside exact staged inventory: extra.txt" in error for error in result.errors)
