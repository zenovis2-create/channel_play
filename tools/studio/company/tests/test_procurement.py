from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.errors import CompanyError
from tools.studio.company.procurement import (
    OWNER_DECISION_FIELDS,
    PROCUREMENT_DECISION_SCHEMA,
    TRUTH_PEN_CANDIDATES,
    apply_procurement_answers,
    evaluate_procurement_outreach,
    preview_procurement_answers,
    procurement_answer_digest,
    procurement_decision_init,
    procurement_outreach_check,
)


class ProcurementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        self._write(
            self.root / "asset_pipeline/index.json",
            {"assets": [{"id": "truth_pen", "status": "briefed"}]},
        )
        self._write_text(
            self.root / "asset_pipeline/briefs/truth_pen_commission_rfp.md",
            "# RFP\n",
        )
        self._write_text(
            self.root / "docs/research/truth_pen_artist_procurement_packet.md",
            "# Procurement Packet\n",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_init_is_fail_closed_and_preserves_existing_decision(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        data = self._read(manifest)

        self.assertEqual(data["schema"], PROCUREMENT_DECISION_SCHEMA)
        self.assertFalse(data["outreach"]["authorized"])
        self.assertFalse(evaluate_procurement_outreach(self.root, "truth_pen")["passed"])

        data["task_id"] = "task-0099"
        self._write(manifest, data)
        self.assertEqual(procurement_decision_init(self.root, "truth_pen"), manifest)
        self.assertEqual(self._read(manifest)["task_id"], "task-0099")

    def test_default_check_writes_fail_receipt_and_blocks_contact(self) -> None:
        procurement_decision_init(self.root, "truth_pen")

        with self.assertRaisesRegex(CompanyError, "Proposal outreach blocked"):
            procurement_outreach_check(self.root, "truth_pen")

        receipt = (
            self.root
            / "runs/asset-procurement-truth_pen/outreach_readiness_check.md"
        )
        text = receipt.read_text(encoding="utf-8")
        self.assertIn("Result: **FAIL**", text)
        self.assertIn("All artist contact remains blocked", text)
        self.assertIn("Gate A `PASS`", text)

    def test_complete_decision_authorizes_proposal_only(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        self._write(manifest, self._complete_decision(manifest))

        result = evaluate_procurement_outreach(self.root, "truth_pen")
        self.assertTrue(result["passed"], result["errors"])

        receipt = procurement_outreach_check(self.root, "truth_pen")
        text = receipt.read_text(encoding="utf-8")
        self.assertIn("Result: **PASS**", text)
        self.assertIn("Proposal-only outreach is authorized", text)
        self.assertIn("Artwork and source-file requests remain blocked", text)

    def test_answer_preview_validates_in_memory_without_authorizing(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        before = manifest.read_bytes()

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )

        self.assertTrue(result["previewOnly"])
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(result["contactAuthorized"])
        self.assertFalse(result["receiptCreated"])
        self.assertEqual(result["answerCount"], 16)
        self.assertEqual(result["expectedAnswerCount"], 16)
        self.assertEqual(result["acceptedFields"], list(OWNER_DECISION_FIELDS))
        self.assertEqual(result["missingFields"], [])
        self.assertEqual(result["changeCount"], 16)
        self.assertEqual(result["unchangedCount"], 0)
        self.assertEqual(
            result["changedFields"],
            list(OWNER_DECISION_FIELDS),
        )
        self.assertEqual(result["unchangedFields"], [])
        self.assertTrue(result["protectedStatePreserved"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_answer_preview_reports_partial_fields_without_writing(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        before = manifest.read_bytes()

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            {"owner.governing_jurisdiction": "KR"},
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["answerCount"], 1)
        self.assertEqual(
            result["acceptedFields"],
            ["owner.governing_jurisdiction"],
        )
        self.assertNotIn(
            "owner.governing_jurisdiction",
            result["missingFields"],
        )
        self.assertEqual(result["changeCount"], 1)
        self.assertEqual(result["unchangedCount"], 0)
        self.assertEqual(
            result["changedFields"],
            ["owner.governing_jurisdiction"],
        )
        self.assertEqual(result["unchangedFields"], [])
        self.assertTrue(result["protectedStatePreserved"])
        self.assertIn(
            "decision_status must be approved_for_proposal_outreach",
            result["errors"],
        )
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_answer_preview_reports_unchanged_fields_without_values(
        self,
    ) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        before = manifest.read_bytes()

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            {"outreach.authorized": False},
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["changeCount"], 0)
        self.assertEqual(result["unchangedCount"], 1)
        self.assertEqual(result["changedFields"], [])
        self.assertEqual(
            result["unchangedFields"],
            ["outreach.authorized"],
        )
        self.assertTrue(result["protectedStatePreserved"])
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_answer_preview_change_summary_is_json_type_aware(self) -> None:
        procurement_decision_init(self.root, "truth_pen")

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            {"outreach.authorized": 0},
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["changeCount"], 1)
        self.assertEqual(result["unchangedCount"], 0)
        self.assertEqual(
            result["changedFields"],
            ["outreach.authorized"],
        )

    def test_answer_preview_noop_is_valid_but_redacts_all_values(
        self,
    ) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        complete = self._complete_decision(manifest)
        complete["owner"]["secure_record_id"] = (
            "vault:123e4567-e89b-42d3-a456-426614174000"
        )
        self._write(manifest, complete)
        answers = self._owner_answers(complete)
        before = manifest.read_bytes()

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )
        encoded = json.dumps(result, ensure_ascii=False)

        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["changeCount"], 0)
        self.assertEqual(result["unchangedCount"], 16)
        self.assertEqual(result["changedFields"], [])
        self.assertEqual(
            result["unchangedFields"],
            list(OWNER_DECISION_FIELDS),
        )
        self.assertTrue(result["protectedStatePreserved"])
        self.assertNotIn("123e4567-e89b-42d3-a456-426614174000", encoded)
        self.assertNotIn("project_owner", encoded)
        self.assertNotIn("cynthia_ignacio", encoded)
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_answer_preview_rejects_unknown_fields_without_echoing_values(
        self,
    ) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        answers["owner.private_message"] = "must-not-be-echoed"

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )
        encoded = json.dumps(result, ensure_ascii=False)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("1 unsupported field" in error for error in result["errors"])
        )
        self.assertNotIn("private_message", encoded)
        self.assertNotIn("must-not-be-echoed", encoded)

    def test_answer_preview_redacts_unknown_candidate_values(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        answers["outreach.candidate_ids"] = ["private-person-name"]

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )
        encoded = json.dumps(result, ensure_ascii=False)

        self.assertFalse(result["valid"])
        self.assertIn(
            "outreach.candidate_ids contains unsupported candidate IDs",
            result["errors"],
        )
        self.assertNotIn("private-person-name", encoded)

    def test_answer_preview_rejects_nonfinite_values(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        answers["commercial.budget_ceiling"] = float("nan")

        result = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )

        self.assertFalse(result["valid"])
        self.assertIn(
            "answers contain a non-finite numeric value",
            result["errors"],
        )
        self.assertFalse((self.root / "runs").exists())

    def test_answer_preview_requires_an_object(self) -> None:
        procurement_decision_init(self.root, "truth_pen")

        with self.assertRaisesRegex(CompanyError, "must be a JSON object"):
            preview_procurement_answers(
                self.root,
                "truth_pen",
                ["not", "an", "object"],
            )

    def test_answer_digest_requires_exact_canonical_fields(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))

        digest = procurement_answer_digest(answers)

        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        answers.pop("decision_status")
        with self.assertRaisesRegex(CompanyError, "every canonical"):
            procurement_answer_digest(answers)

    def test_apply_answers_atomically_saves_without_receipt(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        preview = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )
        real_replace = os.replace
        replace_calls = []

        def record_replace(source, target) -> None:
            replace_calls.append((Path(source), Path(target)))
            real_replace(source, target)

        with patch(
            "tools.studio.company.procurement.os.replace",
            side_effect=record_replace,
        ):
            result = apply_procurement_answers(
                self.root,
                "truth_pen",
                answers,
                preview["manifestSha256"],
            )

        self.assertTrue(result["saved"])
        self.assertFalse(result["contactAuthorized"])
        self.assertFalse(result["receiptCreated"])
        self.assertEqual(result["nextCommand"], "asset.procurementCheck")
        self.assertEqual(len(replace_calls), 1)
        temporary, target = replace_calls[0]
        self.assertEqual(temporary.parent, manifest.parent)
        self.assertEqual(target, manifest)
        self.assertFalse(temporary.exists())
        self.assertTrue(
            evaluate_procurement_outreach(
                self.root,
                "truth_pen",
            )["passed"]
        )
        self.assertFalse((self.root / "runs").exists())

    def test_apply_answers_rejects_stale_manifest_without_writing(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        answers = self._owner_answers(self._complete_decision(manifest))
        before = manifest.read_bytes()

        with self.assertRaisesRegex(CompanyError, "changed"):
            apply_procurement_answers(
                self.root,
                "truth_pen",
                answers,
                "0" * 64,
            )

        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_apply_answers_rejects_noop_without_writing(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        complete = self._complete_decision(manifest)
        self._write(manifest, complete)
        answers = self._owner_answers(complete)
        preview = preview_procurement_answers(
            self.root,
            "truth_pen",
            answers,
        )
        before = manifest.read_bytes()

        with patch(
            "tools.studio.company.procurement.os.replace",
        ) as replace:
            with self.assertRaisesRegex(CompanyError, "do not change"):
                apply_procurement_answers(
                    self.root,
                    "truth_pen",
                    answers,
                    preview["manifestSha256"],
                )

        replace.assert_not_called()
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse((self.root / "runs").exists())

    def test_sensitive_fields_and_privacy_flags_fail(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        data = self._complete_decision(manifest)
        data["owner"]["secure_record_id"] = "UNKNOWN"
        data["owner"]["bank_account"] = "must-not-be-here"
        data["privacy"]["banking_data_in_repo"] = True
        self._write(manifest, data)

        result = evaluate_procurement_outreach(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertIn(
            "owner contains unsupported field: bank_account",
            result["errors"],
        )
        self.assertIn(
            "owner.secure_record_id must use vault:<canonical-lowercase-UUID>",
            result["errors"],
        )
        self.assertIn(
            "privacy.banking_data_in_repo must be false",
            result["errors"],
        )

    def test_sensitive_payload_fields_are_rejected(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        for field in (
            "identity_document",
            "tax_id",
            "bank_account",
            "payment_credential",
            "signature",
            "private_message",
            "email",
        ):
            with self.subTest(field=field):
                data = self._complete_decision(manifest)
                data["owner"][field] = "must-not-be-here"
                self._write(manifest, data)
                errors = evaluate_procurement_outreach(
                    self.root,
                    "truth_pen",
                )["errors"]
                self.assertIn(
                    f"owner contains unsupported field: {field}",
                    errors,
                )

    def test_scope_candidate_and_schedule_validation(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        data = self._complete_decision(manifest)
        data["outreach"]["scope"] = "one"
        data["outreach"]["candidate_ids"] = [
            "cynthia_ignacio",
            "unknown_artist",
        ]
        data["schedule"]["desired_delivery_date"] = data["schedule"][
            "proposal_deadline"
        ]
        self._write(manifest, data)

        errors = evaluate_procurement_outreach(self.root, "truth_pen")["errors"]

        self.assertTrue(any("unknown candidates" in error for error in errors))
        self.assertIn(
            "outreach.scope one requires exactly one candidate",
            errors,
        )
        self.assertIn(
            "schedule.desired_delivery_date must be after proposal_deadline",
            errors,
        )

    def test_non_string_candidate_entry_fails_closed(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        data = self._complete_decision(manifest)
        data["outreach"]["candidate_ids"] = [{"id": "cynthia_ignacio"}]
        self._write(manifest, data)

        result = evaluate_procurement_outreach(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertIn(
            "outreach.candidate_ids entries must be strings",
            result["errors"],
        )

    def test_sensitive_secure_record_values_are_rejected(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        for value in (
            "Jane-Doe",
            "123-45-6789",
            "4111111111111111",
            "vault:NOT-A-UUID",
            "vault:550E8400-E29B-41D4-A716-446655440000",
        ):
            with self.subTest(value=value):
                data = self._complete_decision(manifest)
                data["owner"]["secure_record_id"] = value
                self._write(manifest, data)
                result = evaluate_procurement_outreach(
                    self.root,
                    "truth_pen",
                )
                self.assertFalse(result["passed"])
                self.assertIn(
                    "owner.secure_record_id must use "
                    "vault:<canonical-lowercase-UUID>",
                    result["errors"],
                )

    def test_nonfinite_budget_values_are_rejected(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                data = self._complete_decision(manifest)
                data["commercial"]["budget_ceiling"] = value
                self._write(manifest, data)
                result = evaluate_procurement_outreach(
                    self.root,
                    "truth_pen",
                )
                self.assertFalse(result["passed"])
                self.assertTrue(
                    any(
                        "non-standard numeric constant is prohibited" in error
                        for error in result["errors"]
                    )
                )

    def test_authorization_flags_and_all_scope_fail_closed(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        data = self._complete_decision(manifest)
        data["outreach"]["proposal_only"] = False
        data["outreach"][
            "source_creation_blocked_until_signed_agreement_and_gate_a_pass"
        ] = False
        data["outreach"]["candidate_ids"] = ["cynthia_ignacio"]
        self._write(manifest, data)

        errors = evaluate_procurement_outreach(self.root, "truth_pen")["errors"]

        self.assertIn("outreach.proposal_only must be true", errors)
        self.assertTrue(
            any("keep source creation blocked" in error for error in errors)
        )
        self.assertIn(
            "outreach.scope all requires every shortlisted candidate",
            errors,
        )

    def test_bound_rfp_drift_invalidates_authorization(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        self._write(manifest, self._complete_decision(manifest))
        rfp = self.root / "asset_pipeline/briefs/truth_pen_commission_rfp.md"
        rfp.write_text("# RFP\nRequest artwork immediately.\n", encoding="utf-8")

        result = evaluate_procurement_outreach(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("records.rfp_sha256 must match" in error for error in result["errors"])
        )

    def test_malformed_json_writes_fail_receipt(self) -> None:
        manifest = procurement_decision_init(self.root, "truth_pen")
        manifest.write_text("{broken", encoding="utf-8")

        with self.assertRaisesRegex(CompanyError, "Proposal outreach blocked"):
            procurement_outreach_check(self.root, "truth_pen")

        receipt = (
            self.root
            / "runs/asset-procurement-truth_pen/outreach_readiness_check.md"
        )
        self.assertIn(
            "Result: **FAIL**",
            receipt.read_text(encoding="utf-8"),
        )

    def test_unknown_asset_check_is_side_effect_free(self) -> None:
        with self.assertRaisesRegex(
            CompanyError,
            "Procurement workflow is not configured",
        ):
            procurement_outreach_check(self.root, "unknown")

        self.assertFalse((self.root / "runs").exists())

    def _complete_decision(self, manifest: Path) -> dict:
        data = self._read(manifest)
        proposal_deadline = date.today() + timedelta(days=14)
        desired_delivery = proposal_deadline + timedelta(days=21)
        data.update(
            {
                "decision_status": "approved_for_proposal_outreach",
                "owner": {
                    "secure_record_id": (
                        "vault:550e8400-e29b-41d4-a716-446655440000"
                    ),
                    "authorized_signer_role": "project_owner",
                    "governing_jurisdiction": "KR",
                },
                "commercial": {
                    "budget_ceiling": 1500,
                    "currency": "USD",
                    "payment_route": "upwork",
                    "tax_vendor_process_confirmed_securely": True,
                },
                "schedule": {
                    "proposal_deadline": proposal_deadline.isoformat(),
                    "desired_delivery_date": desired_delivery.isoformat(),
                    "revision_limit": 2,
                },
                "outreach": {
                    "authorized": True,
                    "authorized_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "all",
                    "candidate_ids": sorted(TRUTH_PEN_CANDIDATES),
                    "proposal_only": True,
                    "source_creation_blocked_until_signed_agreement_and_gate_a_pass": True,
                },
                "privacy": {
                    "private_identity_documents_in_repo": False,
                    "tax_data_in_repo": False,
                    "banking_data_in_repo": False,
                    "payment_credentials_in_repo": False,
                    "sensitive_data_stored_outside_repo": True,
                },
            }
        )
        return data

    @staticmethod
    def _owner_answers(data: dict) -> dict:
        answers = {}
        for field in OWNER_DECISION_FIELDS:
            if "." not in field:
                answers[field] = data[field]
                continue
            section, key = field.split(".", 1)
            answers[field] = data[section][key]
        return answers

    @staticmethod
    def _read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
