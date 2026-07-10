from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from validate_khufu_v5_harness import validate_harness  # noqa: E402


class KhufuV5HarnessValidatorTests(unittest.TestCase):
    def _copy_harness(self, destination: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "docs" / "khufu-v5", destination / "docs" / "khufu-v5")
        (destination / "tools").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            PROJECT_ROOT / "tools" / "validate_khufu_v5_harness.py",
            destination / "tools" / "validate_khufu_v5_harness.py",
        )
        test_target = destination / "tools" / "tests" / "test_validate_khufu_v5_harness.py"
        test_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__), test_target)
        binding_source = (
            PROJECT_ROOT
            / "runs"
            / "khufu-mega-labyrinth-v5"
            / "build-input-binding.json"
        )
        binding_target = destination / binding_source.relative_to(PROJECT_ROOT)
        binding_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(binding_source, binding_target)
        binding = json.loads(binding_source.read_text(encoding="utf-8"))
        bound_entries = [binding["scene"], *binding["provenance"], *binding["inputs"]]
        for relative in {entry["path"] for entry in bound_entries}:
            source = PROJECT_ROOT / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copytree(
            PROJECT_ROOT / "work" / "fable-harness",
            destination / "work" / "fable-harness",
        )
        shutil.copytree(
            PROJECT_ROOT / "runs" / "khufu-v5-harness-20260710-gate0",
            destination / "runs" / "khufu-v5-harness-20260710-gate0",
        )
        (destination / "docs" / "research").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            PROJECT_ROOT / "docs" / "research" / "KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md",
            destination / "docs" / "research" / "KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md",
        )
        shutil.copy2(
            PROJECT_ROOT / "docs" / "PYRAMID_REFERENCE_MATCHED_V4_DESIGN.md",
            destination / "docs" / "PYRAMID_REFERENCE_MATCHED_V4_DESIGN.md",
        )
        gameplay_spec = destination / "Assets" / "_Project" / "Scripts" / "Gameplay"
        gameplay_spec.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            PROJECT_ROOT
            / "Assets"
            / "_Project"
            / "Scripts"
            / "Gameplay"
            / "TraitorEscapeMvpSpec.md",
            gameplay_spec / "TraitorEscapeMvpSpec.md",
        )
        status_text = (PROJECT_ROOT / "docs" / "khufu-v5" / "STATUS.md").read_text(encoding="utf-8")
        for line in status_text.splitlines():
            if not line.startswith("| KV5-E-"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 8:
                continue
            source = (PROJECT_ROOT / "docs" / "khufu-v5" / cells[5]).resolve()
            if not source.is_file():
                continue
            relative = source.relative_to(PROJECT_ROOT)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def _add_current_snapshot_fixture(self, root: Path) -> None:
        status = root / "docs" / "khufu-v5" / "STATUS.md"
        placeholder = "0" * 64
        status_text = status.read_text(encoding="utf-8")
        status_text += "\n- [x] Current snapshot mutation fixture; evidence: KV5-E-099\n"
        status_text += (
            "| KV5-E-099 | KV5-R-014 / KV5-T-001 | "
            "HEAD:0000000000000000000000000000000000000000+ARTIFACT:"
            + placeholder
            + " | Mutation fixture | passed | "
            "../research/KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md | 2026-07-10 | "
            "current-snapshot fixture |\n"
        )
        status.write_text(status_text, encoding="utf-8")
        artifact_sha = validate_harness(root).artifact_sha256
        rebound_lines = []
        for line in status.read_text(encoding="utf-8").splitlines():
            if "current-snapshot" in line:
                line = re.sub(
                    r"ARTIFACT:[0-9a-f]{64}",
                    "ARTIFACT:" + artifact_sha,
                    line,
                )
            rebound_lines.append(line)
        status.write_text("\n".join(rebound_lines) + "\n", encoding="utf-8")
        final_receipt = (
            root
            / "runs"
            / "khufu-mega-labyrinth-v5"
            / "final-harness-receipt.md"
        )
        if final_receipt.is_file():
            final_receipt.write_text(
                re.sub(
                    r"Artifact SHA256:\s*`[0-9a-f]{64}`",
                    "Artifact SHA256: `" + artifact_sha + "`",
                    final_receipt.read_text(encoding="utf-8"),
                ),
                encoding="utf-8",
            )
        report = validate_harness(root)
        self.assertTrue(report.passed, "\n".join(report.errors))

    def test_current_harness_passes(self) -> None:
        report = validate_harness(PROJECT_ROOT)
        self.assertTrue(report.passed, "\n".join(report.errors))

    def test_rules_document_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            (root / "docs" / "khufu-v5" / "RULES.md").unlink()
            report = validate_harness(root)
            self.assertTrue(any("RULES.md" in error for error in report.errors))

    def test_build_input_binding_manifest_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            (
                root
                / "runs"
                / "khufu-mega-labyrinth-v5"
                / "build-input-binding.json"
            ).unlink()
            report = validate_harness(root)
            self.assertTrue(
                any("missing build input binding manifest" in error for error in report.errors)
            )

    def test_build_input_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            quality = root / "ProjectSettings" / "QualitySettings.asset"
            quality.write_text(
                quality.read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertTrue(
                any("build binding hash mismatch" in error for error in report.errors)
            )

    def test_completed_status_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            status = root / "docs" / "khufu-v5" / "STATUS.md"
            status.write_text(
                status.read_text(encoding="utf-8") + "\n- [x] Unproved completion\n",
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertTrue(
                any("completed status lacks evidence reference" in error for error in report.errors)
            )

    def test_requirement_without_test_coverage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            test_plan = root / "docs" / "khufu-v5" / "TEST_PLAN.md"
            test_plan.write_text(
                test_plan.read_text(encoding="utf-8").replace("KV5-R-014", "KV5-R-999"),
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertIn(
                "requirement has no test matrix coverage: KV5-R-014",
                report.errors,
            )

    def test_accepted_fable_evidence_requires_ship_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            final_review = root / "work" / "fable-harness" / "final.md"
            final_review.write_text("A review without a verdict token.\n", encoding="utf-8")
            status = root / "docs" / "khufu-v5" / "STATUS.md"
            status_text = status.read_text(encoding="utf-8")
            status_text += "\n- [x] Final review complete; evidence: KV5-E-003\n"
            status_text += (
                "| KV5-E-003 | KV5-R-012 / KV5-T-014 | "
                "HEAD:0000000000000000000000000000000000000000 | Fable final review | accepted | "
                "../../work/fable-harness/final.md | 2026-07-10 | test fixture |\n"
            )
            status.write_text(status_text, encoding="utf-8")
            report = validate_harness(root)
            self.assertTrue(
                any("must contain exactly one verdict line" in error for error in report.errors)
            )

    def test_quoted_ship_token_with_final_revise_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            final_review = root / "work" / "fable-harness" / "final-token.md"
            final_review.write_text(
                "The requested token was `FABLE_VERDICT: ship`.\nFABLE_VERDICT: revise\n",
                encoding="utf-8",
            )
            status = root / "docs" / "khufu-v5" / "STATUS.md"
            status_text = status.read_text(encoding="utf-8")
            status_text += "\n- [x] Final review complete; evidence: KV5-E-099\n"
            status_text += (
                "| KV5-E-099 | KV5-R-012 / KV5-T-014 | "
                "HEAD:0000000000000000000000000000000000000000+ARTIFACT:"
                + ("0" * 64)
                + " | Fable final review | accepted | "
                "../../work/fable-harness/final-token.md | 2026-07-10 | fixture |\n"
            )
            status.write_text(status_text, encoding="utf-8")
            report = validate_harness(root)
            self.assertTrue(any("final verdict is revise" in error for error in report.errors))

    def test_warning_token_with_final_ship_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            final_review = root / "work" / "fable-harness" / "final-warning.md"
            final_review.write_text(
                "<system-warning>invalid review</system-warning>\nFABLE_VERDICT: ship\n",
                encoding="utf-8",
            )
            status = root / "docs" / "khufu-v5" / "STATUS.md"
            status_text = status.read_text(encoding="utf-8")
            status_text += "\n- [x] Final review complete; evidence: KV5-E-098\n"
            status_text += (
                "| KV5-E-098 | KV5-R-012 / KV5-T-014 | "
                "HEAD:0000000000000000000000000000000000000000+ARTIFACT:"
                + ("0" * 64)
                + " | Fable final review | accepted | "
                "../../work/fable-harness/final-warning.md | 2026-07-10 | fixture |\n"
            )
            status.write_text(status_text, encoding="utf-8")
            report = validate_harness(root)
            self.assertTrue(any("contains invalid token" in error for error in report.errors))

    def test_implementation_fable_call_warning_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            meta_path = (
                root
                / "work"
                / "fable-harness"
                / "khufu-v5-implementation-final-review.fable.md.meta.json"
            )
            meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
            meta["warnings"] = ["mutated warning"]
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            report = validate_harness(root)
            self.assertTrue(
                any(
                    "implementation Fable call metadata has warnings" in error
                    for error in report.errors
                )
            )

    def test_document_edit_invalidates_revision_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            self._add_current_snapshot_fixture(root)
            readme = root / "docs" / "khufu-v5" / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            report = validate_harness(root)
            self.assertTrue(any("revision mismatch" in error for error in report.errors))

    def test_tampered_receipt_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            receipt = root / "runs" / "khufu-v5-harness-20260710-gate0" / "pre-fable-receipt.md"
            receipt.write_text(
                re.sub(
                    r"Artifact SHA256: `([0-9a-f]{64})`",
                    "Artifact SHA256: `" + ("0" * 64) + "`",
                    receipt.read_text(encoding="utf-8"),
                ),
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertTrue(any("receipt hash does not match" in error for error in report.errors))

    def test_validator_edit_invalidates_revision_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
            self._add_current_snapshot_fixture(root)
            validator = root / "tools" / "validate_khufu_v5_harness.py"
            validator.write_text(
                validator.read_text(encoding="utf-8") + "\n# mutation\n",
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertTrue(any("revision mismatch" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
