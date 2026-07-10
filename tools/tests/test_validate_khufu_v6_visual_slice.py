from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from validate_khufu_v6_visual_slice import (  # noqa: E402
    CAPTURES,
    DOC_ROOT,
    DOC_TOKENS,
    MATERIALS,
    RUN_ROOT,
    SCENE,
    SURFACES,
    V6_SOURCES,
    WINDOWS_BUILD_SOURCE,
    validate,
)


class KhufuV6VisualSliceValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_parent = PROJECT_ROOT / "Temp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="v6-validator-", dir=temp_parent)
        self.root = Path(self.temp.name)
        self._copy_fixture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _copy(self, relative: Path | str, *, hardlink: bool = False) -> None:
        relative = Path(relative)
        source = PROJECT_ROOT / relative
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if hardlink:
            os.link(source, target)
        else:
            shutil.copy2(source, target)

    def _copy_fixture(self) -> None:
        baseline = PROJECT_ROOT / RUN_ROOT / "frozen-inputs-baseline.md"
        self._copy(RUN_ROOT / "frozen-inputs-baseline.md")
        for _, raw_path in re.findall(
            r"^\| `([0-9a-f]{64})` \| `([^`]+)` \|$",
            baseline.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            self._copy(raw_path)

        for relative in (
            SCENE,
            *V6_SOURCES.values(),
            WINDOWS_BUILD_SOURCE,
            Path("tools/validate_khufu_v6_visual_slice.py"),
            Path("tools/validate_khufu_v5_performance.py"),
            RUN_ROOT / "validation.md",
            RUN_ROOT / "idempotence.md",
            RUN_ROOT / "v5-playmode-regression.md",
            RUN_ROOT / "captures/manifest.md",
            RUN_ROOT / "windows-build.md",
            RUN_ROOT / "performance-final/validation.md",
            RUN_ROOT / "performance-final/v6-final-performance.md",
            RUN_ROOT / "performance-final/player.log",
            RUN_ROOT / "performance-final/binding.json",
            Path("runs/khufu-mega-labyrinth-v5/playmode-probe.md"),
            Path("runs/khufu-mega-labyrinth-v5/gate4-acceptance.md"),
            Path("runs/khufu-mega-labyrinth-v5/performance-budget.json"),
            *(DOC_ROOT / name for name in DOC_TOKENS),
        ):
            self._copy(relative)

        for name in CAPTURES:
            self._copy(RUN_ROOT / "captures" / f"{name}.png")
        for name in MATERIALS:
            self._copy(Path("Assets/_Project/Materials/KhufuV6") / f"{name}.mat")
            self._copy(Path("Assets/_Project/Materials/KhufuV6") / f"{name}.mat.meta")
        for surface in SURFACES:
            for kind in ("Albedo", "Normal"):
                self._copy(
                    Path("Assets/_Project/Art/Generated/KhufuV6VisualSlice/Textures")
                    / f"V6_{surface}_{kind}.png"
                )
                self._copy(
                    Path("Assets/_Project/Art/Generated/KhufuV6VisualSlice/Textures")
                    / f"V6_{surface}_{kind}.png.meta"
                )
        for name in ("initial", "operator"):
            self._copy(RUN_ROOT / "performance-final" / f"v6-final-windows-player-{name}.png")

        for relative in (
            Path("Builds/KhufuV6/ChannelPlayKhufuV6.exe"),
            Path("Builds/KhufuV6/UnityPlayer.dll"),
            Path("Builds/KhufuV6/ChannelPlayKhufuV6_Data/level0"),
            RUN_ROOT / "performance-final/v6-final.raw",
        ):
            self._copy(relative, hardlink=True)

        fable = self.root / "work/fable-harness/khufu-v6-visual-slice-final-review.fable.md"
        fable.parent.mkdir(parents=True, exist_ok=True)
        fable.write_text("Synthetic test fixture.\nFABLE_VERDICT: ship\n", encoding="utf-8")

    def test_complete_fixture_passes(self) -> None:
        report = validate(self.root)
        self.assertTrue(report.passed, "\n".join(report.errors))

    def test_frozen_input_mutation_fails(self) -> None:
        target = self.root / "Packages/manifest.json"
        target.write_bytes(target.read_bytes() + b"\nmutation\n")
        report = validate(self.root)
        self.assertTrue(any("frozen input hash mismatch" in error for error in report.errors))

    def test_stale_capture_scene_binding_fails(self) -> None:
        manifest = self.root / RUN_ROOT / "captures/manifest.md"
        text = manifest.read_text(encoding="utf-8")
        text = re.sub(r"Scene SHA256: `[0-9a-f]{64}`", "Scene SHA256: `" + ("0" * 64) + "`", text)
        manifest.write_text(text, encoding="utf-8")
        report = validate(self.root)
        self.assertIn("capture manifest is not bound to the current scene", report.errors)

    def test_duplicate_capture_fails(self) -> None:
        source = self.root / RUN_ROOT / "captures/hero_valley_to_pyramid.png"
        target = self.root / RUN_ROOT / "captures/temple_hub_detail.png"
        target.unlink()
        shutil.copy2(source, target)
        report = validate(self.root)
        self.assertTrue(any("duplicate" in error for error in report.errors))

    def test_unrestored_player_settings_fails(self) -> None:
        receipt = self.root / RUN_ROOT / "windows-build.md"
        text = receipt.read_text(encoding="utf-8")
        text = re.sub(
            r"Player settings restored SHA256: `[0-9a-f]{64}`",
            "Player settings restored SHA256: `" + ("0" * 64) + "`",
            text,
        )
        receipt.write_text(text, encoding="utf-8")
        report = validate(self.root)
        self.assertTrue(any("was not restored" in error for error in report.errors))

    def test_performance_budget_mutation_fails(self) -> None:
        receipt = self.root / RUN_ROOT / "performance-final/v6-final-performance.md"
        text = receipt.read_text(encoding="utf-8")
        text = re.sub(
            r"(Frame time median: `[0-9.]+ ms`; p95: `)[0-9.]+( ms`)",
            r"\g<1>99.000\g<2>",
            text,
        )
        receipt.write_text(text, encoding="utf-8")
        report = validate(self.root)
        self.assertTrue(any("frame_p95_ms" in error for error in report.errors))

    def test_stale_performance_scene_binding_fails(self) -> None:
        binding = self.root / RUN_ROOT / "performance-final/binding.json"
        text = binding.read_text(encoding="utf-8")
        scene_hash = validate(self.root).observed["scene_sha256"]
        binding.write_text(text.replace(str(scene_hash), "0" * 64, 1), encoding="utf-8")
        report = validate(self.root)
        self.assertIn("performance binding is not bound to the current scene", report.errors)

    def test_stale_playmode_scene_binding_fails(self) -> None:
        receipt = self.root / RUN_ROOT / "v5-playmode-regression.md"
        text = receipt.read_text(encoding="utf-8")
        text = re.sub(r"Scene SHA256: `[0-9a-f]{64}`", "Scene SHA256: `" + ("0" * 64) + "`", text)
        receipt.write_text(text, encoding="utf-8")
        report = validate(self.root)
        self.assertIn("V5 PlayMode receipt is not bound to the current scene", report.errors)

    def test_stale_windows_build_scene_binding_fails(self) -> None:
        receipt = self.root / RUN_ROOT / "windows-build.md"
        text = receipt.read_text(encoding="utf-8")
        text = re.sub(
            r"Scene source SHA256: `[0-9a-f]{64}`",
            "Scene source SHA256: `" + ("0" * 64) + "`",
            text,
        )
        receipt.write_text(text, encoding="utf-8")
        report = validate(self.root)
        self.assertIn("Windows build is not bound to the current scene", report.errors)

    def test_fable_revise_fails(self) -> None:
        fable = self.root / "work/fable-harness/khufu-v6-visual-slice-final-review.fable.md"
        fable.write_text("FABLE_VERDICT: revise\n", encoding="utf-8")
        report = validate(self.root)
        self.assertIn("Fable final verdict is revise, not ship", report.errors)


if __name__ == "__main__":
    unittest.main()
