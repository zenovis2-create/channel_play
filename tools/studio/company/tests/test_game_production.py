from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.capture import PNG_SIGNATURE
from tools.studio.company.errors import CompanyError
from tools.studio.company.game_production import (
    PROCUREMENT_FIELD_GUIDANCE,
    _procurement_decision_progress,
    _procurement_issue_groups,
    _procurement_owner_worksheet,
    game_production_state,
    render_game_production_status,
)
from tools.studio.company.procurement import (
    OWNER_DECISION_FIELDS,
    procurement_decision_init,
    procurement_outreach_check,
)


class GameProductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets" / "_Project" / "Scenes").mkdir(parents=True)
        (self.root / "Assets" / "_Project" / "Scripts" / "Gameplay").mkdir(parents=True)
        (self.root / "Assets" / "_Project" / "Scripts" / "Player").mkdir(parents=True)
        (self.root / "Assets" / "_Project" / "Prefabs").mkdir(parents=True)
        (self.root / "Assets" / "_Project" / "Scenes" / "School_MVP.unity").write_text("%YAML\n", encoding="utf-8")
        (self.root / "Assets" / "_Project" / "Scripts" / "Gameplay" / "TraitorEscapeMvpSpec.md").write_text("# spec\n", encoding="utf-8")
        (self.root / "Assets" / "_Project" / "Scripts" / "Gameplay" / "TraitorEscapeMvpSession.cs").write_text("// runtime\n", encoding="utf-8")
        (self.root / "Assets" / "_Project" / "Scripts" / "Player" / "ChannelPlayerController.cs").write_text("// player\n", encoding="utf-8")
        (self.root / "Assets" / "_Project" / "Prefabs" / "MVP_Player.prefab").write_text("%YAML\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_state_reports_pending_without_evidence(self) -> None:
        state = game_production_state(self.root)

        self.assertEqual(state["readiness"]["status"], "needs_work")
        self.assertEqual(state["readiness"]["passed"], 1)
        self.assertEqual(len(state["optimizationLoops"]), 5)
        self.assertEqual(state["optimizationLoops"][0]["status"], "needs_capture")
        self.assertEqual(state["nextBestAction"]["command"], "game.productionCheck")
        self.assertEqual(state["perfectionGate"]["status"], "needs_work")
        self.assertEqual(state["unity"]["scenes"], 1)
        self.assertEqual(state["unity"]["gameplayScripts"], 1)
        self.assertEqual(state["unity"]["playerScripts"], 1)
        self.assertEqual(state["unity"]["prefabs"], 1)

    def test_state_marks_ready_when_all_receipts_exist(self) -> None:
        self._write_run("unity-check-001", "unity_check.md", "Exit code: 0\nCompile errors: 0\n")
        self._write_run("unity-playtest-001", "unity_playtest.md", "Exit code: 0\nCompile errors: 0\nPlaytest smoke: passed\n")
        self._write_run("unity-build-mac-dev-001", "unity_build.md", "Exit code: 0\nBuild status: passed\nBuild output exists: True\n")
        self._write_run("gdx-probe-001", "gdx_probe.md", "Status: ok\nusable\n")
        capture_dir = self.root / "reviews" / "captures"
        capture_dir.mkdir(parents=True)
        (capture_dir / "screen.png").write_bytes(PNG_SIGNATURE + b"test")

        state = game_production_state(self.root)

        self.assertEqual(state["readiness"], {"passed": 6, "total": 6, "status": "ready"})
        self.assertEqual(state["unity"]["compile"]["path"], "runs/unity-check-001/unity_check.md")
        self.assertEqual(state["gdx"]["path"], "runs/gdx-probe-001/gdx_probe.md")

    def test_state_accepts_windows_development_build_receipt(self) -> None:
        self._write_run("unity-check-001", "unity_check.md", "Exit code: 0\nCompile errors: 0\n")
        self._write_run("unity-playtest-001", "unity_playtest.md", "Exit code: 0\nPlaytest smoke: passed\n")
        self._write_run(
            "unity-build-windows-dev-001",
            "unity_build.md",
            "Exit code: 0\nBuild status: passed\nBuild output exists: True\n",
        )
        self._write_run("gdx-probe-001", "gdx_probe.md", "Status: ok\n")
        capture_dir = self.root / "reviews" / "captures"
        capture_dir.mkdir(parents=True)
        (capture_dir / "screen.png").write_bytes(PNG_SIGNATURE + b"test")

        state = game_production_state(self.root)

        self.assertEqual(state["readiness"], {"passed": 6, "total": 6, "status": "ready"})
        self.assertIn("unity-build-windows-dev-001", state["unity"]["build"]["path"])

    def test_blocked_gdx_probe_is_recorded_without_blocking_local_readiness(self) -> None:
        self._write_ready_receipts()
        probe = self.root / "runs" / "gdx-probe-001" / "gdx_probe.md"
        probe.write_text(
            "# gdx1 Probe\n\n"
            "SSH exit: 255\n"
            "SSH stderr: Host key verification failed.\n\n"
            "## Result\n\n"
            "blocked: SSH authentication or host access failed\n",
            encoding="utf-8",
        )

        state = game_production_state(self.root)

        self.assertEqual(state["readiness"], {"passed": 6, "total": 6, "status": "ready"})
        probe_check = next(
            check
            for check in state["checks"]
            if check["label"] == "gdx1 probe evidence"
        )
        self.assertTrue(probe_check["passed"])
        self.assertEqual(state["remote"]["status"], "server_blocked")

    def test_state_rejects_text_file_with_png_extension(self) -> None:
        capture_dir = self.root / "reviews" / "captures"
        capture_dir.mkdir(parents=True)
        (capture_dir / "screen.png").write_text("capture failed\n", encoding="utf-8")

        state = game_production_state(self.root)

        capture_check = next(
            check
            for check in state["checks"]
            if check["label"] == "Capture evidence"
        )
        self.assertFalse(capture_check["passed"])

    def test_quick_unity_check_does_not_replace_valid_compile_evidence(self) -> None:
        self._write_ready_receipts()
        self._write_run("unity-check-999", "unity_check.md", "Result: quick project check passed. Use `--batch` for Unity batchmode.\n")

        state = game_production_state(self.root)

        self.assertEqual(state["readiness"], {"passed": 6, "total": 6, "status": "ready"})
        self.assertEqual(state["unity"]["compile"]["path"], "runs/unity-check-001/unity_check.md")

    def test_state_reports_feedback_asset_and_server_handoff_loops(self) -> None:
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: open\n", encoding="utf-8")
        asset_index = self.root / "asset_pipeline" / "index.json"
        asset_index.parent.mkdir(parents=True)
        asset_index.write_text(
            '{"assets":[{"id":"prop","status":"generated","pipeline_receipt":"runs/asset-pipeline-prop/asset_pipeline_receipt.md"}]}',
            encoding="utf-8",
        )

        state = game_production_state(self.root)
        loops = {loop["id"]: loop for loop in state["optimizationLoops"]}

        self.assertEqual(loops["play_feedback"]["status"], "ready")
        self.assertEqual(loops["asset_factory"]["status"], "ready")
        self.assertEqual(loops["server_soak"]["status"], "handoff_ready")
        self.assertIn("game-server-handoff-001", loops["server_soak"]["evidence"])
        self.assertEqual(state["nextBestAction"]["command"], "game.productionCheck")

    def test_next_action_routes_open_feedback_before_external_server_blocker(self) -> None:
        self._write_ready_receipts()
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: open\n", encoding="utf-8")
        self._write_asset_index()

        state = game_production_state(self.root)

        self.assertEqual(state["nextBestAction"]["command"], "feedback.process")
        self.assertEqual(state["nextBestAction"]["payload"], {"path": "reviews/2026-06-03/feedback-0001/feedback.md"})

    def test_next_action_runs_assigned_task_after_feedback_is_routed(self) -> None:
        self._write_ready_receipts()
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_asset_index()
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True)
        board.write_text(
            '{"tasks":[{"id":"task-0007","status":"assigned","updated_at":"2026-06-03T00:00:00+09:00","work_order":"memory/sessions/test/work_orders/task-0007.md"}]}',
            encoding="utf-8",
        )

        state = game_production_state(self.root)

        self.assertEqual(state["nextBestAction"]["command"], "agent.run")
        self.assertEqual(state["nextBestAction"]["payload"], {"taskId": "task-0007"})
        self.assertEqual(state["taskFlow"]["assigned"], 1)

    def test_next_action_assigns_latest_planned_task(self) -> None:
        self._write_ready_receipts()
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_asset_index()
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True)
        board.write_text(
            '{"tasks":[{"id":"task-0009","status":"planned",'
            '"suggested_agent":"research_librarian",'
            '"updated_at":"2026-07-26T18:07:35+09:00"}]}',
            encoding="utf-8",
        )
        state_path = self.root / "memory" / "company" / "state.json"
        state_path.write_text(
            '{"active_session":"20260726-truth-pen"}',
            encoding="utf-8",
        )

        state = game_production_state(self.root)

        self.assertEqual(state["nextBestAction"]["command"], "company.assign")
        self.assertEqual(
            state["nextBestAction"]["payload"],
            {
                "taskId": "task-0009",
                "agentId": "research_librarian",
            },
        )
        work_queue = next(
            loop
            for loop in state["optimizationLoops"]
            if loop["id"] == "game_work_queue"
        )
        self.assertEqual(work_queue["status"], "ready")

    def test_next_action_starts_session_before_assigning_planned_task(self) -> None:
        self._write_ready_receipts()
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_asset_index()
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True)
        board.write_text(
            '{"tasks":[{"id":"task-0009","status":"planned",'
            '"request":"Truth Pen source research",'
            '"suggested_agent":"research_librarian",'
            '"updated_at":"2026-07-26T18:07:35+09:00"}]}',
            encoding="utf-8",
        )

        state = game_production_state(self.root)

        self.assertEqual(
            state["nextBestAction"]["command"],
            "company.session.start",
        )
        self.assertEqual(
            state["nextBestAction"]["payload"],
            {"goal": "Truth Pen source research"},
        )

    def test_blocked_procurement_is_visible_and_routes_read_only_check(self) -> None:
        self._write_ready_receipts()
        self._write_run(
            "game-feedback-loop-001",
            "game_feedback_loop.md",
            "Status: ready_for_review\n",
        )
        self._write_run(
            "game-server-handoff-001",
            "server_handoff.md",
            "Status: waiting_for_x86_64_runner\n",
        )
        feedback = (
            self.root
            / "reviews"
            / "2026-06-03"
            / "feedback-0001"
            / "feedback.md"
        )
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_truth_pen_procurement_decision()

        state = game_production_state(self.root)
        procurement = state["procurement"]
        loops = {loop["id"]: loop for loop in state["optimizationLoops"]}
        text = render_game_production_status(self.root)

        self.assertEqual(procurement["assetId"], "truth_pen")
        self.assertEqual(procurement["status"], "blocked")
        self.assertEqual(procurement["errorCount"], 16)
        self.assertEqual(len(procurement["errors"]), 16)
        self.assertFalse(
            any("UNKNOWN" in error for error in procurement["errors"])
        )
        issue_groups = procurement["issueGroups"]
        self.assertEqual(
            [group["id"] for group in issue_groups],
            [
                "approval",
                "owner",
                "commercial",
                "schedule",
                "outreach",
                "privacy",
            ],
        )
        self.assertEqual(
            [group["count"] for group in issue_groups],
            [1, 3, 4, 3, 4, 1],
        )
        issues = [
            issue
            for group in issue_groups
            for issue in group["items"]
        ]
        self.assertEqual(len(issues), 16)
        self.assertEqual(
            {issue["message"] for issue in issues},
            set(procurement["errors"]),
        )
        self.assertTrue(
            all(
                issue["field"]
                and issue["label"]
                and issue["guidance"]
                for issue in issues
            )
        )
        self.assertNotIn(
            "UNKNOWN",
            json.dumps(issue_groups, ensure_ascii=False),
        )
        progress = procurement["decisionProgress"]
        self.assertEqual(progress["total"], 16)
        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["unresolved"], 16)
        self.assertEqual(progress["additionalIssueCount"], 0)
        self.assertFalse(progress["indeterminate"])
        self.assertEqual(progress["status"], "pending")
        self.assertEqual(
            [group["total"] for group in progress["groups"]],
            [1, 3, 4, 3, 4, 1],
        )
        self.assertTrue(
            all(
                group["completed"] == 0
                and group["status"] == "pending"
                for group in progress["groups"]
            )
        )
        worksheet = procurement["decisionWorksheet"]
        self.assertTrue(worksheet["available"])
        self.assertEqual(worksheet["itemCount"], 16)
        self.assertEqual(worksheet["reason"], "unresolved")
        self.assertEqual(
            worksheet["text"].count(
                "<owner-approved repository-safe value>"
            ),
            16,
        )
        for issue in issues:
            self.assertEqual(
                worksheet["text"].count(f"`{issue['field']}`"),
                1,
            )
            self.assertNotIn(issue["message"], worksheet["text"])
        for stored_value in ("UNKNOWN", "unselected"):
            self.assertNotIn(stored_value, worksheet["text"])
        self.assertIn(
            "not artist-contact authorization",
            worksheet["text"],
        )
        self.assertIn(
            "Do not include personal names",
            worksheet["text"],
        )
        self.assertEqual(
            procurement["intake"],
            "docs/research/truth_pen_owner_decision_intake.md",
        )
        self.assertEqual(loops["artist_procurement"]["status"], "blocked")
        procurement_gate = next(
            check
            for check in state["perfectionGate"]["checks"]
            if check["label"] == "Artist procurement"
        )
        self.assertFalse(procurement_gate["passed"])
        self.assertEqual(state["perfectionGate"]["total"], 7)
        self.assertEqual(
            loops["artist_procurement"]["evidence"],
            "asset_pipeline/manifests/truth_pen_procurement_decision.json",
        )
        self.assertEqual(
            state["nextBestAction"],
            {
                "label": "Resolve artist procurement owner decisions",
                "command": "asset.procurementCheck",
                "payload": {"assetId": "truth_pen"},
                "reason": (
                    "truth_pen has 16 unresolved owner decisions. "
                    "The check is read-only; artist contact remains blocked."
                ),
                "status": "blocked",
            },
        )
        self.assertIn(
            "Artist procurement: blocked (16 unresolved owner decisions)",
            text,
        )
        self.assertFalse(
            (
                self.root
                / "runs"
                / "asset-procurement-truth_pen"
                / "outreach_readiness_check.md"
            ).exists()
        )

    def test_unknown_procurement_error_uses_safe_fallback_guidance(self) -> None:
        groups = _procurement_issue_groups(
            ["procurement decision is not valid UTF-8 JSON"]
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["id"], "validation")
        self.assertEqual(groups[0]["count"], 1)
        self.assertEqual(
            groups[0]["items"][0]["label"],
            "조달 기록 추가 검증",
        )
        self.assertIn(
            "소유자 안내서",
            groups[0]["items"][0]["guidance"],
        )
        progress = _procurement_decision_progress(groups)
        self.assertTrue(progress["indeterminate"])
        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["unresolved"], 16)
        self.assertEqual(progress["additionalIssueCount"], 1)
        self.assertTrue(
            all(
                group["status"] == "indeterminate"
                for group in progress["groups"]
            )
        )
        self.assertEqual(
            _procurement_owner_worksheet("truth_pen", groups, progress),
            {
                "available": False,
                "itemCount": 0,
                "reason": "indeterminate",
                "text": "",
            },
        )
        self.assertEqual(
            _procurement_owner_worksheet(
                "truth_pen",
                groups,
                {"indeterminate": False},
            )["reason"],
            "indeterminate",
        )

    def test_owner_answer_contract_matches_progress_guidance(self) -> None:
        self.assertEqual(
            tuple(PROCUREMENT_FIELD_GUIDANCE),
            OWNER_DECISION_FIELDS,
        )

    def test_procurement_progress_deduplicates_known_field_errors(self) -> None:
        groups = _procurement_issue_groups(
            [
                "schedule.proposal_deadline must use YYYY-MM-DD",
                "schedule.proposal_deadline must not be in the past",
            ]
        )

        progress = _procurement_decision_progress(groups)
        schedule = next(
            group
            for group in progress["groups"]
            if group["id"] == "schedule"
        )

        self.assertFalse(progress["indeterminate"])
        self.assertEqual(progress["completed"], 15)
        self.assertEqual(progress["unresolved"], 1)
        self.assertEqual(progress["additionalIssueCount"], 0)
        self.assertEqual(schedule["completed"], 2)
        self.assertEqual(schedule["unresolved"], 1)

    def test_partial_procurement_decision_reports_field_progress(self) -> None:
        self._write_truth_pen_procurement_decision()
        manifest = (
            self.root
            / "asset_pipeline"
            / "manifests"
            / "truth_pen_procurement_decision.json"
        )
        decision = json.loads(manifest.read_text(encoding="utf-8"))
        decision["owner"]["governing_jurisdiction"] = "KR"
        manifest.write_text(
            json.dumps(decision, indent=2) + "\n",
            encoding="utf-8",
        )

        progress = game_production_state(self.root)["procurement"][
            "decisionProgress"
        ]
        owner = next(
            group
            for group in progress["groups"]
            if group["id"] == "owner"
        )

        self.assertEqual(progress["completed"], 1)
        self.assertEqual(progress["unresolved"], 15)
        self.assertEqual(progress["status"], "in_progress")
        self.assertEqual(owner["completed"], 1)
        self.assertEqual(owner["unresolved"], 2)
        self.assertEqual(owner["status"], "in_progress")
        worksheet = game_production_state(self.root)["procurement"][
            "decisionWorksheet"
        ]
        self.assertTrue(worksheet["available"])
        self.assertEqual(worksheet["itemCount"], 15)
        self.assertNotIn(
            "`owner.governing_jurisdiction`",
            worksheet["text"],
        )
        self.assertIn("`owner.secure_record_id`", worksheet["text"])

    def test_current_fail_receipt_routes_to_owner_intake(self) -> None:
        self._write_ready_receipts()
        self._write_run(
            "game-feedback-loop-001",
            "game_feedback_loop.md",
            "Status: ready_for_review\n",
        )
        self._write_run(
            "game-server-handoff-001",
            "server_handoff.md",
            "Status: waiting_for_x86_64_runner\n",
        )
        feedback = (
            self.root
            / "reviews"
            / "2026-06-03"
            / "feedback-0001"
            / "feedback.md"
        )
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_truth_pen_procurement_decision()
        with self.assertRaises(CompanyError):
            procurement_outreach_check(self.root, "truth_pen")

        state = game_production_state(self.root)
        text = render_game_production_status(self.root)
        actionability = next(
            check
            for check in state["perfectionGate"]["checks"]
            if check["label"] == "Work queue actionable"
        )

        self.assertEqual(
            state["nextBestAction"],
            {
                "label": "Complete artist procurement owner decisions",
                "artifact": (
                    "docs/research/truth_pen_owner_decision_intake.md"
                ),
                "actionLabel": "Open owner decision intake",
                "reason": (
                    "The current FAIL receipt already covers truth_pen and "
                    "lists 16 unresolved owner decisions. Complete only "
                    "owner-approved fields, then rerun the check; artist "
                    "contact remains blocked."
                ),
                "status": "blocked",
            },
        )
        self.assertTrue(actionability["passed"])
        self.assertEqual(
            actionability["detail"],
            "docs/research/truth_pen_owner_decision_intake.md",
        )
        self.assertIn(
            "Complete artist procurement owner decisions -> "
            "docs/research/truth_pen_owner_decision_intake.md",
            text,
        )

    def test_procurement_ignores_receipt_for_a_different_manifest(self) -> None:
        self._write_truth_pen_procurement_decision()
        receipt = (
            self.root
            / "runs"
            / "asset-procurement-truth_pen"
            / "outreach_readiness_check.md"
        )
        receipt.parent.mkdir(parents=True)
        receipt.write_text(
            "Decision SHA-256: stale\nResult: **FAIL**\n",
            encoding="utf-8",
        )

        state = game_production_state(self.root)
        procurement = state["procurement"]
        loop = next(
            item
            for item in state["optimizationLoops"]
            if item["id"] == "artist_procurement"
        )

        self.assertEqual(procurement["receipt"], "")
        self.assertEqual(
            loop["evidence"],
            "asset_pipeline/manifests/truth_pen_procurement_decision.json",
        )
        with self.assertRaises(CompanyError):
            procurement_outreach_check(self.root, "truth_pen")

        refreshed = game_production_state(self.root)

        self.assertEqual(
            refreshed["procurement"]["receipt"],
            "runs/asset-procurement-truth_pen/outreach_readiness_check.md",
        )

    def test_missing_owner_intake_with_current_fail_receipt_stays_blocked(
        self,
    ) -> None:
        self._write_ready_procurement_workflow()
        self._write_truth_pen_procurement_decision()
        with self.assertRaises(CompanyError):
            procurement_outreach_check(self.root, "truth_pen")
        (
            self.root
            / "docs"
            / "research"
            / "truth_pen_owner_decision_intake.md"
        ).unlink()

        state = game_production_state(self.root)
        actionability = next(
            check
            for check in state["perfectionGate"]["checks"]
            if check["label"] == "Work queue actionable"
        )

        self.assertEqual(
            state["nextBestAction"],
            {
                "label": "Restore owner decision intake guidance",
                "reason": (
                    "The current procurement result is FAIL, but the required "
                    "guide is missing: "
                    "docs/research/truth_pen_owner_decision_intake.md. "
                    "Procurement cannot advance and artist contact remains "
                    "blocked."
                ),
                "status": "blocked",
            },
        )
        self.assertFalse(actionability["passed"])
        self.assertNotIn("command", state["nextBestAction"])
        self.assertNotIn("artifact", state["nextBestAction"])

    def test_ready_decision_requires_current_pass_receipt(self) -> None:
        self._write_ready_procurement_workflow()
        self._write_truth_pen_procurement_decision()
        self._approve_truth_pen_procurement_decision()

        state = game_production_state(self.root)

        self.assertTrue(state["procurement"]["passed"])
        self.assertEqual(state["procurement"]["receipt"], "")
        self.assertEqual(
            state["procurement"]["decisionProgress"],
            {
                "total": 16,
                "completed": 16,
                "unresolved": 0,
                "additionalIssueCount": 0,
                "indeterminate": False,
                "status": "complete",
                "groups": [
                    {
                        "id": "approval",
                        "label": "승인 상태",
                        "total": 1,
                        "completed": 1,
                        "unresolved": 0,
                        "status": "complete",
                    },
                    {
                        "id": "owner",
                        "label": "소유자 및 권한",
                        "total": 3,
                        "completed": 3,
                        "unresolved": 0,
                        "status": "complete",
                    },
                    {
                        "id": "commercial",
                        "label": "예산 및 결제",
                        "total": 4,
                        "completed": 4,
                        "unresolved": 0,
                        "status": "complete",
                    },
                    {
                        "id": "schedule",
                        "label": "일정",
                        "total": 3,
                        "completed": 3,
                        "unresolved": 0,
                        "status": "complete",
                    },
                    {
                        "id": "outreach",
                        "label": "연락 범위 및 승인",
                        "total": 4,
                        "completed": 4,
                        "unresolved": 0,
                        "status": "complete",
                    },
                    {
                        "id": "privacy",
                        "label": "보안 및 개인정보",
                        "total": 1,
                        "completed": 1,
                        "unresolved": 0,
                        "status": "complete",
                    },
                ],
            },
        )
        self.assertEqual(
            state["procurement"]["decisionWorksheet"],
            {
                "available": False,
                "itemCount": 0,
                "reason": "complete",
                "text": "",
            },
        )
        self.assertEqual(
            state["nextBestAction"],
            {
                "label": "Record proposal outreach readiness",
                "command": "asset.procurementCheck",
                "payload": {"assetId": "truth_pen"},
                "reason": (
                    "The owner decision evaluates ready, but no current PASS "
                    "receipt exists. Run the read-only check before outreach."
                ),
                "status": "ready",
            },
        )

        procurement_outreach_check(self.root, "truth_pen")
        refreshed = game_production_state(self.root)

        self.assertTrue(refreshed["procurement"]["receipt"])
        self.assertNotEqual(
            refreshed["nextBestAction"].get("command"),
            "asset.procurementCheck",
        )

    def test_verified_task_receipt_keeps_progress_visibility_healthy(
        self,
    ) -> None:
        self._write_ready_procurement_workflow()
        self._write_asset_index()
        self._write_verified_task("task-0008")

        state = game_production_state(self.root)
        visibility = next(
            loop
            for loop in state["optimizationLoops"]
            if loop["id"] == "agent_visibility"
        )
        progress_gate = next(
            check
            for check in state["perfectionGate"]["checks"]
            if check["label"] == "Progress evidence healthy"
        )

        self.assertEqual(visibility["status"], "ready")
        self.assertIn("verified task-0008", visibility["summary"])
        self.assertEqual(
            visibility["evidence"],
            (
                "memory/sessions/test/verification/"
                "task-0008-verification.md"
            ),
        )
        self.assertEqual(
            state["taskFlow"]["latestVerified"]["id"],
            "task-0008",
        )
        self.assertTrue(progress_gate["passed"])
        self.assertEqual(state["perfectionGate"]["status"], "perfect")

    def test_invalid_verified_task_receipt_does_not_fake_visibility(
        self,
    ) -> None:
        for (
            write_evidence,
            receipt_status,
            receipt_task_id,
            verification_relative,
        ) in (
            (False, "passed", "task-0008", None),
            (True, "pending", "task-0008", None),
            (True, "passed", "task-9999", None),
            (
                True,
                "passed",
                "task-0008",
                "docs/fake-verification.md",
            ),
        ):
            with self.subTest(
                write_evidence=write_evidence,
                receipt_status=receipt_status,
                receipt_task_id=receipt_task_id,
                verification_relative=verification_relative,
            ):
                self._write_verified_task(
                    "task-0008",
                    write_evidence=write_evidence,
                    receipt_status=receipt_status,
                    receipt_task_id=receipt_task_id,
                    verification_relative=verification_relative,
                )

                state = game_production_state(self.root)
                visibility = next(
                    loop
                    for loop in state["optimizationLoops"]
                    if loop["id"] == "agent_visibility"
                )
                progress_gate = next(
                    check
                    for check in state["perfectionGate"]["checks"]
                    if check["label"] == "Progress evidence healthy"
                )

                self.assertEqual(
                    state["taskFlow"]["latestVerified"],
                    {},
                )
                self.assertEqual(visibility["status"], "pending")
                self.assertFalse(progress_gate["passed"])

    def test_active_job_does_not_borrow_verified_task_receipt(self) -> None:
        self._write_verified_task("task-0008")
        self._write_active_job_without_receipt()

        state = game_production_state(self.root)
        visibility = next(
            loop
            for loop in state["optimizationLoops"]
            if loop["id"] == "agent_visibility"
        )
        progress_gate = next(
            check
            for check in state["perfectionGate"]["checks"]
            if check["label"] == "Progress evidence healthy"
        )

        self.assertEqual(visibility["status"], "running")
        self.assertIn("agent.run", visibility["summary"])
        self.assertEqual(visibility["evidence"], "")
        self.assertTrue(progress_gate["passed"])
        self.assertNotIn(
            "task-0008-verification.md",
            progress_gate["detail"],
        )

    def test_perfection_gate_passes_when_workstation_workflow_is_actionable(self) -> None:
        self._write_ready_receipts()
        self._write_run("game-feedback-loop-001", "game_feedback_loop.md", "Status: ready_for_review\n")
        self._write_run("game-server-handoff-001", "server_handoff.md", "Status: waiting_for_x86_64_runner\n")
        feedback = self.root / "reviews" / "2026-06-03" / "feedback-0001" / "feedback.md"
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")
        self._write_asset_index()
        self._write_assigned_task("task-0007")
        self._write_job_receipt()

        state = game_production_state(self.root)

        self.assertEqual(state["perfectionGate"]["status"], "perfect")
        self.assertEqual(state["perfectionGate"]["answer"], "완벽합니다")
        self.assertEqual(state["perfectionGate"]["passed"], state["perfectionGate"]["total"])

    def test_status_render_includes_readiness_and_artifact_paths(self) -> None:
        self._write_run("unity-check-001", "unity_check.md", "Exit code: 0\nCompile errors: 0\n")

        text = render_game_production_status(self.root)

        self.assertIn("Game Production Cockpit", text)
        self.assertIn("Readiness:", text)
        self.assertIn("runs/unity-check-001/unity_check.md", text)

    def _write_run(self, dirname: str, filename: str, text: str) -> None:
        run = self.root / "runs" / dirname
        run.mkdir(parents=True)
        (run / filename).write_text(text, encoding="utf-8")

    def _write_ready_receipts(self) -> None:
        self._write_run("unity-check-001", "unity_check.md", "Exit code: 0\nCompile errors: 0\n")
        self._write_run("unity-playtest-001", "unity_playtest.md", "Exit code: 0\nCompile errors: 0\nPlaytest smoke: passed\n")
        self._write_run("unity-build-mac-dev-001", "unity_build.md", "Exit code: 0\nBuild status: passed\nBuild output exists: True\n")
        self._write_run("gdx-probe-001", "gdx_probe.md", "Status: ok\nusable\n")
        capture_dir = self.root / "reviews" / "captures"
        capture_dir.mkdir(parents=True)
        (capture_dir / "screen.png").write_bytes(PNG_SIGNATURE + b"test")

    def _write_asset_index(self) -> None:
        asset_index = self.root / "asset_pipeline" / "index.json"
        asset_index.parent.mkdir(parents=True)
        asset_index.write_text(
            '{"assets":[{"id":"prop","status":"generated","pipeline_receipt":"runs/asset-pipeline-prop/asset_pipeline_receipt.md"}]}',
            encoding="utf-8",
        )

    def _write_ready_procurement_workflow(self) -> None:
        self._write_ready_receipts()
        self._write_run(
            "game-feedback-loop-001",
            "game_feedback_loop.md",
            "Status: ready_for_review\n",
        )
        self._write_run(
            "game-server-handoff-001",
            "server_handoff.md",
            "Status: waiting_for_x86_64_runner\n",
        )
        feedback = (
            self.root
            / "reviews"
            / "2026-06-03"
            / "feedback-0001"
            / "feedback.md"
        )
        feedback.parent.mkdir(parents=True)
        feedback.write_text("Status: routed\n", encoding="utf-8")

    def _write_truth_pen_procurement_decision(self) -> None:
        asset_index = self.root / "asset_pipeline" / "index.json"
        asset_index.parent.mkdir(parents=True, exist_ok=True)
        asset_index.write_text(
            '{"assets":[{"id":"truth_pen","status":"briefed",'
            '"pipeline_receipt":'
            '"runs/asset-pipeline-truth_pen/asset_pipeline_receipt.md"}]}',
            encoding="utf-8",
        )
        rfp = (
            self.root
            / "asset_pipeline"
            / "briefs"
            / "truth_pen_commission_rfp.md"
        )
        rfp.parent.mkdir(parents=True, exist_ok=True)
        rfp.write_text("# RFP\n", encoding="utf-8")
        packet = (
            self.root
            / "docs"
            / "research"
            / "truth_pen_artist_procurement_packet.md"
        )
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text("# Procurement packet\n", encoding="utf-8")
        intake = (
            self.root
            / "docs"
            / "research"
            / "truth_pen_owner_decision_intake.md"
        )
        intake.write_text("# Owner decision intake\n", encoding="utf-8")
        procurement_decision_init(self.root, "truth_pen")

    def _approve_truth_pen_procurement_decision(self) -> None:
        manifest = (
            self.root
            / "asset_pipeline"
            / "manifests"
            / "truth_pen_procurement_decision.json"
        )
        decision = json.loads(manifest.read_text(encoding="utf-8"))
        decision["decision_status"] = "approved_for_proposal_outreach"
        decision["owner"] = {
            "secure_record_id": (
                "vault:12345678-1234-4234-8234-123456789abc"
            ),
            "authorized_signer_role": "project_owner",
            "governing_jurisdiction": "KR",
        }
        decision["commercial"] = {
            "budget_ceiling": 1000,
            "currency": "USD",
            "payment_route": "upwork",
            "tax_vendor_process_confirmed_securely": True,
        }
        decision["schedule"] = {
            "proposal_deadline": "2099-01-01",
            "desired_delivery_date": "2099-02-01",
            "revision_limit": 2,
        }
        decision["outreach"].update(
            {
                "authorized": True,
                "authorized_at": "2026-01-01T00:00:00+09:00",
                "scope": "one",
                "candidate_ids": ["cynthia_ignacio"],
            }
        )
        decision["privacy"]["sensitive_data_stored_outside_repo"] = True
        manifest.write_text(
            json.dumps(decision, indent=2) + "\n",
            encoding="utf-8",
        )

    def _write_assigned_task(self, task_id: str) -> None:
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True)
        board.write_text(
            f'{{"tasks":[{{"id":"{task_id}","status":"assigned","updated_at":"2026-06-03T00:00:00+09:00","work_order":"memory/sessions/test/work_orders/{task_id}.md"}}]}}',
            encoding="utf-8",
        )

    def _write_verified_task(
        self,
        task_id: str,
        *,
        write_evidence: bool = True,
        receipt_status: str = "passed",
        receipt_task_id: str | None = None,
        verification_relative: str | None = None,
    ) -> None:
        relative = verification_relative or (
            "memory/sessions/test/verification/"
            f"{task_id}-verification.md"
        )
        if write_evidence:
            verification = self.root / relative
            verification.parent.mkdir(parents=True, exist_ok=True)
            verification.write_text(
                f"# Verification\n\n"
                f"Task ID: {receipt_task_id or task_id}\n"
                f"Status: {receipt_status}\n",
                encoding="utf-8",
            )
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": task_id,
                            "status": "closed",
                            "verification_status": "passed",
                            "verification": relative,
                            "closed_at": "2026-06-03T00:00:00+09:00",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def _write_job_receipt(self) -> None:
        jobs_dir = self.root / "memory" / "company" / "jobs"
        jobs_dir.mkdir(parents=True)
        receipt = jobs_dir / "job-0001-receipt.md"
        receipt.write_text("# receipt\n", encoding="utf-8")
        (jobs_dir / "jobs.json").write_text(
            '{"jobs":[{"id":"job-0001","commandName":"company.brief","status":"succeeded","createdAt":"2026-06-03T00:00:00Z","receipt":{"path":"memory/company/jobs/job-0001-receipt.md"},"events":[]}]}\n',
            encoding="utf-8",
        )

    def _write_active_job_without_receipt(self) -> None:
        jobs_dir = self.root / "memory" / "company" / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        (jobs_dir / "jobs.json").write_text(
            json.dumps(
                {
                    "jobs": [
                        {
                            "id": "job-0002",
                            "commandName": "agent.run",
                            "status": "running",
                            "createdAt": "2026-06-04T00:00:00Z",
                            "receipt": {},
                            "events": [],
                        }
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
