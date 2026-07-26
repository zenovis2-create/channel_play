from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.asset_forge import asset_forge_new
from tools.studio.company.asset_gate import (
    CRITIC_APPROVAL_SCHEMA,
    asset_gate_a_check,
    asset_gate_a_init,
    asset_gate_b_check,
    asset_gate_b_init,
    evaluate_asset_gate_a,
    evaluate_asset_gate_b,
    gate_a_manifest_path,
    sha256_file,
    sha256_gate_manifest,
)
from tools.studio.company.assets import asset_new, asset_prepare, asset_status
from tools.studio.company.errors import CompanyError
from tools.studio.company.image_to_blender import image3d_generate, image3d_new


class AssetGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_init_preserves_lifecycle_and_records_pending_gate(self) -> None:
        self._track("truth_pen", status="accepted")

        manifest = asset_gate_a_init(self.root, "truth_pen")

        data = self._read(manifest)
        self.assertEqual(data["source_path"], "unselected")
        self.assertEqual(data["rights"]["commercial_use"], "UNKNOWN")
        asset = self._asset("truth_pen")
        self.assertEqual(asset["status"], "accepted")
        self.assertEqual(asset["source_gate_status"], "pending")
        self.assertTrue(asset["source_gate_required"])

    def test_missing_and_unknown_checks_are_side_effect_free(self) -> None:
        self._track("truth_pen")
        original_index = (self.root / "asset_pipeline/index.json").read_text(
            encoding="utf-8"
        )

        with self.assertRaisesRegex(CompanyError, "Gate A manifest missing"):
            asset_gate_a_check(self.root, "truth_pen")
        with self.assertRaisesRegex(CompanyError, "Unknown asset"):
            asset_gate_a_check(self.root, "unknown")

        self.assertFalse((self.root / "runs").exists())
        self.assertEqual(
            (self.root / "asset_pipeline/index.json").read_text(encoding="utf-8"),
            original_index,
        )

    def test_invalid_manifest_shape_writes_deterministic_fail_receipt(self) -> None:
        self._track("truth_pen", status="accepted")
        manifest = gate_a_manifest_path(self.root, "truth_pen")
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("[]\n", encoding="utf-8")

        with self.assertRaisesRegex(CompanyError, "top level must be a JSON object"):
            asset_gate_a_check(self.root, "truth_pen")

        receipt = self.root / "runs/asset-gate-a-truth_pen/gate_a_check.md"
        self.assertIn("Result: **FAIL**", receipt.read_text(encoding="utf-8"))
        asset = self._asset("truth_pen")
        self.assertEqual(asset["status"], "accepted")
        self.assertEqual(asset["source_gate_status"], "blocked")

    def test_unrelated_approved_markdown_cannot_authorize_gate(self) -> None:
        manifest = self._complete_gate_a("truth_pen", "openai", approve=False)
        approval = self.root / "reviews/truth_pen_gate_a.json"
        approval.parent.mkdir(parents=True, exist_ok=True)
        approval.write_text("Verdict: APPROVED\n", encoding="utf-8")

        result = evaluate_asset_gate_a(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("unreadable JSON" in error for error in result["errors"])
        )
        self.assertEqual(self._read(manifest)["critic_review"]["receipt"], approval.relative_to(self.root).as_posix())

    def test_manifest_tamper_invalidates_bound_critic_approval(self) -> None:
        manifest = self._complete_gate_a("truth_pen", "openai")
        data = self._read(manifest)
        data["applicable_jurisdiction"] = "Changed after review"
        self._write(manifest, data)

        result = evaluate_asset_gate_a(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("manifest_sha256" in error for error in result["errors"])
        )

    def test_gate_manifest_hash_ignores_line_endings_only(self) -> None:
        manifest = self._complete_gate_a("truth_pen", "openai")
        lf_bytes = (
            manifest.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        )
        manifest.write_bytes(lf_bytes)
        canonical_hash = sha256_gate_manifest(manifest)
        raw_lf_hash = sha256_file(manifest)

        manifest.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))

        self.assertEqual(sha256_gate_manifest(manifest), canonical_hash)
        self.assertNotEqual(sha256_file(manifest), raw_lf_hash)
        self.assertTrue(evaluate_asset_gate_a(self.root, "truth_pen")["passed"])

        source = self.root / "source.bin"
        source.write_bytes(b"line-one\r\nline-two")
        source_hash = sha256_file(source)
        source.write_bytes(b"line-one\nline-two")
        self.assertNotEqual(sha256_file(source), source_hash)

    def test_complete_source_paths_pass(self) -> None:
        for source_path in ("commissioned_human", "openai", "cc0"):
            with self.subTest(source_path=source_path):
                asset_id = f"truth_pen_{source_path}"
                self._complete_gate_a(asset_id, source_path)

                receipt = asset_gate_a_check(self.root, asset_id)

                self.assertIn("Result: **PASS**", receipt.read_text(encoding="utf-8"))
                self.assertEqual(self._asset(asset_id)["status"], "briefed")
                self.assertEqual(
                    self._asset(asset_id)["source_gate_status"],
                    "approved",
                )

    def test_openai_mandatory_risk_records_fail_closed(self) -> None:
        manifest = self._complete_gate_a("truth_pen", "openai", approve=False)
        data = self._read(manifest)
        data["path_details"]["non_uniqueness_acknowledged"] = False
        data["path_details"]["ai_provenance_record"] = ""
        self._write(manifest, data)

        result = evaluate_asset_gate_a(self.root, "truth_pen")

        self.assertFalse(result["passed"])
        self.assertIn(
            "path_details.non_uniqueness_acknowledged must be true",
            result["errors"],
        )
        self.assertIn(
            "path_details.ai_provenance_record is required",
            result["errors"],
        )

    def test_gate_a_alone_cannot_unlock_production(self) -> None:
        self._complete_gate_a("truth_pen", "openai")
        image3d_new(
            self.root,
            "truth_pen",
            provider="pixal3d",
            source_image="asset_pipeline/incoming_2d/truth_pen/concept.png",
        )

        job = self._read(
            self.root
            / "asset_pipeline/image_to_blender/truth_pen/image3d_job.json"
        )
        self.assertEqual(job["status"], "waiting_for_gate_b")
        self.assertEqual(job["pipeline"][0]["status"], "waiting_for_image")
        self.assertEqual(job["pipeline"][1]["status"], "blocked_by_gate_b")
        self.assertEqual(job["pipeline"][2]["status"], "blocked_by_gate_b")
        self.assertEqual(job["pipeline"][3]["status"], "blocked_by_gate_b")
        with self.assertRaisesRegex(CompanyError, "Gate B approval required"):
            asset_status(self.root, "truth_pen", "generated")
        with self.assertRaisesRegex(CompanyError, "Gate B approval required"):
            image3d_generate(self.root, "truth_pen", provider="pixal3d")

    def test_complete_gate_b_unlocks_protected_status_only(self) -> None:
        self._complete_gate_b("truth_pen", provider="local")

        asset_status(self.root, "truth_pen", "generated")

        asset = self._asset("truth_pen")
        self.assertEqual(asset["status"], "generated")
        self.assertEqual(asset["source_gate_status"], "approved")
        self.assertEqual(asset["production_gate_status"], "approved")

    def test_gate_b_rejects_provider_mismatch_before_runtime(self) -> None:
        source = self._complete_gate_b("truth_pen", provider="pixal3d")
        image3d_new(
            self.root,
            "truth_pen",
            provider="pixal3d",
            source_image=source.relative_to(self.root).as_posix(),
        )

        with self.assertRaisesRegex(CompanyError, "approves provider pixal3d, not local"):
            image3d_generate(self.root, "truth_pen", provider="local")

        self.assertFalse(
            (
                self.root
                / "runs/image-to-blender-truth_pen/model_generation_receipt.md"
            ).exists()
        )

    def test_nonlocal_provider_failure_never_falls_back_to_local(self) -> None:
        source = self._complete_gate_b("truth_pen", provider="pixal3d")
        image3d_new(
            self.root,
            "truth_pen",
            provider="pixal3d",
            source_image=source.relative_to(self.root).as_posix(),
        )

        with (
            patch(
                "tools.studio.company.image_to_blender._gdx1_status",
                return_value={"ssh": "not_tested"},
            ),
            patch(
                "tools.studio.company.image_to_blender._try_pixal3d_generate_or_prepare",
                return_value={
                    "provider": "pixal3d",
                    "status": "failed",
                    "reason": "test runtime unavailable",
                },
            ),
            patch(
                "tools.studio.company.image_to_blender._generate_local_blender_model"
            ) as local_fallback,
        ):
            with self.assertRaisesRegex(
                CompanyError,
                "unreviewed local fallback is prohibited",
            ):
                image3d_generate(self.root, "truth_pen", provider="pixal3d")

        local_fallback.assert_not_called()

    def test_gate_b_rejects_unbound_source_and_source_tamper(self) -> None:
        approved_source = self._complete_gate_b("truth_pen", provider="local")
        other_source = (
            self.root / "asset_pipeline/incoming_2d/truth_pen/other.png"
        )
        other_source.write_bytes(b"other source")
        image3d_new(
            self.root,
            "truth_pen",
            provider="local",
            source_image=other_source.relative_to(self.root).as_posix(),
        )

        with self.assertRaisesRegex(CompanyError, "exact file approved by Gate B"):
            image3d_generate(self.root, "truth_pen", provider="local")

        approved_source.write_bytes(b"tampered")
        result = evaluate_asset_gate_b(self.root, "truth_pen")
        self.assertFalse(result["passed"])
        self.assertIn(
            "source_sha256 does not match source_asset_path",
            result["errors"],
        )
        manifest = result["manifest"]
        data = self._read(manifest)
        data["source_asset_path"] = str(approved_source.resolve())
        self._write(manifest, data)
        result = evaluate_asset_gate_b(self.root, "truth_pen")
        self.assertIn(
            "source_asset_path must be a repository-relative path",
            result["errors"],
        )

    def test_scaffolds_are_blocked_and_do_not_overwrite_lifecycle(self) -> None:
        self._track("truth_pen", status="accepted")

        prepare_receipt = asset_prepare(self.root, "truth_pen")
        forge_receipt = asset_forge_new(self.root, "truth_pen")
        image_receipt = image3d_new(self.root, "truth_pen", provider="pixal3d")

        self.assertIn("blocked_by_gate_a", prepare_receipt.read_text(encoding="utf-8"))
        self.assertIn("waiting_for_gate_a", forge_receipt.read_text(encoding="utf-8"))
        self.assertIn("waiting_for_gate_a", image_receipt.read_text(encoding="utf-8"))
        forge = self._read(
            self.root / "asset_pipeline/forge/truth_pen/forge_job.json"
        )
        image = self._read(
            self.root
            / "asset_pipeline/image_to_blender/truth_pen/image3d_job.json"
        )
        self.assertEqual(forge["pipeline"][3]["status"], "blocked_by_gate_a")
        self.assertEqual(image["pipeline"][4]["status"], "blocked_by_gate_a")
        for relative in (
            "asset_pipeline/forge/truth_pen/concept/source_intake.md",
            "asset_pipeline/forge/truth_pen/cubepart/cubepart_job.md",
            "asset_pipeline/forge/truth_pen/blender/cleanup_plan.md",
            "asset_pipeline/forge/truth_pen/unity/unity_import_plan.md",
            "asset_pipeline/blender_work/truth_pen/cleanup_work_order.md",
            "asset_pipeline/blender_work/truth_pen/blender_batch_template.py",
            "asset_pipeline/unity_ready/truth_pen/import_note.md",
            "asset_pipeline/unity_ready/truth_pen/unity_import_manifest.md",
            "asset_pipeline/image_to_blender/truth_pen/providers/trellis2_job.md",
            "asset_pipeline/image_to_blender/truth_pen/providers/tripo_job.md",
            "asset_pipeline/image_to_blender/truth_pen/blender/cleanup_plan.md",
            "asset_pipeline/image_to_blender/truth_pen/unity/unity_import_plan.md",
        ):
            self.assertIn(
                "blocked_by_gate_a",
                (self.root / relative).read_text(encoding="utf-8"),
                relative,
            )
        blender_template = (
            self.root
            / "asset_pipeline/blender_work/truth_pen/blender_batch_template.py"
        ).read_text(encoding="utf-8")
        self.assertIn("require_asset_gate_b", blender_template)
        self.assertIn("require_production_gate()", blender_template)
        self.assertEqual(self._asset("truth_pen")["status"], "accepted")

    def test_asset_new_replaces_all_stale_blender_unity_scaffolds(self) -> None:
        self._track("fresh_prop", status="accepted")
        paths = (
            "asset_pipeline/blender_work/fresh_prop/cleanup_work_order.md",
            "asset_pipeline/blender_work/fresh_prop/blender_batch_template.py",
            "asset_pipeline/unity_ready/fresh_prop/import_note.md",
            "asset_pipeline/unity_ready/fresh_prop/unity_import_manifest.md",
        )
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Status: stale_ready\n", encoding="utf-8")

        asset_new(self.root, "fresh_prop")

        for relative in paths:
            text = (self.root / relative).read_text(encoding="utf-8")
            self.assertIn("blocked_by_gate_a", text, relative)
            self.assertNotIn("stale_ready", text, relative)
        template = (self.root / paths[1]).read_text(encoding="utf-8")
        self.assertIn("require_asset_gate_b", template)
        self.assertEqual(self._asset("fresh_prop")["status"], "accepted")

    def test_gate_statuses_are_evaluator_owned(self) -> None:
        self._track("truth_pen")
        with self.assertRaisesRegex(CompanyError, "Invalid asset status"):
            asset_status(self.root, "truth_pen", "source_gate_approved")

    def _complete_gate_a(
        self,
        asset_id: str,
        source_path: str,
        *,
        approve: bool = True,
    ) -> Path:
        self._track(asset_id)
        manifest = asset_gate_a_init(
            self.root,
            asset_id,
            source_path=source_path,
        )
        evidence = self.root / f"docs/{asset_id}_source_rights.md"
        provenance = self.root / f"docs/{asset_id}_provenance.md"
        disclosure = self.root / f"docs/{asset_id}_disclosure.md"
        snapshot = self.root / f"docs/{asset_id}_cc0_snapshot.md"
        for path in (evidence, provenance, disclosure, snapshot):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"Test evidence for {asset_id}.\n", encoding="utf-8")

        relative_evidence = evidence.relative_to(self.root).as_posix()
        data = self._read(manifest)
        data.update(
            {
                "task_id": "task-0011",
                "applicable_jurisdiction": "Republic of Korea",
                "provider_or_source": "Test Source",
                "creator_or_affirmer": "Test Creator",
                "rights_holder_or_legal_customer": "Channel Play Test Organization",
                "license_or_agreement": "Test commercial rights instrument",
                "source_reference": relative_evidence,
                "retrieval_date": date.today().isoformat(),
                "controlling_terms_reference": relative_evidence,
                "rights": {field: "PASS" for field in data["rights"]},
                "input_clearance": {
                    "project_owned_or_cleared_inputs": True,
                    "unverified_web_references": False,
                    "watermarks_or_logos": False,
                    "copied_franchise_style": False,
                    "tracing_or_image_conditioning": False,
                },
                "evidence_paths": [relative_evidence],
                "critic_review": {
                    "receipt": f"reviews/{asset_id}_gate_a.json",
                },
            }
        )
        if source_path == "commissioned_human":
            data["path_details"] = {
                "contracting_parties": "Test Organization and Test Artist",
                "signed_rights_instrument": relative_evidence,
                "downstream_asset_creation_grant": True,
            }
        elif source_path == "openai":
            data["controlling_terms_reference"] = (
                "https://openai.com/policies/services-agreement/"
            )
            data["path_details"] = {
                "product_account_type": "api_business",
                "workspace_owner": "Channel Play Test Organization",
                "intended_model": "gpt-image-test",
                "beta_service": False,
                "beta_risk_acceptance": "",
                "producing_contributor": "Test Contributor",
                "contributor_transfer_evidence": relative_evidence,
                "input_rights_evidence": relative_evidence,
                "non_uniqueness_acknowledged": True,
                "human_review_required": True,
                "output_allocation_not_warranty": True,
                "indemnity_limits_reviewed": True,
                "ai_provenance_record": provenance.relative_to(self.root).as_posix(),
                "disclosure_decision_record": disclosure.relative_to(self.root).as_posix(),
                "public_service_sharing": False,
                "third_party_app_or_gpt": False,
                "likeness_or_real_person": False,
            }
        else:
            data["source_reference"] = (
                "https://example.org/assets/truth-pen-source"
            )
            data["controlling_terms_reference"] = (
                "https://creativecommons.org/publicdomain/zero/1.0/legalcode.en"
            )
            data["path_details"] = {
                "exact_work_url": "https://example.org/assets/truth-pen-source",
                "original_host": "example.org",
                "cc0_marking_url": (
                    "https://creativecommons.org/publicdomain/zero/1.0/"
                ),
                "retrieval_snapshot": snapshot.relative_to(self.root).as_posix(),
                "affirmer_authority_evidence": relative_evidence,
            }
        self._write(manifest, data)
        if approve:
            self._write_critic_approval(
                manifest,
                asset_id,
                task_id="task-0011",
                gate="A",
                receipt=data["critic_review"]["receipt"],
            )
        return manifest

    def _complete_gate_b(self, asset_id: str, *, provider: str) -> Path:
        self._complete_gate_a(asset_id, "openai")
        asset_gate_a_check(self.root, asset_id)
        manifest = asset_gate_b_init(self.root, asset_id)
        source = self.root / f"asset_pipeline/incoming_2d/{asset_id}/concept.png"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"approved source")
        records = {}
        for name in ("prompt", "edits", "clearance", "disclosure"):
            path = self.root / f"docs/{asset_id}_{name}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{name} record\n", encoding="utf-8")
            records[name] = path.relative_to(self.root).as_posix()
        data = self._read(manifest)
        data.update(
            {
                "task_id": "task-0012",
                "source_asset_path": source.relative_to(self.root).as_posix(),
                "source_sha256": sha256_file(source),
                "source_created_or_acquired_at": "2025-01-01T00:00:00+00:00",
                "source_provider_or_tool": "OpenAI API",
                "source_model_or_version": "gpt-image-test",
                "source_job_or_seed": "test-job-1",
                "prompt_record": records["prompt"],
                "edit_history_record": records["edits"],
                "clearance_record": records["clearance"],
                "attribution_disclosure_record": records["disclosure"],
                "rights": {field: "PASS" for field in data["rights"]},
                "production": {
                    "approved_3d_provider": provider,
                    "allow_unreviewed_fallback": False,
                },
                "critic_review": {
                    "receipt": f"reviews/{asset_id}_gate_b.json",
                },
            }
        )
        self._write(manifest, data)
        self._write_critic_approval(
            manifest,
            asset_id,
            task_id="task-0012",
            gate="B",
            receipt=data["critic_review"]["receipt"],
        )
        asset_gate_b_check(self.root, asset_id)
        return source

    def _write_critic_approval(
        self,
        manifest: Path,
        asset_id: str,
        *,
        task_id: str,
        gate: str,
        receipt: str,
    ) -> None:
        path = self.root / receipt
        self._write(
            path,
            {
                "schema": CRITIC_APPROVAL_SCHEMA,
                "asset_id": asset_id,
                "task_id": task_id,
                "gate": gate,
                "manifest_sha256": sha256_gate_manifest(manifest),
                "reviewer_role": "critic_reviewer",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "verdict": "APPROVED",
                "source_creation_authorized": gate == "A",
                "production_authorized": gate == "B",
            },
        )

    def _track(self, asset_id: str, *, status: str = "briefed") -> None:
        index = self.root / "asset_pipeline/index.json"
        data = self._read(index) if index.exists() else {"assets": []}
        if not any(asset.get("id") == asset_id for asset in data["assets"]):
            data["assets"].append({"id": asset_id, "status": status})
        self._write(index, data)

    def _asset(self, asset_id: str) -> dict:
        data = self._read(self.root / "asset_pipeline/index.json")
        return next(asset for asset in data["assets"] if asset["id"] == asset_id)

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


if __name__ == "__main__":
    unittest.main()
