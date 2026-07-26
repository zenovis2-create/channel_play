from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

import pytest

import tools.validate_khufu_v12_release as release
from tools.validate_khufu_v12_release import (
    ValidationResult,
    fable_verdict,
    parse_status_paths,
    png_dimensions,
)


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def configure_gate_repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.name", "V12 Test")
    git(root, "config", "user.email", "v12@example.invalid")
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "baseline")

    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("staged-inventory.json"))
    monkeypatch.setattr(release, "STAGED_REPORT", Path("staged-index-validation.md"))
    monkeypatch.setattr(release, "POSTCOMMIT_REPORT", Path("post-commit-validation.md"))
    monkeypatch.setattr(release, "STRICT_PREFIXES", ("scope/",))
    (root / "allowlist.txt").write_text(
        "\n".join(
            (
                "scope/source.cs",
                "staged-inventory.json",
                "staged-index-validation.md",
                "post-commit-validation.md",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "scope").mkdir()
    (root / "scope/source.cs").write_text("source v1\n", encoding="utf-8")
    git(root, "add", "scope/source.cs")
    release.write_staged_inventory(root)
    git(root, "add", "staged-inventory.json")
    (root / "staged-index-validation.md").write_text(
        "KHUFU_V12_RELEASE_VERDICT: passed\n", encoding="utf-8"
    )
    git(root, "add", "staged-index-validation.md")


def test_fable_ship_must_be_the_only_final_verdict() -> None:
    assert fable_verdict("No blockers.\nVERDICT: ship\n") == "ship"
    assert fable_verdict("VERDICT: ship\nTrailing text\n") is None
    assert fable_verdict("VERDICT: revise minimally\nVERDICT: ship\n") is None
    assert fable_verdict("VERDICT: do not ship\n") == "do not ship"


def test_fable_harness_error_is_never_a_verdict() -> None:
    assert fable_verdict("FABLE_HARNESS_ERROR\nVERDICT: ship\n") is None


def test_staged_and_postcommit_modes_automatically_require_reviews() -> None:
    assert not release.effective_review_requirement(False, False, False)
    assert release.effective_review_requirement(True, False, False)
    assert release.effective_review_requirement(False, True, False)
    assert release.effective_review_requirement(False, False, True)


def test_pass_token_must_be_one_exact_complete_line() -> None:
    passing = ValidationResult()
    release.require_exact_token(
        "context\nTOKEN: passed\n", "TOKEN: passed", "receipt", passing
    )
    assert passing.passed

    for text in (
        "TOKEN: not passed\n",
        "TOKEN: passed_with_suffix\n",
        "TOKEN: passed\nTOKEN: passed\n",
    ):
        failing = ValidationResult()
        release.require_exact_token(text, "TOKEN: passed", "receipt", failing)
        assert not failing.passed


def test_png_dimensions_reads_ihdr(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", 1600, 1000)
    )
    assert png_dimensions(path) == (1600, 1000)


def test_png_dimensions_rejects_invalid_signature(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="invalid PNG"):
        png_dimensions(path)


def test_allowlist_normalizes_and_ignores_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "allowlist.txt"
    path.write_text("# comment\nfoo/bar.txt\n\nfoo/baz.txt\n", encoding="utf-8")
    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    assert release.read_allowlist(tmp_path) == {"foo/bar.txt", "foo/baz.txt"}


@pytest.mark.parametrize(
    "entry", ("../outside.txt", "C:/outside.txt", "foo\\bar.txt")
)
def test_allowlist_rejects_unsafe_entries(
    entry: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "allowlist.txt").write_text(entry + "\n", encoding="utf-8")
    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    with pytest.raises(ValueError, match="unsafe allowlist entry"):
        release.read_allowlist(tmp_path)


def test_allowlist_rejects_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "allowlist.txt").write_text(
        "scope/file.txt\nscope/file.txt\n", encoding="utf-8"
    )
    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    with pytest.raises(ValueError, match="duplicate"):
        release.read_allowlist(tmp_path)


def test_status_paths_preserves_both_sides_of_rename_records() -> None:
    payload = (
        b" M scope/modified.cs\0"
        b"R  scope/renamed.cs\0scope/original.cs\0"
        b"?? scope/new.cs\0"
    )
    assert parse_status_paths(payload) == {
        "scope/modified.cs",
        "scope/renamed.cs",
        "scope/original.cs",
        "scope/new.cs",
    }


def test_unlisted_run_receipts_fail_but_raw_logs_are_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(release, "RUN_ROOT", Path("runs/v12"))
    assert release.is_unlisted_release_scope("runs/v12/unlisted-final.md")
    assert not release.is_unlisted_release_scope("runs/v12/iteration.log")
    assert not release.is_unlisted_release_scope("runs/v12/legacy-v10-raw.md")


def test_staged_gate_binds_exact_index_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    passing = ValidationResult()
    release.check_staged(tmp_path, passing)
    assert passing.passed

    (tmp_path / "scope/source.cs").write_text("source v2\n", encoding="utf-8")
    git(tmp_path, "add", "scope/source.cs")
    failing = ValidationResult()
    release.check_staged(tmp_path, failing)
    assert any("staged hash or size drifted" in error for error in failing.errors)


def test_staged_gate_rejects_unlisted_scope_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    (tmp_path / "scope/unlisted.cs").write_text("unlisted\n", encoding="utf-8")
    result = ValidationResult()
    release.check_staged(tmp_path, result)
    assert any("unlisted V12 scope path" in error for error in result.errors)


def test_postcommit_requires_exact_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    git(tmp_path, "commit", "-q", "-m", "release")
    passing = ValidationResult()
    release.check_postcommit(tmp_path, passing)
    assert passing.passed

    (tmp_path / "scope/source.cs").write_text("drift\n", encoding="utf-8")
    failing = ValidationResult()
    release.check_postcommit(tmp_path, failing)
    assert any("worktree drift" in error for error in failing.errors)


def test_staged_inventory_schema_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps({"schema": "wrong", "files": []}), encoding="utf-8"
    )
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("inventory.json"))
    result = ValidationResult()
    release.read_staged_inventory(tmp_path, result)
    assert any("schema" in error for error in result.errors)


def test_staged_inventory_rejects_non_object_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "schema": "khufu-v12-staged-inventory-v1",
                "files": ["not-an-object"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("inventory.json"))
    result = ValidationResult()
    assert release.read_staged_inventory(tmp_path, result) == []
    assert any("record" in error for error in result.errors)


def test_staged_inventory_base_commit_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "schema": "khufu-v12-staged-inventory-v1",
                "base_commit": "not-a-commit",
                "files": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("inventory.json"))
    result = ValidationResult()
    assert release.read_staged_base_commit(tmp_path, result) == ""
    assert any("base_commit" in error for error in result.errors)
