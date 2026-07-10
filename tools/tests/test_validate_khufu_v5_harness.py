from __future__ import annotations

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

    def test_current_harness_passes(self) -> None:
        report = validate_harness(PROJECT_ROOT)
        self.assertTrue(report.passed, "\n".join(report.errors))

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

    def test_document_edit_invalidates_revision_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_harness(root)
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
            validator = root / "tools" / "validate_khufu_v5_harness.py"
            validator.write_text(
                validator.read_text(encoding="utf-8") + "\n# mutation\n",
                encoding="utf-8",
            )
            report = validate_harness(root)
            self.assertTrue(any("revision mismatch" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
