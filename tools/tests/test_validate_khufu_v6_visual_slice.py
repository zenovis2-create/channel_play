from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
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

V6_BASELINE_REVISION = "9f4158673f9b4cdcdea94c74b71638413c5d77fe"
V6_PACKAGE_INPUT_REVISION = "10e8ed0d3cc7be82c2ec8e3d69c618da2f160d5a"
V6_RELEASE_REVISION = "d35070c53b3643f9e6657f9309eb697214f91678"


class KhufuV6VisualSliceValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_parent = PROJECT_ROOT / "Temp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="v6-validator-", dir=temp_parent)
        self.root = Path(self.temp.name)
        self._copy_fixture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _copy(self, relative: Path | str) -> None:
        relative = Path(relative)
        source = PROJECT_ROOT / relative
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def _copy_git_blob(self, revision: str, relative: Path | str) -> None:
        relative = Path(relative)
        result = subprocess.run(
            ["git", "show", f"{revision}:{relative.as_posix()}"],
            cwd=PROJECT_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        )
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)

    def _copy_v5_probe_receipt(self) -> None:
        relative = Path("runs/khufu-mega-labyrinth-v5/playmode-probe.md")
        result = subprocess.run(
            ["git", "show", f"{V6_RELEASE_REVISION}:{relative.as_posix()}"],
            cwd=PROJECT_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        )
        lines = result.stdout.decode("utf-8").splitlines()
        content = "\n".join(lines[:2]) + "\n" + "\r\n".join(lines[2:]) + "\r\n"
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))

    def _write_synthetic_build_outputs(self) -> None:
        outputs = {
            "Player executable": (
                Path("Builds/KhufuV6/ChannelPlayKhufuV6.exe"),
                b"synthetic Khufu V6 player fixture\n",
            ),
            "UnityPlayer": (
                Path("Builds/KhufuV6/UnityPlayer.dll"),
                b"synthetic Khufu V6 UnityPlayer fixture\n",
            ),
            "Built level": (
                Path("Builds/KhufuV6/ChannelPlayKhufuV6_Data/level0"),
                b"synthetic Khufu V6 level fixture\n",
            ),
        }
        for _, (relative, content) in outputs.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        receipt = self.root / RUN_ROOT / "windows-build.md"
        receipt_text = receipt.read_text(encoding="utf-8")
        for label, (_, content) in outputs.items():
            digest = hashlib.sha256(content).hexdigest()
            receipt_text = re.sub(
                rf"({re.escape(label)} SHA256: `)[0-9a-f]{{64}}(`)",
                rf"\g<1>{digest}\g<2>",
                receipt_text,
            )
        receipt.write_text(receipt_text, encoding="utf-8")

        binding_path = self.root / RUN_ROOT / "performance-final/binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        for key, label in (("player", "Player executable"), ("built_level", "Built level")):
            relative, content = outputs[label]
            binding[key]["path"] = relative.as_posix()
            binding[key]["bytes"] = len(content)
            binding[key]["sha256"] = hashlib.sha256(content).hexdigest()
        binding_path.write_text(
            json.dumps(binding, indent=2) + "\n",
            encoding="utf-8",
        )

    def _copy_fixture(self) -> None:
        baseline = PROJECT_ROOT / RUN_ROOT / "frozen-inputs-baseline.md"
        self._copy(RUN_ROOT / "frozen-inputs-baseline.md")
        for _, raw_path in re.findall(
            r"^\| `([0-9a-f]{64})` \| `([^`]+)` \|$",
            baseline.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            revision = (
                V6_PACKAGE_INPUT_REVISION
                if raw_path.startswith("Packages/")
                else V6_BASELINE_REVISION
            )
            self._copy_git_blob(revision, raw_path)

        self._copy_git_blob(V6_RELEASE_REVISION, SCENE)
        for relative in (*V6_SOURCES.values(), WINDOWS_BUILD_SOURCE):
            self._copy_git_blob(V6_RELEASE_REVISION, relative)
        self._copy_v5_probe_receipt()

        for relative in (
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

        self._copy(RUN_ROOT / "performance-final/v6-final.raw")
        self._write_synthetic_build_outputs()

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
