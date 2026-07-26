from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

import tools.validate_khufu_v13_release as release
from tools.validate_khufu_v13_release import ValidationResult


def test_legacy_source_binding_covers_v4_through_v12() -> None:
    names = {path.name for path in release.LEGACY_SOURCES}
    assert len(release.LEGACY_SOURCES) == 9
    assert "ChannelPlayKhufuV6VisualSliceValidator.cs" in names
    assert "ChannelPlayKhufuV7EntryWayfindingValidator.cs" in names


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


def write(root: Path, relative: Path, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def png_bytes(seed: int, width: int = 1600, height: int = 1000) -> bytes:
    header = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
    )
    return header + bytes([seed]) * (60032 + seed)


def meta(guid: str) -> str:
    return f"fileFormatVersion: 2\nguid: {guid}\n"


def hash_lines(root: Path, paths: tuple[Path, ...]) -> str:
    return "\n".join(
        f"- {path.as_posix()} SHA256: `{release.sha256(root / path)}`"
        for path in paths
    )


def build_complete_fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, str]:
    git(root, "init", "-q")
    git(root, "config", "user.name", "V13 Test")
    git(root, "config", "user.email", "v13@example.invalid")
    write(root, Path("README.md"), "baseline\n")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "baseline")
    baseline = git(root, "rev-parse", "HEAD")
    monkeypatch.setattr(release, "BASELINE_COMMIT", baseline)

    guid_by_path: dict[Path, str] = {}
    for index, relative in enumerate(
        (
            *release.UNITY_SCRIPT_METAS,
            *release.GENERATED_METAS,
            *release.MATERIAL_METAS,
            *release.ROOT_METAS,
        ),
        start=1,
    ):
        guid = f"{index:032x}"
        guid_by_path[relative] = guid
        write(root, relative, meta(guid))

    for relative in release.UNITY_SOURCES:
        write(root, relative, f"// synthetic source {relative.name}\n")
    for relative in release.PYTHON_SOURCES:
        write(root, relative, f"# synthetic source {relative.name}\n")
    for relative in release.LEGACY_SOURCES:
        write(root, relative, f"// legacy dependency {relative.name}\n")
    for relative in release.GENERATED_ASSETS:
        write(root, relative, f"generated:{relative.name}\n".encode())
    for relative in release.MATERIAL_FILES:
        write(root, relative, f"material:{relative.name}\n".encode())
    write(root, release.GIT_ATTRIBUTES, "* text=auto\n")

    scene_guids = [
        guid_by_path[path]
        for path in (
            *release.GENERATED_METAS,
            *release.MATERIAL_METAS,
            *release.SERIALIZED_SCRIPT_METAS,
        )
    ]
    write(
        root,
        release.SCENE,
        "synthetic V13 scene\n" + "\n".join(f"guid: {guid}" for guid in scene_guids),
    )

    rules = "\n".join(
        (
            release.BASELINE_COMMIT,
            release.BASELINE_SCENE_SHA256,
            release.V12_STATIC_SIGNATURE,
        )
    )
    for relative in release.DOC_FILES:
        if relative == release.ALLOWLIST:
            continue
        write(root, relative, rules if relative.name == "RULES.md" else "contract\n")
    write(
        root,
        release.ALLOWLIST,
        "# Exact synthetic release inventory.\n"
        + "\n".join(sorted(release.expected_allowlist()))
        + "\n",
    )

    for relative in (
        release.PLAYER,
        release.UNITY_PLAYER,
        release.BUILT_LEVEL,
        release.ASSEMBLY,
    ):
        write(root, relative, f"build:{relative.name}\n".encode())
    for relative in release.PHASE_RECEIPTS:
        write(root, relative, f"# {relative.stem}\n\nVerdict: passed\n")
    write(root, release.RUN_ROOT / "prewrite-audit.json", '{"passed": true}\n')

    prewrite_tokens = "\n".join(
        (
            release.BASELINE_SCENE_SHA256,
            release.V12_STATIC_SIGNATURE,
            "renderers=5_vertices=1176_triangles=588_colliders=22",
            "renderers=834_vertices=67070_triangles=48560_colliders=589",
        )
    )
    write(
        root,
        release.RUN_ROOT / "prewrite-audit.md",
        prewrite_tokens
        + "\n- Exact V4 ownership targets: `13/13`"
        + "\n- Exact preserved observations: `7/7`"
        + "\n\nKHUFU_V13_PREWRITE_AUDIT: passed\n",
    )
    write(
        root,
        release.RUN_ROOT / "prewrite-validation.md",
        prewrite_tokens + "\n\nV13_PREWRITE_VERDICT: passed\n",
    )

    static_signature = "a" * 64
    write(
        root,
        release.RUN_ROOT / "static-validation.md",
        "# Static\n"
        f"- V13 signature: `{static_signature}`\n"
        f"- V12 restored-context signature: `{release.V12_STATIC_SIGNATURE}`\n"
        "- Root metrics: `renderers=5_vertices=792_triangles=396_colliders=20`\n"
        "- Map metrics: `renderers=839_vertices=67862_triangles=48956_colliders=609`\n\n"
        "KHUFU_V13_STATIC_VALIDATION: passed\n",
    )
    scene_hash = release.sha256(root / release.SCENE)
    generated_hash = release.generated_asset_signature(root)
    write(
        root,
        release.RUN_ROOT / "idempotence.md",
        "# Idempotence\n"
        f"- First / second signature: `{static_signature} / {static_signature}`\n"
        f"- First / second scene SHA256: `{scene_hash} / {scene_hash}`\n"
        f"- First / second generated signature: `{generated_hash} / {generated_hash}`\n\n"
        "KHUFU_V13_IDEMPOTENCE: passed\n",
    )
    negative_cases = (
        "V4 renderer restored",
        "V4 target deactivated",
        "Structural pair drift",
        "Chamber ceiling proxy disabled",
        "Pit backing disabled",
        "V10-owned marker moved",
        "Inherited light disabled",
        "Junction inner wall trim reverted",
        "V10 branch bypass floor proxy restored",
        "Injected successor failure -> rollback verified",
    )
    write(
        root,
        release.RUN_ROOT / "negative-controls.md",
        "# Negative controls\n"
        + "\n".join(f"- {label}: `rejected`" for label in negative_cases)
        + f"\n- Rollback scene SHA256: `{scene_hash}`"
        + f"\n- Rollback generated signature: `{generated_hash}`"
        + "\n\nKHUFU_V13_NEGATIVE_CONTROLS: passed\n",
    )

    legacy_rows = "\n".join(
        f"- {label}: `passed` / signature `original`"
        for label in ("V4", "V5")
    )
    legacy_rows += "\n" + "\n".join(
        f"- {label}: `passed` / signature `{signature} / "
        f"classified exact historical source-hash deltas={count}`"
        for label, (signature, count) in release.LEGACY_HISTORICAL_RESULTS.items()
    )
    legacy_rows += (
        f"\n- V10: `passed` / signature `{release.V10_RESTORED_SIGNATURE} / "
        "classified exact V12 transition deltas=19`"
        f"\n- V11: `passed` / signature `{release.V11_RESTORED_SIGNATURE}`"
        f"\n- V12: `passed` / signature `{release.V12_STATIC_SIGNATURE}`"
    )
    historical_deltas = "\n".join(
        f"  - Classified exact historical source-hash delta: "
        f"`historical-{index:02d}`"
        for index in range(23)
    )
    deltas = "\n".join(
        f"  - Classified exact V12 transition delta: `delta-{index:02d}`"
        for index in range(19)
    )
    legacy_hashes = hash_lines(
        root, (*release.LEGACY_SOURCES, release.BUILDER, release.LEGACY)
    )
    write(
        root,
        release.RUN_ROOT / "legacy-regression.md",
        "# Legacy\n"
        f"- V13 canonical return: `passed` / signature `{static_signature}`\n"
        f"- Scene SHA256 before / after: `{scene_hash} / {scene_hash}`\n"
        "- Scene bytes unchanged: `True`\n"
        + legacy_rows
        + "\n- Summary: `classified exact V12 transition deltas=19`\n"
        + historical_deltas
        + "\n"
        + deltas
        + "\n"
        + legacy_hashes
        + "\n\nKHUFU_V13_LEGACY_REGRESSION: passed\n",
    )

    image_hashes: dict[Path, str] = {}
    for index, relative in enumerate(release.CAPTURE_IMAGES, start=1):
        write(root, relative, png_bytes(index))
        image_hashes[relative] = release.sha256(root / relative)
    capture_sources = hash_lines(root, release.CAPTURE_BOUND_SOURCES)
    static_receipt_hash = release.sha256(
        root / release.RUN_ROOT / "static-validation.md"
    )
    capture_entries = "\n".join(
        f"## {relative.stem}\n- SHA256: `{digest}`\n"
        for relative, digest in image_hashes.items()
    )
    write(
        root,
        release.RUN_ROOT / "captures/manifest.md",
        "# Captures\n"
        "- Resolution: `1600x1000`\n"
        "- Required captures: `6`\n"
        "- Inherited `V4_Light_Subterranean`: `enabled and disclosed`\n"
        f"- Scene SHA256: `{scene_hash}`\n"
        + capture_sources
        + f"\n- Static receipt SHA256: `{static_receipt_hash}`\n"
        + capture_entries
        + "\nCAPTURE_INTEGRITY: passed\n"
        + "KHUFU_V13_REQUIRED_CAPTURES: passed\n",
    )
    review_entries = "\n".join(
        f"- {relative.name}: `{digest}`" for relative, digest in image_hashes.items()
    )
    write(
        root,
        release.RUN_ROOT / "captures/manual-semantic-review.md",
        "# Semantic review\n"
        + review_entries
        + "\n\nKHUFU_V13_CAPTURE_SEMANTIC_REVIEW: passed\n",
    )

    build_hashes = hash_lines(
        root,
        (
            release.PLAYER,
            release.UNITY_PLAYER,
            release.BUILT_LEVEL,
            release.ASSEMBLY,
            *release.BUILD_BOUND_SOURCES,
        ),
    )
    write(
        root,
        release.RUN_ROOT / "windows-build.md",
        "# Build\n"
        "- Build target: `StandaloneWindows64` Development Player\n"
        "- Output: `Builds/KhufuV13/ChannelPlayKhufuV13.exe`\n"
        "- Errors / warnings: `0 / 7`\n"
        f"- Scene source SHA256: `{scene_hash}`\n"
        "- Protected V13 generated/material signature before/after: "
        f"`{generated_hash} / {generated_hash}`\n"
        + build_hashes
        + "\n\nV13_WINDOWS_BUILD: passed\n",
    )

    header = (
        "segment,step,move_frame,before,target,after,request,error,flags,"
        "side_hit,callback_frame\n"
    )
    write(root, release.PLAYER_ARTIFACTS[2], header + "1,1,10,a,b,c,0.1,0,None,,\n")
    write(root, release.PLAYER_ARTIFACTS[3], header + "1,1,20,a,b,c,0.08,0,Sides,wall,20\n")
    normal_trace_hash = release.sha256(root / release.PLAYER_ARTIFACTS[2])
    boundary_trace_hash = release.sha256(root / release.PLAYER_ARTIFACTS[3])
    assembly_hash = release.sha256(root / release.ASSEMBLY)
    write(
        root,
        release.PLAYER_ARTIFACTS[0],
        "# Player normal\n"
        "- Mode: `normal-round-trip`\n"
        "- V10 branch -> landing -> door -> chamber/pit -> return: `passed`\n"
        "- Reached route anchors: `11/11`\n"
        "- Serialized anchors match: `True`\n"
        "- Traversed distance / max error / final error: `62.000 / 0.100 / 0.050`\n"
        "- Grounded steps/fraction: `100/100 / 1.000`\n"
        "- Outbound grounded steps/fraction: `50/50 / 1.000`\n"
        "- Return grounded steps/fraction: `50/50 / 1.000`\n"
        "- Root renderers / enabled colliders: `5 / 20`\n"
        "- Pit overlap / cast solid backing: `True / True`\n"
        f"- Movement trace: `{release.PLAYER_ARTIFACTS[2].as_posix()}` / "
        f"records `1` / SHA256 `{normal_trace_hash}`\n"
        f"- Assembly-CSharp SHA256: `{assembly_hash}`\n\n"
        "V13_WINDOWS_PLAYER_TRAVERSAL: passed\n",
    )
    write(
        root,
        release.PLAYER_ARTIFACTS[1],
        "# Player boundary\n"
        "- Mode: `outside-wall-control`\n"
        "- Outside-wall control: `passed`\n"
        "- Control boundary start distance: `1.700 m`\n"
        "- Control boundary signed start / end: `-1.700 / 0.650 m`\n"
        "- Control pre-Move overlap empty: `True`\n"
        "- Control maximum requested step: `0.080 m`\n"
        "- Control blocked collider / flags: `V13_Proxy_Chamber_East_Wall / Sides`\n"
        "- Control Move / callback frame: `20 / 20`\n"
        "- Control callback: `OnControllerColliderHit` / exact `True`\n"
        f"- Movement trace: `{release.PLAYER_ARTIFACTS[3].as_posix()}` / "
        f"records `1` / SHA256 `{boundary_trace_hash}`\n"
        f"- Assembly-CSharp SHA256: `{assembly_hash}`\n\n"
        "V13_WINDOWS_PLAYER_BOUNDARY_CONTROL: passed\n",
    )
    write(
        root,
        release.RUN_ROOT / "python-tests.md",
        "KHUFU_V13_PYTHON_TESTS: passed\n",
    )
    clean_hashes = hash_lines(root, release.CLEAN_BOUND_SOURCES)
    write(
        root,
        release.RUN_ROOT / "clean-index-import.md",
        "# Clean index\n"
        f"- Static signature: `{static_signature}`\n"
        "- Compiler errors: `0`\n"
        + clean_hashes
        + "\n\nKHUFU_V13_CLEAN_INDEX_IMPORT: passed\n",
    )
    return {
        "baseline": baseline,
        "generated": generated_hash,
        "scene": scene_hash,
        "static": static_signature,
    }


def validate_fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> release.ValidationResult:
    build_complete_fixture(root, monkeypatch)
    return release.validate(root, False, False, False)


def test_complete_synthetic_release_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = validate_fixture(tmp_path, monkeypatch)
    assert result.passed, result.errors
    assert result.facts["capture_pngs"] == 6


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("duplicate_token", "exactly one complete pass token"),
        ("scene_drift", "idempotence receipt contract missing"),
        ("generated_drift", "idempotence receipt contract missing"),
        ("duplicate_capture", "duplicate PNG bytes"),
        ("wrong_dimensions", "PNG dimensions drifted"),
        ("forbidden_term", "forbidden V13 scope term"),
        ("extra_source", "editor source/meta inventory drifted"),
        ("duplicate_guid", "GUIDs are not unique"),
        ("traversal_error", "anchor error exceeds"),
        ("outbound_grounded", "outbound grounded fraction is below 0.90"),
        ("return_grounded", "return grounded fraction is below 0.90"),
        ("boundary_direction", "does not run from chamber interior to exterior"),
        ("legacy_delta", "exactly 19 V10 deltas"),
        ("allowlist_extra", "unexpected path is present"),
        ("build_hash", "Windows build receipt is not bound"),
    ),
)
def test_release_mutations_fail_closed(
    mutation: str,
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_complete_fixture(tmp_path, monkeypatch)
    if mutation == "duplicate_token":
        path = tmp_path / release.RUN_ROOT / "static-validation.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "KHUFU_V13_STATIC_VALIDATION: passed\n",
            encoding="utf-8",
        )
    elif mutation == "scene_drift":
        with (tmp_path / release.SCENE).open("a", encoding="utf-8") as stream:
            stream.write("drift\n")
    elif mutation == "generated_drift":
        with (tmp_path / release.GENERATED_ASSETS[0]).open("ab") as stream:
            stream.write(b"drift")
    elif mutation == "duplicate_capture":
        shutil.copyfile(
            tmp_path / release.CAPTURE_IMAGES[0],
            tmp_path / release.CAPTURE_IMAGES[1],
        )
    elif mutation == "wrong_dimensions":
        (tmp_path / release.CAPTURE_IMAGES[0]).write_bytes(
            png_bytes(9, width=1599)
        )
    elif mutation == "forbidden_term":
        with (tmp_path / release.BUILDER).open("a", encoding="utf-8") as stream:
            stream.write("// ScanPyramids\n")
    elif mutation == "extra_source":
        write(
            tmp_path,
            Path(
                "Assets/_Project/Scripts/Editor/"
                "ChannelPlayKhufuV13Unexpected.cs"
            ),
            "// extra\n",
        )
    elif mutation == "duplicate_guid":
        source = tmp_path / release.UNITY_SCRIPT_METAS[0]
        target = tmp_path / release.UNITY_SCRIPT_METAS[1]
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    elif mutation == "traversal_error":
        path = tmp_path / release.PLAYER_ARTIFACTS[0]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "62.000 / 0.100 / 0.050", "62.000 / 0.401 / 0.050"
            ),
            encoding="utf-8",
        )
    elif mutation == "outbound_grounded":
        path = tmp_path / release.PLAYER_ARTIFACTS[0]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "50/50 / 1.000", "44/50 / 0.880", 1
            ),
            encoding="utf-8",
        )
    elif mutation == "return_grounded":
        path = tmp_path / release.PLAYER_ARTIFACTS[0]
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "- Return grounded steps/fraction: `50/50 / 1.000`",
                "- Return grounded steps/fraction: `44/50 / 0.880`",
            ),
            encoding="utf-8",
        )
    elif mutation == "boundary_direction":
        path = tmp_path / release.PLAYER_ARTIFACTS[1]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "-1.700 / 0.650", "1.700 / -0.650"
            ),
            encoding="utf-8",
        )
    elif mutation == "legacy_delta":
        path = tmp_path / release.RUN_ROOT / "legacy-regression.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "  - Classified exact V12 transition delta: `delta-00`\n", ""
        )
        path.write_text(text, encoding="utf-8")
    elif mutation == "allowlist_extra":
        with (tmp_path / release.ALLOWLIST).open("a", encoding="utf-8") as stream:
            stream.write("unapproved.txt\n")
    elif mutation == "build_hash":
        path = tmp_path / release.RUN_ROOT / "windows-build.md"
        digest = release.sha256(tmp_path / release.ASSEMBLY)
        path.write_text(
            path.read_text(encoding="utf-8").replace(digest, "0" * 64),
            encoding="utf-8",
        )
    result = release.validate(tmp_path, False, False, False)
    assert not result.passed
    assert any(expected in error for error in result.errors), result.errors


def test_missing_source_meta_fails_before_receipt_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_complete_fixture(tmp_path, monkeypatch)
    (tmp_path / release.UNITY_SCRIPT_METAS[0]).unlink()
    result = release.validate(tmp_path, False, False, False)
    assert any("missing or empty" in error for error in result.errors)


def test_baseline_ancestry_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_complete_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(release, "BASELINE_COMMIT", "0" * 40)
    result = release.validate(tmp_path, False, False, False)
    assert any("baseline commit is unavailable" in error for error in result.errors)


def test_pass_token_requires_one_exact_complete_line() -> None:
    passing = ValidationResult()
    release.require_exact_token(
        "context\nTOKEN: passed\n", "TOKEN: passed", "receipt", passing
    )
    assert passing.passed
    for text in (
        "TOKEN: passed_with_suffix\n",
        "TOKEN: passed\nTOKEN: passed\n",
        "prefix TOKEN: passed\n",
    ):
        failing = ValidationResult()
        release.require_exact_token(text, "TOKEN: passed", "receipt", failing)
        assert not failing.passed


def test_png_dimensions_rejects_invalid_signature(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="invalid PNG"):
        release.png_dimensions(path)


@pytest.mark.parametrize(
    "entry", ("../outside.txt", "C:/outside.txt", "foo\\bar.txt")
)
def test_allowlist_rejects_unsafe_entries(
    entry: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write(tmp_path, Path("allowlist.txt"), entry + "\n")
    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    with pytest.raises(ValueError, match="unsafe allowlist entry"):
        release.read_allowlist(tmp_path)


def configure_gate_repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.name", "V13 Gate Test")
    git(root, "config", "user.email", "gate@example.invalid")
    write(root, Path("README.md"), "baseline\n")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "baseline")
    monkeypatch.setattr(release, "ALLOWLIST", Path("allowlist.txt"))
    monkeypatch.setattr(release, "STAGED_INVENTORY", Path("staged-inventory.json"))
    monkeypatch.setattr(release, "STAGED_REPORT", Path("staged-index-validation.md"))
    monkeypatch.setattr(release, "POSTCOMMIT_REPORT", Path("post-commit-validation.md"))
    monkeypatch.setattr(release, "STRICT_PREFIXES", ("scope/",))
    write(
        root,
        Path("allowlist.txt"),
        "\n".join(
            (
                "scope/source.cs",
                "staged-inventory.json",
                "staged-index-validation.md",
                "post-commit-validation.md",
            )
        )
        + "\n",
    )
    write(root, Path("scope/source.cs"), "source v1\n")
    git(root, "add", "scope/source.cs")
    release.write_staged_inventory(root)
    git(root, "add", "staged-inventory.json")
    write(
        root,
        Path("staged-index-validation.md"),
        "KHUFU_V13_RELEASE_VERDICT: passed\n",
    )
    git(root, "add", "staged-index-validation.md")


def test_staged_gate_binds_exact_index_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    passing = ValidationResult()
    release.check_staged(tmp_path, passing)
    assert passing.passed, passing.errors
    write(tmp_path, Path("scope/source.cs"), "source v2\n")
    git(tmp_path, "add", "scope/source.cs")
    failing = ValidationResult()
    release.check_staged(tmp_path, failing)
    assert any("hash or size drifted" in error for error in failing.errors)


def test_staged_gate_rejects_unlisted_scope_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    write(tmp_path, Path("scope/unlisted.cs"), "unlisted\n")
    result = ValidationResult()
    release.check_staged(tmp_path, result)
    assert any("unlisted V13 scope path" in error for error in result.errors)


def test_postcommit_requires_exact_inventory_and_clean_convergence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_gate_repo(tmp_path, monkeypatch)
    git(tmp_path, "commit", "-q", "-m", "release")
    passing = ValidationResult()
    release.check_postcommit(tmp_path, passing)
    assert passing.passed, passing.errors
    write(tmp_path, Path("scope/source.cs"), "worktree drift\n")
    failing = ValidationResult()
    release.check_postcommit(tmp_path, failing)
    assert any("worktree drift" in error for error in failing.errors)


def test_staged_inventory_schema_and_records_are_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = Path("inventory.json")
    write(
        tmp_path,
        path,
        json.dumps(
            {
                "schema": "wrong",
                "base_commit": "not-a-commit",
                "files": ["not-an-object"],
            }
        ),
    )
    monkeypatch.setattr(release, "STAGED_INVENTORY", path)
    result = ValidationResult()
    assert release.read_staged_inventory(tmp_path, result) == []
    assert release.read_staged_base_commit(tmp_path, result) == ""
    assert any("schema" in error for error in result.errors)
    assert any("record" in error for error in result.errors)
    assert any("base_commit" in error for error in result.errors)


def test_staged_and_postcommit_modes_require_reviews() -> None:
    assert not release.effective_review_requirement(False, False, False)
    assert release.effective_review_requirement(True, False, False)
    assert release.effective_review_requirement(False, True, False)
    assert release.effective_review_requirement(False, False, True)


def test_fable_ship_must_be_the_only_final_verdict() -> None:
    assert release.fable_verdict("No blockers.\nVERDICT: ship\n") == "ship"
    assert release.fable_verdict("VERDICT: ship\nTrailing text\n") is None
    assert release.fable_verdict("FABLE_HARNESS_ERROR\nVERDICT: ship\n") is None


def test_orchestrator_review_fallback_is_hash_bound(tmp_path: Path) -> None:
    for relative in release.ORCHESTRATOR_REVIEW_SOURCES:
        write(tmp_path, relative, f"reviewed {relative.as_posix()}\n")
    hashes = hash_lines(tmp_path, release.ORCHESTRATOR_REVIEW_SOURCES)
    write(
        tmp_path,
        release.RUN_ROOT / "review-resolution.md",
        "# Review resolution\n"
        "- Review mechanism: `activate-agents-orchestrator`\n"
        "- Blocking findings: `0`\n"
        + hashes
        + "\n\nKHUFU_V13_REVIEW_RESOLUTION: passed\n",
    )
    passing = ValidationResult()
    release.check_review_evidence(tmp_path, passing)
    assert passing.passed, passing.errors

    path = tmp_path / release.ORCHESTRATOR_REVIEW_SOURCES[0]
    path.write_text("drifted\n", encoding="utf-8")
    failing = ValidationResult()
    release.check_review_evidence(tmp_path, failing)
    assert any("not bound" in error for error in failing.errors)
