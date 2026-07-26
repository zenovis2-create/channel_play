from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.studio.company.game_production import game_production_state, render_game_production_status


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
        (capture_dir / "screen.png").write_bytes(b"png")

        state = game_production_state(self.root)

        self.assertEqual(state["readiness"], {"passed": 6, "total": 6, "status": "ready"})
        self.assertEqual(state["unity"]["compile"]["path"], "runs/unity-check-001/unity_check.md")
        self.assertEqual(state["gdx"]["path"], "runs/gdx-probe-001/gdx_probe.md")

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
        (capture_dir / "screen.png").write_bytes(b"png")

    def _write_asset_index(self) -> None:
        asset_index = self.root / "asset_pipeline" / "index.json"
        asset_index.parent.mkdir(parents=True)
        asset_index.write_text(
            '{"assets":[{"id":"prop","status":"generated","pipeline_receipt":"runs/asset-pipeline-prop/asset_pipeline_receipt.md"}]}',
            encoding="utf-8",
        )

    def _write_assigned_task(self, task_id: str) -> None:
        board = self.root / "memory" / "company" / "task_board.json"
        board.parent.mkdir(parents=True)
        board.write_text(
            f'{{"tasks":[{{"id":"{task_id}","status":"assigned","updated_at":"2026-06-03T00:00:00+09:00","work_order":"memory/sessions/test/work_orders/{task_id}.md"}}]}}',
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


if __name__ == "__main__":
    unittest.main()
