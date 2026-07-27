from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tools.studio.company import procurement as procurement_module
from tools.studio.jobs import get_job
from tools.studio.company.procurement import (
    OWNER_DECISION_FIELDS,
    TRUTH_PEN_CANDIDATES,
    procurement_decision_init,
)
from tools.studio.workspace_server import (
    MAX_PROCUREMENT_PREVIEW_BYTES,
    MAX_PROCUREMENT_STATUS_BYTES,
    PROCUREMENT_APPLY_CONFIRMATION,
    ProcurementApplyGrantStore,
    ProcurementApplyResultStore,
    build_command,
    collect_runtime_adapter_state,
    collect_workspace_state,
    read_workspace_file,
    run_command,
    run_local_command,
    _ensure_safe_bind,
    _handler,
    _host_header_allowed,
    _origin_allowed,
    _workflow_task_id,
)
from tools.studio.company.errors import CompanyError


class WorkspaceServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        (self.root / "tools").mkdir()
        channelctl = self.root / "tools" / "channelctl"
        channelctl.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import sys",
                    "from pathlib import Path",
                    "print('channelctl ' + ' '.join(sys.argv[1:]))",
                    "if sys.argv[1:3] == ['company', 'workflow']:",
                    "    output = Path('memory/company/workflows/task-0099-workflow.md')",
                    "    output.parent.mkdir(parents=True, exist_ok=True)",
                    "    output.write_text('# Workflow\\n', encoding='utf-8')",
                    "    print('Wrote memory/company/workflows/task-0099-workflow.md')",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        channelctl.chmod(0o755)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "channel_play_agent_company_plan.md").write_text("# plan\n", encoding="utf-8")
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (memory / "state.json").write_text(json.dumps({"project": "channel_play", "gdx1": {"ssh": "ok"}}), encoding="utf-8")
        (memory / "agent_registry.json").write_text(json.dumps({"agents": []}), encoding="utf-8")
        (memory / "task_board.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        (memory / "locks.json").write_text(json.dumps({"locks": []}), encoding="utf-8")
        (memory / "current_context.md").write_text("context\n", encoding="utf-8")
        (memory / "current_brief.md").write_text("brief\n", encoding="utf-8")
        (memory / "decision_log.md").write_text("decisions\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_collect_workspace_state(self) -> None:
        state = collect_workspace_state(self.root)
        self.assertEqual(state["project"], "channel_play")
        self.assertIn("company.status", state["commands"])
        self.assertIn("gameProduction", state)
        self.assertIn("game.productionCheck", state["commands"])
        self.assertIn("game.feedbackLoop", state["commands"])
        self.assertIn("asset.prepare", state["commands"])
        self.assertIn("asset.procurementCheck", state["commands"])
        self.assertIn("optimizationLoops", state["gameProduction"])
        self.assertEqual(state["jobs"], [])

    def test_collect_workspace_state_includes_project_brain_and_standards(self) -> None:
        state = collect_workspace_state(self.root)
        memory = state["memory"]

        self.assertEqual(memory["projectBrainPath"], "memory/company/project_brain.md")
        self.assertEqual(memory["userProfilePath"], "memory/company/user_profile.md")
        self.assertEqual(memory["agentMemoryPath"], "memory/company/agent_memory")
        self.assertEqual(memory["standardsPath"], "memory/company/standards")
        self.assertIn("Project Brain", memory["projectBrain"])
        self.assertGreaterEqual(len(memory["standards"]), 5)
        self.assertIn("evidence", {standard["id"] for standard in memory["standards"]})
        self.assertIn("unity_scripts", {standard["id"] for standard in memory["standards"]})

    def test_collect_workspace_state_includes_worker_fleet(self) -> None:
        state = collect_workspace_state(self.root)
        workers = {worker["id"]: worker for worker in state["workers"]["workers"]}

        self.assertIn("mac_studio", workers)
        self.assertIn("gdx1", workers)
        self.assertIn("local_ollama", workers)
        self.assertIn("capabilities", workers["mac_studio"])
        self.assertIn("recommended_jobs", workers["gdx1"])

    def test_collect_workspace_state_includes_model_cookbook(self) -> None:
        state = collect_workspace_state(self.root)
        cookbook = state["modelCookbook"]

        self.assertEqual(cookbook["hardware_profile"]["gpu_budget_gb"], 48)
        self.assertIn("gdx1_probe", cookbook)
        self.assertEqual(len(cookbook["use_cases"]), 9)
        self.assertIn("x86_server_soak", {row["use_case"] for row in cookbook["use_cases"]})
        self.assertTrue(all("verification_status" in row["primary"] for row in cookbook["use_cases"]))

    def test_collect_workspace_state_includes_runtime(self) -> None:
        state = collect_workspace_state(self.root)
        runtime = state["runtime"]

        self.assertIn("containerized", runtime)
        self.assertEqual(runtime["executionMode"], "local")
        self.assertEqual(runtime["hostRunner"]["status"], "local")
        self.assertIn("dockerSocketMounted", runtime)

    def test_collect_workspace_state_enriches_task_artifacts(self) -> None:
        memory = self.root / "memory" / "company"
        runs = self.root / "runs" / "agent-codex-task-0001"
        runs.mkdir(parents=True)
        (runs / "agent_run.md").write_text("# Agent Run\n", encoding="utf-8")
        (memory / "task-0001-plan.md").write_text("# Plan\n", encoding="utf-8")
        (memory / "workflows").mkdir()
        (memory / "workflows" / "task-0001-workflow.md").write_text("# Workflow\n", encoding="utf-8")
        (self.root / "memory" / "sessions" / "unassigned" / "verification").mkdir(parents=True)
        verification = "memory/sessions/unassigned/verification/task-0001-verification.md"
        (self.root / verification).write_text("# Verification\n", encoding="utf-8")
        (memory / "task_board.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "task-0001",
                            "request": "make mvp",
                            "status": "closed",
                            "last_agent_run": "runs/agent-codex-task-0001/agent_run.md",
                            "verification": verification,
                            "verification_status": "passed",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        state = collect_workspace_state(self.root)
        artifacts = state["company"]["tasks"][0]["artifacts"]

        self.assertEqual(
            [artifact["kind"] for artifact in artifacts],
            ["plan", "workflow", "answer", "verification"],
        )
        self.assertTrue(all(artifact["exists"] for artifact in artifacts))

    def test_collect_workspace_state_includes_agent_answer_summary(self) -> None:
        memory = self.root / "memory" / "company"
        run_path = self.root / "runs" / "agent-codex-task-0001" / "agent_run.md"
        run_path.parent.mkdir(parents=True)
        run_path.write_text(
            "\n".join(
                [
                    "# Agent Run",
                    "",
                    "## Task",
                    "make mvp",
                    "",
                    "## Output",
                    "진행 완료.",
                    "- 플레이어 이동 수정",
                    "- Unity compile 통과",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "task-0001",
                            "request": "make mvp",
                            "status": "closed",
                            "verification_status": "passed",
                            "agent_runs": [
                                {
                                    "tool": "codex",
                                    "mode": "run",
                                    "status": "ok",
                                    "path": "runs/agent-codex-task-0001/agent_run.md",
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        state = collect_workspace_state(self.root)
        answer = state["company"]["tasks"][0]["answerSummary"]

        self.assertEqual(answer["path"], "runs/agent-codex-task-0001/agent_run.md")
        self.assertIn("진행 완료", answer["summary"])
        self.assertIn("Unity compile 통과", answer["summary"])

    def test_collect_workspace_state_links_jobs_to_task_production_card(self) -> None:
        memory = self.root / "memory" / "company"
        jobs_dir = memory / "jobs"
        jobs_dir.mkdir()
        receipt = jobs_dir / "job-0001-receipt.md"
        receipt.write_text("# Job Receipt\n", encoding="utf-8")
        (memory / "task_board.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "task-0001",
                            "request": "make mvp",
                            "status": "needs_evidence",
                            "assigned_agent": "unity_gameplay",
                            "required_evidence": "Unity compile or playtest evidence",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (jobs_dir / "jobs.json").write_text(
            json.dumps(
                {
                    "jobs": [
                        {
                            "id": "job-0001",
                            "commandName": "agent.run",
                            "command": ["tools/channelctl", "agent", "run", "task-0001"],
                            "payload": {"taskId": "task-0001", "tool": "codex"},
                            "taskId": "task-0001",
                            "status": "succeeded",
                            "ok": True,
                            "createdAt": "2026-06-03T00:00:00Z",
                            "updatedAt": "2026-06-03T00:00:02Z",
                            "endedAt": "2026-06-03T00:00:02Z",
                            "receipt": {
                                "path": "memory/company/jobs/job-0001-receipt.md",
                                "summary": "done",
                                "verification": {"status": "passed"},
                            },
                            "events": [{"time": "2026-06-03T00:00:02Z", "type": "completed", "message": "done"}],
                            "isTerminal": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        state = collect_workspace_state(self.root)
        task = state["company"]["tasks"][0]

        self.assertEqual(task["jobs"][0]["id"], "job-0001")
        self.assertIn("receipt", [artifact["kind"] for artifact in task["artifacts"]])
        self.assertEqual(task["productionCard"]["receiptPath"], "memory/company/jobs/job-0001-receipt.md")
        self.assertEqual(task["productionCard"]["nextAction"]["command"], "company.advance")

    def test_build_command_rejects_unknown(self) -> None:
        with self.assertRaises(CompanyError):
            build_command(self.root, "shell.anything", {})

    def test_agent_run_command_builds_from_payload(self) -> None:
        command = build_command(
            self.root,
            "agent.run",
            {"taskId": "task-0006", "tool": "codex", "dryRun": True, "message": "smoke"},
        )

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "agent",
                "run",
                "task-0006",
                "--tool",
                "codex",
                "--dry-run",
                "--full-approval",
                "--message",
                "smoke",
            ],
        )

    def test_agent_run_manual_review_can_disable_full_approval(self) -> None:
        command = build_command(
            self.root,
            "agent.run",
            {"taskId": "task-0006", "tool": "codex", "manualReview": True},
        )

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "agent",
                "run",
                "task-0006",
                "--tool",
                "codex",
                "--manual-review",
            ],
        )

    def test_review_checkpoint_command_builds_from_payload(self) -> None:
        command = build_command(self.root, "company.review", {"taskId": "task-0006"})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "review",
                "task-0006",
                "critic_reviewer",
            ],
        )

    def test_advance_command_builds_from_payload(self) -> None:
        command = build_command(self.root, "company.advance", {"taskId": "task-0006"})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "advance",
                "task-0006",
            ],
        )

    def test_worker_probe_command_builds_from_payload(self) -> None:
        command = build_command(self.root, "company.workers.probe", {})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "workers",
                "--probe",
            ],
        )

    def test_model_cookbook_refresh_command_builds_from_payload(self) -> None:
        command = build_command(self.root, "company.models.refresh", {})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "models",
                "--refresh",
            ],
        )

    def test_game_production_commands_build_from_payload(self) -> None:
        self.assertEqual(
            build_command(self.root, "unity.compile", {}),
            [str(self.root / "tools" / "channelctl"), "unity", "check", "--batch"],
        )
        self.assertEqual(
            build_command(self.root, "unity.playtest", {}),
            [str(self.root / "tools" / "channelctl"), "unity", "playtest"],
        )
        self.assertEqual(
            build_command(self.root, "unity.build.windows", {}),
            [str(self.root / "tools" / "channelctl"), "unity", "build", "windows-dev"],
        )
        self.assertEqual(
            build_command(self.root, "unity.build.mac", {}),
            [str(self.root / "tools" / "channelctl"), "unity", "build", "mac-dev"],
        )
        self.assertEqual(
            build_command(self.root, "unity.build.linuxServer", {}),
            [str(self.root / "tools" / "channelctl"), "unity", "build", "linux-server"],
        )
        self.assertEqual(
            build_command(self.root, "game.productionCheck", {}),
            [str(self.root / "tools" / "channelctl"), "game", "production-check", "--capture", "--build"],
        )
        self.assertEqual(
            build_command(self.root, "game.feedbackLoop", {}),
            [str(self.root / "tools" / "channelctl"), "game", "feedback-loop"],
        )
        self.assertEqual(
            build_command(self.root, "game.serverHandoff", {}),
            [str(self.root / "tools" / "channelctl"), "game", "server-handoff"],
        )
        self.assertEqual(
            build_command(self.root, "asset.prepare", {"assetId": "prop"}),
            [str(self.root / "tools" / "channelctl"), "asset", "prepare", "prop"],
        )
        self.assertEqual(
            build_command(
                self.root,
                "asset.procurementCheck",
                {"assetId": "truth_pen"},
            ),
            [
                str(self.root / "tools" / "channelctl"),
                "asset",
                "procurement-check",
                "truth_pen",
            ],
        )

    def test_orchestrator_run_command_builds_from_payload(self) -> None:
        command = build_command(self.root, "orchestrator.run", {"request": "make mvp", "dryRun": True})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "workflow",
                "make mvp",
            ],
        )

    def test_orchestrator_run_defaults_to_real_mode(self) -> None:
        command = build_command(self.root, "orchestrator.run", {"request": "make mvp"})

        self.assertEqual(
            command,
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "workflow",
                "make mvp",
                "--real",
            ],
        )

    def test_goal_commands_build_from_payload(self) -> None:
        self.assertEqual(
            build_command(self.root, "company.goal.set", {"objective": "make mvp", "maxIterations": 5}),
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "goal",
                "set",
                "make mvp",
                "--max-iterations",
                "5",
            ],
        )
        self.assertEqual(
            build_command(self.root, "company.goal.run", {"dryRun": True, "maxIterations": 3}),
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "goal",
                "run",
                "--max-iterations",
                "3",
            ],
        )
        self.assertEqual(
            build_command(self.root, "company.goal.run", {"dryRun": False, "maxIterations": 3}),
            [
                str(self.root / "tools" / "channelctl"),
                "company",
                "goal",
                "run",
                "--max-iterations",
                "3",
                "--real",
            ],
        )

    def test_workflow_stdout_exposes_task_id(self) -> None:
        self.assertEqual(_workflow_task_id("Wrote memory/company/workflows/task-0011-workflow.md"), "task-0011")

    def test_run_command_forwards_to_host_runner_when_configured(self) -> None:
        with patch.dict(os.environ, {"CHANNEL_PLAY_HOST_RUNNER_URL": "http://127.0.0.1:9"}):
            with patch("tools.studio.workspace_server._run_command_via_host_runner") as forward:
                forward.return_value = {"ok": True, "jobId": "job-forwarded"}
                result = run_command(self.root, "company.status", {})

        self.assertEqual(result["jobId"], "job-forwarded")
        forward.assert_called_once_with(self.root, "company.status", {})

    def test_adapter_state_forwards_to_host_runner_when_configured(self) -> None:
        host_state = {"summary": {"available": 4, "total": 4}, "tools": {"codex": {"primaryExecutor": "codex_sdk"}}}
        with patch.dict(os.environ, {"CHANNEL_PLAY_HOST_RUNNER_URL": "http://127.0.0.1:9"}):
            with patch("tools.studio.workspace_server._fetch_host_adapters", return_value=host_state) as fetch:
                result = collect_runtime_adapter_state(self.root)

        self.assertEqual(result["tools"]["codex"]["primaryExecutor"], "codex_sdk")
        fetch.assert_called_once_with(self.root)

    def test_run_command_creates_async_job_receipt(self) -> None:
        result = run_local_command(self.root, "company.status", {})

        self.assertTrue(result["ok"])
        self.assertIn("jobId", result)
        job = self._wait_for_job(result["jobId"])

        self.assertEqual(job["status"], "succeeded")
        self.assertTrue(job["ok"])
        self.assertEqual(job["exit"], 0)
        self.assertIn("channelctl company status", job["stdout"])
        self.assertTrue(job["receipt"]["path"].startswith("memory/company/jobs/"))
        self.assertTrue((self.root / job["receipt"]["path"]).exists())
        self.assertIn("completed", [event["type"] for event in job["events"]])

    def test_orchestrator_job_extracts_task_id_and_workflow_path(self) -> None:
        result = run_local_command(self.root, "orchestrator.run", {"request": "make mvp", "dryRun": True})
        job = self._wait_for_job(result["jobId"])

        self.assertEqual(job["status"], "succeeded")
        self.assertEqual(job["taskId"], "task-0099")
        self.assertEqual(job["workflowPath"], "memory/company/workflows/task-0099-workflow.md")
        self.assertIn("memory/company/workflows/task-0099-workflow.md", job["receipt"]["artifacts"])

    def test_read_workspace_file_rejects_escape(self) -> None:
        with self.assertRaises(CompanyError):
            read_workspace_file(self.root, "../secret")

    def test_refuses_non_loopback_bind_without_override(self) -> None:
        previous = os.environ.pop("CHANNEL_PLAY_STUDIO_ALLOW_REMOTE", None)
        try:
            with self.assertRaises(CompanyError):
                _ensure_safe_bind("0.0.0.0")
        finally:
            if previous is not None:
                os.environ["CHANNEL_PLAY_STUDIO_ALLOW_REMOTE"] = previous

    def test_command_api_requires_execution_token(self) -> None:
        server, thread, base = self._start_server("test-token")
        try:
            with self.assertRaises(urllib.error.HTTPError) as missing:
                self._post_command(base, token="")
            self.assertEqual(missing.exception.code, 400)
            missing.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as wrong_origin:
                self._post_command(base, token="test-token", origin="http://evil.example")
            self.assertEqual(wrong_origin.exception.code, 400)
            wrong_origin.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as wrong_type:
                self._post_command(base, token="test-token", content_type="text/plain")
            self.assertEqual(wrong_type.exception.code, 400)
            wrong_type.exception.close()

            data = self._post_command(base, token="test-token")
            self.assertTrue(data["ok"])
            self.assertIn("jobId", data)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_command_api_allows_loopback_docker_port_mapping(self) -> None:
        self.assertTrue(_host_header_allowed("127.0.0.1:8778", "0.0.0.0", 8776))
        self.assertTrue(_origin_allowed("http://127.0.0.1:8778", "0.0.0.0", 8776))
        self.assertFalse(_host_header_allowed("evil.example:8778", "0.0.0.0", 8776))
        self.assertFalse(_origin_allowed("http://evil.example:8778", "0.0.0.0", 8776))

    def test_procurement_preview_api_is_protected_and_side_effect_free(
        self,
    ) -> None:
        manifest = self._write_procurement_fixture()
        before = manifest.read_bytes()
        server, thread, base = self._start_server("test-token")
        try:
            with self.assertRaises(urllib.error.HTTPError) as missing:
                self._post_procurement_preview(
                    base,
                    token="",
                    answers={"owner.governing_jurisdiction": "KR"},
                )
            self.assertEqual(missing.exception.code, 400)
            missing.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as wrong_origin:
                self._post_procurement_preview(
                    base,
                    token="test-token",
                    origin="http://evil.example",
                    answers={"owner.governing_jurisdiction": "KR"},
                )
            self.assertEqual(wrong_origin.exception.code, 400)
            wrong_origin.exception.close()

            result = self._post_procurement_preview(
                base,
                token="test-token",
                answers={"owner.governing_jurisdiction": "KR"},
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["previewOnly"])
            self.assertFalse(result["valid"])
            self.assertFalse(result["contactAuthorized"])
            self.assertFalse(result["receiptCreated"])
            self.assertEqual(result["answerCount"], 1)
            self.assertEqual(result["changeCount"], 1)
            self.assertEqual(result["unchangedCount"], 0)
            self.assertEqual(
                result["changedFields"],
                ["owner.governing_jurisdiction"],
            )
            self.assertTrue(result["protectedStatePreserved"])
            self.assertNotIn("applyGrant", result)
            self.assertNotIn(
                "applyResultRecoveryExpiresInSeconds",
                result,
            )
            self.assertEqual(manifest.read_bytes(), before)
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_noop_preview_does_not_mint_apply_grant(
        self,
    ) -> None:
        manifest = self._write_procurement_fixture()
        answers = self._complete_procurement_answers()
        self._write_procurement_answers(manifest, answers)
        before = manifest.read_bytes()
        server, thread, base = self._start_server("test-token")
        try:
            result = self._post_procurement_preview(
                base,
                token="test-token",
                answers=answers,
            )
            encoded = json.dumps(result, ensure_ascii=False)

            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["changeCount"], 0)
            self.assertEqual(result["unchangedCount"], 16)
            self.assertEqual(result["changedFields"], [])
            self.assertTrue(result["protectedStatePreserved"])
            self.assertNotIn("applyGrant", result)
            self.assertNotIn(
                "applyResultRecoveryExpiresInSeconds",
                result,
            )
            self.assertNotIn("550e8400-e29b-41d4-a716-446655440000", encoded)
            self.assertNotIn("cynthia_ignacio", encoded)

            with self.assertRaises(urllib.error.HTTPError) as noop:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant="not-issued",
                    manifest_sha256=result["manifestSha256"],
                )
            self.assertEqual(noop.exception.code, 400)
            noop.exception.close()
            self.assertEqual(manifest.read_bytes(), before)
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_preview_api_rejects_oversize_and_nonfinite_json(
        self,
    ) -> None:
        self._write_procurement_fixture()
        server, thread, base = self._start_server("test-token")
        try:
            oversized = json.dumps(
                {
                    "assetId": "truth_pen",
                    "answers": {
                        "decision_status": (
                            "x" * MAX_PROCUREMENT_PREVIEW_BYTES
                        )
                    },
                }
            ).encode("utf-8")
            with self.assertRaises(urllib.error.HTTPError) as too_large:
                self._post_procurement_preview(
                    base,
                    token="test-token",
                    raw_body=oversized,
                )
            self.assertEqual(too_large.exception.code, 400)
            too_large.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as nonfinite:
                self._post_procurement_preview(
                    base,
                    token="test-token",
                    raw_body=(
                        b'{"assetId":"truth_pen","answers":'
                        b'{"commercial.budget_ceiling":NaN}}'
                    ),
                )
            self.assertEqual(nonfinite.exception.code, 400)
            nonfinite.exception.close()
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_apply_grant_is_bound_and_one_time(self) -> None:
        clock = [100.0]
        grants = ProcurementApplyGrantStore(10, lambda: clock[0])
        grant = grants.mint("truth_pen", "a" * 64, "b" * 64)

        with self.assertRaisesRegex(CompanyError, "does not match"):
            grants.consume(
                grant,
                "truth_pen",
                "c" * 64,
                "b" * 64,
            )

        grants.consume(grant, "truth_pen", "a" * 64, "b" * 64)
        with self.assertRaisesRegex(CompanyError, "invalid or expired"):
            grants.consume(grant, "truth_pen", "a" * 64, "b" * 64)

        limited = ProcurementApplyGrantStore(
            10,
            lambda: clock[0],
            max_grants=1,
        )
        evicted = limited.mint("truth_pen", "a" * 64, "b" * 64)
        retained = limited.mint("truth_pen", "c" * 64, "d" * 64)
        with self.assertRaisesRegex(CompanyError, "invalid or expired"):
            limited.consume(
                evicted,
                "truth_pen",
                "a" * 64,
                "b" * 64,
            )
        limited.consume(
            retained,
            "truth_pen",
            "c" * 64,
            "d" * 64,
        )

    def test_procurement_apply_result_store_is_bounded_and_redacted(
        self,
    ) -> None:
        clock = [100.0]
        store = ProcurementApplyResultStore(
            10,
            lambda: clock[0],
            max_results=2,
        )
        attempt_a = "a" * 32
        attempt_b = "b" * 32
        attempt_c = "c" * 32
        safe_result = {
            "saved": True,
            "savedVerified": True,
            "savedChangeCount": len(OWNER_DECISION_FIELDS),
            "savedChangedFields": list(OWNER_DECISION_FIELDS),
            "protectedStatePreserved": True,
            "contactAuthorized": False,
            "receiptCreated": False,
            "manifest": (
                "asset_pipeline/manifests/"
                "truth_pen_procurement_decision.json"
            ),
            "manifestSha256": "d" * 64,
            "nextCommand": "asset.procurementCheck",
            "answers": {"owner.secure_record_id": "vault:secret"},
        }

        store.reserve(attempt_a, "truth_pen")
        self.assertEqual(
            store.lookup(attempt_a, "truth_pen"),
            {"found": False, "pending": True},
        )
        with self.assertRaisesRegex(CompanyError, "already been used"):
            store.reserve(attempt_a, "truth_pen")
        store.complete(attempt_a, "truth_pen", safe_result)
        safe_result["savedChangedFields"].append("owner.secret")
        recovered = store.lookup(attempt_a, "truth_pen")
        self.assertTrue(recovered["found"])
        self.assertFalse(recovered["pending"])
        self.assertNotIn("answers", recovered)
        self.assertNotIn("vault:secret", json.dumps(recovered))
        self.assertEqual(
            recovered["savedChangedFields"],
            list(OWNER_DECISION_FIELDS),
        )
        recovered["savedChangedFields"].append("owner.secret")
        self.assertEqual(
            store.lookup(attempt_a, "truth_pen")["savedChangedFields"],
            list(OWNER_DECISION_FIELDS),
        )
        self.assertEqual(
            store.lookup(attempt_a, "other_asset"),
            {"found": False, "pending": False},
        )

        clock[0] = 101.0
        store.reserve(attempt_b, "truth_pen")
        clock[0] = 102.0
        store.reserve(attempt_c, "truth_pen")
        self.assertFalse(store.lookup(attempt_a, "truth_pen")["found"])
        self.assertTrue(store.lookup(attempt_c, "truth_pen")["pending"])
        clock[0] = 112.0
        self.assertEqual(
            store.lookup(attempt_c, "truth_pen"),
            {"found": False, "pending": False},
        )

        with self.assertRaisesRegex(CompanyError, "invalid"):
            store.reserve("not-random", "truth_pen")
        store.reserve("e" * 32, "truth_pen")
        unsafe = dict(safe_result)
        unsafe["savedChangedFields"] = list(OWNER_DECISION_FIELDS)
        unsafe["contactAuthorized"] = True
        with self.assertRaisesRegex(CompanyError, "retained safely"):
            store.complete("e" * 32, "truth_pen", unsafe)

    def test_procurement_apply_api_requires_confirmation_and_is_one_time(
        self,
    ) -> None:
        manifest = self._write_procurement_fixture()
        answers = self._complete_procurement_answers()
        before = manifest.read_bytes()
        server, thread, base = self._start_server(
            "test-token",
            procurement_result_ttl_seconds=17,
        )
        try:
            preview = self._post_procurement_preview(
                base,
                token="test-token",
                answers=answers,
            )
            self.assertTrue(preview["valid"])
            self.assertTrue(preview["applyGrant"])
            self.assertEqual(
                preview["applyResultRecoveryExpiresInSeconds"],
                17,
            )

            with self.assertRaises(urllib.error.HTTPError) as missing_token:
                self._post_procurement_apply(
                    base,
                    token="",
                    answers=answers,
                    grant=preview["applyGrant"],
                    manifest_sha256=preview["manifestSha256"],
                )
            self.assertEqual(missing_token.exception.code, 400)
            missing_token.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as confirmation:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=preview["applyGrant"],
                    manifest_sha256=preview["manifestSha256"],
                    confirmation="not-confirmed",
                )
            self.assertEqual(confirmation.exception.code, 400)
            confirmation.exception.close()
            self.assertEqual(manifest.read_bytes(), before)

            with self.assertRaises(urllib.error.HTTPError) as invalid_attempt:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=preview["applyGrant"],
                    manifest_sha256=preview["manifestSha256"],
                    attempt_id="predictable",
                )
            self.assertEqual(invalid_attempt.exception.code, 400)
            invalid_attempt.exception.close()
            self.assertEqual(manifest.read_bytes(), before)

            result = self._post_procurement_apply(
                base,
                token="test-token",
                answers=answers,
                grant=preview["applyGrant"],
                manifest_sha256=preview["manifestSha256"],
            )
            self.assertTrue(result["saved"])
            self.assertTrue(result["savedVerified"])
            self.assertFalse(result["contactAuthorized"])
            self.assertFalse(result["receiptCreated"])
            self.assertEqual(result["savedChangeCount"], 16)
            self.assertEqual(
                result["savedChangedFields"],
                list(answers),
            )
            self.assertTrue(result["protectedStatePreserved"])
            self.assertEqual(
                result["nextCommand"],
                "asset.procurementCheck",
            )
            saved = manifest.read_bytes()
            self.assertNotEqual(saved, before)
            self.assertFalse((self.root / "runs").exists())

            recovered = self._post_procurement_status(
                base,
                token="test-token",
                attempt_id="a" * 32,
            )
            self.assertTrue(recovered["found"])
            self.assertFalse(recovered["pending"])
            self.assertTrue(recovered["saved"])
            self.assertTrue(recovered["savedVerified"])
            self.assertNotIn(
                "550e8400-e29b-41d4-a716-446655440000",
                json.dumps(recovered),
            )

            with self.assertRaises(urllib.error.HTTPError) as replay:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=preview["applyGrant"],
                    manifest_sha256=result["manifestSha256"],
                )
            self.assertEqual(replay.exception.code, 400)
            replay.exception.close()
            self.assertEqual(manifest.read_bytes(), saved)
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_apply_status_is_protected_strict_and_expires(
        self,
    ) -> None:
        clock = [100.0]
        store = ProcurementApplyResultStore(1, lambda: clock[0])
        store.reserve("f" * 32, "truth_pen")
        server, thread, base = self._start_server(
            "test-token",
            procurement_result_store=store,
        )
        try:
            pending = self._post_procurement_status(
                base,
                token="test-token",
                attempt_id="f" * 32,
            )
            self.assertEqual(
                pending,
                {"ok": True, "found": False, "pending": True},
            )
            wrong_asset = self._post_procurement_status(
                base,
                token="test-token",
                attempt_id="f" * 32,
                asset_id="other_asset",
            )
            self.assertEqual(
                wrong_asset,
                {"ok": True, "found": False, "pending": False},
            )

            with self.assertRaises(urllib.error.HTTPError) as missing_token:
                self._post_procurement_status(
                    base,
                    token="",
                    attempt_id="f" * 32,
                )
            self.assertEqual(missing_token.exception.code, 400)
            missing_token.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as invalid_id:
                self._post_procurement_status(
                    base,
                    token="test-token",
                    attempt_id="not-random",
                )
            self.assertEqual(invalid_id.exception.code, 400)
            invalid_id.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as extra_field:
                self._post_procurement_status(
                    base,
                    token="test-token",
                    attempt_id="f" * 32,
                    raw_body=json.dumps(
                        {
                            "assetId": "truth_pen",
                            "applyAttemptId": "f" * 32,
                            "answers": {},
                        }
                    ).encode("utf-8"),
                )
            self.assertEqual(extra_field.exception.code, 400)
            extra_field.exception.close()

            with self.assertRaises(urllib.error.HTTPError) as too_large:
                self._post_procurement_status(
                    base,
                    token="test-token",
                    attempt_id="f" * 32,
                    raw_body=b"{" + b" " * MAX_PROCUREMENT_STATUS_BYTES,
                )
            self.assertEqual(too_large.exception.code, 400)
            too_large.exception.close()

            clock[0] = 102.0
            expired = self._post_procurement_status(
                base,
                token="test-token",
                attempt_id="f" * 32,
            )
            self.assertEqual(
                expired,
                {"ok": True, "found": False, "pending": False},
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_apply_api_reports_post_write_mismatch(
        self,
    ) -> None:
        manifest = self._write_procurement_fixture()
        answers = self._complete_procurement_answers()
        server, thread, base = self._start_server("test-token")
        real_atomic_write = procurement_module._write_json_atomic

        def write_then_tamper(path: Path, data: dict) -> None:
            real_atomic_write(path, data)
            stored = json.loads(path.read_text(encoding="utf-8"))
            stored["task_id"] = "task-0099"
            path.write_text(
                json.dumps(stored, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        try:
            preview = self._post_procurement_preview(
                base,
                token="test-token",
                answers=answers,
            )
            with patch(
                "tools.studio.company.procurement._write_json_atomic",
                side_effect=write_then_tamper,
            ):
                result = self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=preview["applyGrant"],
                    manifest_sha256=preview["manifestSha256"],
                )
            encoded = json.dumps(result, ensure_ascii=False)

            self.assertTrue(result["saved"])
            self.assertFalse(result["savedVerified"])
            self.assertEqual(result["savedChangeCount"], 16)
            self.assertEqual(
                result["savedChangedFields"],
                list(answers),
            )
            self.assertTrue(result["protectedStatePreserved"])
            self.assertFalse(result["contactAuthorized"])
            self.assertFalse(result["receiptCreated"])
            recovered = self._post_procurement_status(
                base,
                token="test-token",
                attempt_id="a" * 32,
            )
            self.assertTrue(recovered["found"])
            self.assertFalse(recovered["savedVerified"])
            self.assertNotIn(
                "550e8400-e29b-41d4-a716-446655440000",
                encoded,
            )
            self.assertNotIn("cynthia_ignacio", encoded)
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_procurement_apply_api_rejects_stale_and_expired_grants(
        self,
    ) -> None:
        manifest = self._write_procurement_fixture()
        answers = self._complete_procurement_answers()
        clock = [100.0]
        server, thread, base = self._start_server(
            "test-token",
            procurement_grant_ttl_seconds=1,
            procurement_grant_clock=lambda: clock[0],
        )
        try:
            expired_preview = self._post_procurement_preview(
                base,
                token="test-token",
                answers=answers,
            )
            clock[0] = 102.0
            with self.assertRaises(urllib.error.HTTPError) as expired:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=expired_preview["applyGrant"],
                    manifest_sha256=expired_preview["manifestSha256"],
                )
            self.assertEqual(expired.exception.code, 400)
            expired.exception.close()

            clock[0] = 103.0
            stale_preview = self._post_procurement_preview(
                base,
                token="test-token",
                answers=answers,
            )
            decision = json.loads(manifest.read_text(encoding="utf-8"))
            decision["task_id"] = "task-0099"
            manifest.write_text(
                json.dumps(decision, indent=2) + "\n",
                encoding="utf-8",
            )
            stale_bytes = manifest.read_bytes()

            with self.assertRaises(urllib.error.HTTPError) as stale:
                self._post_procurement_apply(
                    base,
                    token="test-token",
                    answers=answers,
                    grant=stale_preview["applyGrant"],
                    manifest_sha256=stale_preview["manifestSha256"],
                )
            self.assertEqual(stale.exception.code, 400)
            stale.exception.close()
            self.assertEqual(manifest.read_bytes(), stale_bytes)
            self.assertFalse((self.root / "runs").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_search_api_returns_source_type_and_preview(self) -> None:
        (self.root / "memory" / "sessions" / "session-a").mkdir(parents=True)
        (self.root / "memory" / "sessions" / "session-a" / "summary.md").write_text(
            "# Session\nUnity compile error for task-0042 by unity_gameplay.\n",
            encoding="utf-8",
        )
        server, thread, base = self._start_server("test-token")
        try:
            data = self._get_json(f"{base}/api/search?q=Unity%20compile&rebuild=1")
            self.assertGreater(data["count"], 0)
            self.assertIn("sourceType", data["results"][0])
            self.assertIn("preview", data["results"][0])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def _wait_for_job(self, job_id: str) -> dict:
        for _ in range(80):
            job = get_job(self.root, job_id)
            if job and job["isTerminal"]:
                return job
            time.sleep(0.05)
        self.fail(f"Job did not finish: {job_id}")

    def _start_server(self, token: str, **handler_kwargs):
        port = _free_port()
        server = ThreadingHTTPServer(
            ("127.0.0.1", port),
            _handler(
                self.root,
                token=token,
                host="127.0.0.1",
                port=port,
                **handler_kwargs,
            ),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, f"http://127.0.0.1:{port}"

    def _post_command(self, base: str, token: str, origin: str = "", content_type: str = "application/json") -> dict:
        body = json.dumps({"command": "company.status", "payload": {}}).encode("utf-8")
        headers = {"Content-Type": content_type}
        if token:
            headers["X-Channel-Play-Token"] = token
        if origin:
            headers["Origin"] = origin
        request = urllib.request.Request(f"{base}/api/command", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_procurement_preview(
        self,
        base: str,
        token: str,
        *,
        answers: dict | None = None,
        origin: str = "",
        raw_body: bytes | None = None,
    ) -> dict:
        body = raw_body or json.dumps(
            {
                "assetId": "truth_pen",
                "answers": answers if answers is not None else {},
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Channel-Play-Token"] = token
        if origin:
            headers["Origin"] = origin
        request = urllib.request.Request(
            f"{base}/api/procurement/preview",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_procurement_apply(
        self,
        base: str,
        token: str,
        *,
        answers: dict,
        grant: str,
        manifest_sha256: str,
        confirmation: str = PROCUREMENT_APPLY_CONFIRMATION,
        attempt_id: str = "a" * 32,
    ) -> dict:
        body = json.dumps(
            {
                "assetId": "truth_pen",
                "answers": answers,
                "applyAttemptId": attempt_id,
                "applyGrant": grant,
                "confirmation": confirmation,
                "expectedManifestSha256": manifest_sha256,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Channel-Play-Token"] = token
        request = urllib.request.Request(
            f"{base}/api/procurement/apply",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_procurement_status(
        self,
        base: str,
        token: str,
        *,
        attempt_id: str,
        asset_id: str = "truth_pen",
        raw_body: bytes | None = None,
    ) -> dict:
        body = raw_body or json.dumps(
            {
                "assetId": asset_id,
                "applyAttemptId": attempt_id,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Channel-Play-Token"] = token
        request = urllib.request.Request(
            f"{base}/api/procurement/apply-status",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _write_procurement_fixture(self) -> Path:
        (self.root / "asset_pipeline" / "briefs").mkdir(parents=True)
        (self.root / "asset_pipeline" / "index.json").write_text(
            json.dumps(
                {"assets": [{"id": "truth_pen", "status": "briefed"}]}
            ),
            encoding="utf-8",
        )
        (
            self.root
            / "asset_pipeline"
            / "briefs"
            / "truth_pen_commission_rfp.md"
        ).write_text("# RFP\n", encoding="utf-8")
        (
            self.root
            / "docs"
            / "research"
        ).mkdir(parents=True, exist_ok=True)
        (
            self.root
            / "docs"
            / "research"
            / "truth_pen_artist_procurement_packet.md"
        ).write_text("# Packet\n", encoding="utf-8")
        return procurement_decision_init(self.root, "truth_pen")

    @staticmethod
    def _write_procurement_answers(
        manifest: Path,
        answers: dict,
    ) -> None:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for field, value in answers.items():
            if "." not in field:
                data[field] = value
                continue
            section, key = field.split(".", 1)
            data[section][key] = value
        manifest.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _complete_procurement_answers() -> dict:
        proposal = date.today() + timedelta(days=14)
        delivery = proposal + timedelta(days=21)
        return {
            "decision_status": "approved_for_proposal_outreach",
            "owner.secure_record_id": (
                "vault:550e8400-e29b-41d4-a716-446655440000"
            ),
            "owner.authorized_signer_role": "project_owner",
            "owner.governing_jurisdiction": "KR",
            "commercial.budget_ceiling": 1500,
            "commercial.currency": "USD",
            "commercial.payment_route": "upwork",
            "commercial.tax_vendor_process_confirmed_securely": True,
            "schedule.proposal_deadline": proposal.isoformat(),
            "schedule.desired_delivery_date": delivery.isoformat(),
            "schedule.revision_limit": 2,
            "outreach.authorized": True,
            "outreach.authorized_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "outreach.scope": "all",
            "outreach.candidate_ids": sorted(TRUTH_PEN_CANDIDATES),
            "privacy.sensitive_data_stored_outside_repo": True,
        }

    def _get_json(self, url: str) -> dict:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
