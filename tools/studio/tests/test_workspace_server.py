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
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tools.studio.jobs import get_job
from tools.studio.company.procurement import procurement_decision_init
from tools.studio.workspace_server import (
    MAX_PROCUREMENT_PREVIEW_BYTES,
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

    def _start_server(self, token: str):
        port = _free_port()
        server = ThreadingHTTPServer(("127.0.0.1", port), _handler(self.root, token=token, host="127.0.0.1", port=port))
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

    def _get_json(self, url: str) -> dict:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
