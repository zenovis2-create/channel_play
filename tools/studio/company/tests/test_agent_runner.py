from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import tools.studio.company.agent_runner as agent_runner_module
from tools.studio.company.agent_runner import collect_agent_adapter_state, run_agent_task, run_agent_task_full_approval
from tools.studio.company.planner import assign_task, plan_task
from tools.studio.company.reports import create_review_checkpoint
from tools.studio.company.sessions import start_session
from tools.studio.company.state import load_task_board
from tools.studio.company.verify import verify_task
from tools.studio.company.workflow import run_orchestrator_workflow


class AgentRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "channel_play_agent_company_plan.md").write_text("# plan\n", encoding="utf-8")
        (self.root / "agents" / "roles").mkdir(parents=True)
        (self.root / "agents" / "roles" / "unity_gameplay.agent.md").write_text("# Unity Gameplay\n", encoding="utf-8")
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (memory / "state.json").write_text(
            json.dumps(
                {
                    "project": "channel_play",
                    "active_session": None,
                    "current_orchestrator_task": None,
                    "integrated_goal": {"id": "mvp_traitor_escape_gameshow", "title": "MVP"},
                }
            ),
            encoding="utf-8",
        )
        (memory / "agent_registry.json").write_text(
            json.dumps(
                {
                    "agents": [
                        {
                            "id": "unity_gameplay",
                            "profile": "agents/roles/unity_gameplay.agent.md",
                            "goal_setting": {
                                "goal_id": "mvp_traitor_escape_gameshow",
                                "tool": "agy",
                                "focus": "movement",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        (memory / "locks.json").write_text(json.dumps({"locks": []}), encoding="utf-8")
        (memory / "current_context.md").write_text("# context\n", encoding="utf-8")
        (memory / "current_brief.md").write_text("# brief\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dry_run_writes_agent_run_without_external_process(self) -> None:
        start_session(self.root, "agent smoke")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")

        report = run_agent_task(self.root, "task-0001", dry_run=True)

        self.assertTrue(report.exists())
        self.assertTrue((report.parent / "prompt.md").exists())
        prompt = (report.parent / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("## Integrated Goal", prompt)
        self.assertIn("mvp_traitor_escape_gameshow", prompt)
        self.assertIn("## Current Agent Setting", prompt)
        self.assertIn("Tool: agy", prompt)
        self.assertIn("Dry run", (report.parent / "stdout.txt").read_text(encoding="utf-8"))
        task = load_task_board(self.root)["tasks"][0]
        self.assertEqual(task["last_tool"], "agy")
        self.assertEqual(task["agent_status"], "dry_run")
        self.assertEqual(task["status"], "needs_review")
        self.assertEqual(task["report"], report.relative_to(self.root).as_posix())
        self.assertEqual(task["agent_runs"][0]["mode"], "run")

    def test_review_dry_run_moves_to_evidence_step(self) -> None:
        start_session(self.root, "review smoke")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")

        run_agent_task(self.root, "task-0001", dry_run=True)
        report = run_agent_task(self.root, "task-0001", mode="review", dry_run=True)

        task = load_task_board(self.root)["tasks"][0]
        self.assertEqual(task["status"], "needs_evidence")
        self.assertEqual(task["report"], report.relative_to(self.root).as_posix())
        self.assertEqual(task["agent_runs"][-1]["mode"], "review")

    def test_fast_workflow_closes_without_manual_evidence_attachment(self) -> None:
        start_session(self.root, "full smoke")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")

        run_agent_task(self.root, "task-0001", dry_run=True)
        create_review_checkpoint(self.root, "task-0001")
        verify_task(self.root, "task-0001")

        task = load_task_board(self.root)["tasks"][0]
        self.assertEqual(task["status"], "closed")
        self.assertEqual(task["verification_status"], "passed")
        self.assertTrue(task["evidence"])

    def test_full_approval_agent_run_closes_task(self) -> None:
        start_session(self.root, "full approval")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")

        report, advance = run_agent_task_full_approval(self.root, "task-0001", dry_run=True)

        task = load_task_board(self.root)["tasks"][0]
        self.assertTrue(report.exists())
        self.assertIsNotNone(advance)
        self.assertEqual(task["status"], "closed")
        self.assertEqual(task["verification_status"], "passed")
        self.assertEqual(task["review_status"], "reviewed")

    def test_orchestrator_workflow_runs_end_to_end(self) -> None:
        report = run_orchestrator_workflow(self.root, "fix player movement", dry_run=True)

        task = load_task_board(self.root)["tasks"][0]
        self.assertTrue(report.exists())
        self.assertEqual(task["status"], "closed")
        self.assertEqual(task["verification_status"], "passed")
        self.assertEqual(task["agent_runs"][0]["mode"], "run")
        self.assertEqual(task["agent_runs"][-1]["mode"], "review")

    def test_adapter_state_creates_default_config(self) -> None:
        state = collect_agent_adapter_state(self.root)

        self.assertIn("codex", state["tools"])
        self.assertTrue((self.root / "memory" / "company" / "tool_adapters.json").exists())

        config = json.loads((self.root / "memory" / "company" / "tool_adapters.json").read_text(encoding="utf-8"))
        self.assertNotIn("claude", config["tools"])
        self.assertIn("claude", config["excluded_tools"])
        self.assertEqual(config["review_tool"], "codex")
        self.assertEqual(config["role_defaults"]["game_director"], "hermes")
        self.assertEqual(config["role_defaults"]["critic_reviewer"], "codex")
        self.assertEqual(config["role_defaults"]["production_planner"], "codex")
        self.assertEqual(config["role_defaults"]["coding_specialist"], "codex")
        self.assertEqual(config["role_defaults"]["toolchain_integrator"], "codex")
        self.assertEqual(config["role_defaults"]["operator_broadcast_designer"], "hermes")
        self.assertEqual(config["tools"]["codex"]["execution"], "codex_auto")
        self.assertEqual(config["tools"]["codex"]["sdk_package"], "openai_codex")
        self.assertIn("status", state["tools"]["codex"])
        self.assertIn("defaultRoles", state["tools"]["codex"])
        self.assertIn("primaryExecutor", state["tools"]["codex"])
        agy_argv = config["tools"]["agy"]["argv"]
        self.assertLess(agy_argv.index("--print-timeout"), agy_argv.index("--print"))

    def test_codex_adapter_uses_python_sdk_when_available(self) -> None:
        start_session(self.root, "sdk smoke")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")
        sdk_status = {
            "available": True,
            "status": "available",
            "package": "openai_codex",
            "version": "0.1.0",
            "origin": "/sdk",
            "last_error": "",
        }

        with (
            patch.object(agent_runner_module, "codex_sdk_status", return_value=sdk_status),
            patch.object(
                agent_runner_module,
                "run_codex_sdk_turn",
                return_value={
                    "status": "ok",
                    "exit": 0,
                    "stdout": "SDK completed the task.\n",
                    "stderr": "",
                    "executor": "codex_sdk",
                    "sdk": sdk_status,
                },
            ) as run_sdk,
        ):
            report = run_agent_task(self.root, "task-0001", tool_name="codex")

        run_sdk.assert_called_once()
        command = json.loads((report.parent / "command.json").read_text(encoding="utf-8"))
        self.assertEqual(command["executor"], "codex_sdk")
        self.assertEqual(command["sdk"]["package"], "openai_codex")
        self.assertIn("SDK completed", (report.parent / "stdout.txt").read_text(encoding="utf-8"))
        task = load_task_board(self.root)["tasks"][0]
        self.assertEqual(task["last_tool"], "codex")
        self.assertEqual(task["agent_status"], "ok")
        self.assertEqual(task["status"], "needs_review")

    def test_codex_adapter_falls_back_to_cli_when_sdk_auth_fails(self) -> None:
        fake = self.root / "fake_codex.py"
        fake.write_text(
            "print('CLI fallback completed.')\n",
            encoding="utf-8",
        )
        collect_agent_adapter_state(self.root)
        adapter_config = json.loads((self.root / "memory" / "company" / "tool_adapters.json").read_text(encoding="utf-8"))
        adapter_config["tools"]["codex"]["argv"] = [sys.executable, str(fake), "{prompt}"]
        adapter_config["tools"]["codex"]["version_command"] = [sys.executable, str(fake), "--version"]
        (self.root / "memory" / "company" / "tool_adapters.json").write_text(
            json.dumps(adapter_config),
            encoding="utf-8",
        )
        start_session(self.root, "sdk fallback")
        plan_task(self.root, "fix player movement")
        assign_task(self.root, "task-0001", "unity_gameplay")
        sdk_status = {
            "available": True,
            "status": "available",
            "package": "openai_codex",
            "version": "0.1.0",
            "origin": "/sdk",
            "last_error": "",
        }

        with (
            patch.object(agent_runner_module, "codex_sdk_status", return_value=sdk_status),
            patch.object(
                agent_runner_module,
                "run_codex_sdk_turn",
                return_value={
                    "status": "auth_missing",
                    "exit": 1,
                    "stdout": "",
                    "stderr": "Access token is unavailable.\n",
                    "executor": "codex_sdk",
                    "sdk": sdk_status,
                },
            ),
        ):
            report = run_agent_task(self.root, "task-0001", tool_name="codex")

        command = json.loads((report.parent / "command.json").read_text(encoding="utf-8"))
        self.assertEqual(command["executor"], "cli_fallback")
        self.assertIn("CLI fallback completed", (report.parent / "stdout.txt").read_text(encoding="utf-8"))
        task = load_task_board(self.root)["tasks"][0]
        self.assertEqual(task["agent_status"], "ok")

    def test_adapter_health_matrix_reports_version_path_and_roles(self) -> None:
        fake = self.root / "fake_agent.py"
        fake.write_text(
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('fake-agent 1.0')\n",
            encoding="utf-8",
        )
        (self.root / "memory" / "company" / "tool_adapters.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_tool": "fake",
                    "review_tool": "fake",
                    "default_timeout_seconds": 30,
                    "role_defaults": {"unity_gameplay": "fake"},
                    "tools": {
                        "fake": {
                            "enabled": True,
                            "description": "Fake adapter",
                            "argv": [sys.executable, str(fake), "{prompt}"],
                            "timeout_seconds": 30,
                            "version_command": [sys.executable, str(fake), "--version"],
                        },
                        "disabled_tool": {
                            "enabled": False,
                            "description": "Disabled adapter",
                            "argv": [sys.executable, str(fake), "{prompt}"],
                            "disabled_reason": "not used",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        state = collect_agent_adapter_state(self.root)

        fake_state = state["tools"]["fake"]
        self.assertEqual(fake_state["status"], "available")
        self.assertEqual(fake_state["version"], "fake-agent 1.0")
        self.assertEqual(Path(fake_state["resolvedPath"]).resolve(), Path(sys.executable).resolve())
        self.assertEqual(fake_state["defaultRoles"], ["unity_gameplay"])
        self.assertEqual(state["tools"]["disabled_tool"]["status"], "disabled")
        self.assertGreaterEqual(state["summary"]["available"], 1)

    def test_external_adapter_output_is_decoded_as_utf8(self) -> None:
        completed = Mock(
            returncode=0,
            stdout="research complete ✓\n",
            stderr="",
        )

        with (
            patch.object(
                agent_runner_module.shutil,
                "which",
                return_value=r"C:\Tools\fake-agent.cmd",
            ),
            patch.object(
                agent_runner_module.subprocess,
                "run",
                return_value=completed,
            ) as run,
        ):
            result = agent_runner_module._execute(
                ["fake-agent"],
                self.root,
                None,
                30,
                False,
            )

        self.assertEqual(result["status"], "ok")
        self.assertIn("✓", result["stdout"])
        self.assertEqual(run.call_args.args[0][0], r"C:\Tools\fake-agent.cmd")
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(run.call_args.kwargs["errors"], "replace")

    def test_external_adapter_permission_denial_is_failed(self) -> None:
        completed = Mock(
            returncode=0,
            stdout="",
            stderr=(
                "jetski: no output produced because write_file permission "
                "was auto-denied."
            ),
        )

        with (
            patch.object(
                agent_runner_module.shutil,
                "which",
                return_value="fake-agent",
            ),
            patch.object(
                agent_runner_module.subprocess,
                "run",
                return_value=completed,
            ),
        ):
            result = agent_runner_module._execute(
                ["fake-agent"],
                self.root,
                None,
                30,
                False,
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["exit"], 0)

    def test_changes_required_review_blocks_task(self) -> None:
        start_session(self.root, "review verdict")
        plan_task(self.root, "review source licensing")
        assign_task(self.root, "task-0001", "unity_gameplay")
        task = load_task_board(self.root)["tasks"][0]
        report = self.root / "runs" / "review" / "agent_run.md"
        report.parent.mkdir(parents=True)
        report.write_text("# Agent Run\n", encoding="utf-8")

        agent_runner_module._update_task_after_run(
            self.root,
            task,
            "codex",
            "review",
            {
                "status": "ok",
                "exit": 0,
                "stdout": "Verdict: CHANGES REQUIRED\nAsset gate: blocked.",
                "stderr": "",
            },
            report,
        )

        updated = load_task_board(self.root)["tasks"][0]
        self.assertEqual(updated["status"], "blocked")
        self.assertEqual(updated["review_status"], "changes_required")
        self.assertEqual(updated["reviewer"], "critic_reviewer")
        self.assertIn("Critic review requested changes", updated["blocked_reason"])

    def test_review_outcome_requires_explicit_verdict(self) -> None:
        self.assertEqual(
            agent_runner_module._review_outcome("Verdict: APPROVED"),
            "approved",
        )
        self.assertEqual(
            agent_runner_module._review_outcome("Review completed without a verdict."),
            "unresolved",
        )
        self.assertEqual(
            agent_runner_module._review_outcome(
                "The reviewer must choose APPROVED or CHANGES REQUIRED."
            ),
            "unresolved",
        )

    def test_full_approval_stops_on_changes_required_review(self) -> None:
        start_session(self.root, "review auto-advance guard")
        plan_task(self.root, "review source licensing")
        assign_task(self.root, "task-0001", "unity_gameplay")
        task = load_task_board(self.root)["tasks"][0]
        report = self.root / "runs" / "review" / "agent_run.md"
        report.parent.mkdir(parents=True)
        report.write_text("# Agent Run\n", encoding="utf-8")
        agent_runner_module._update_task_after_run(
            self.root,
            task,
            "codex",
            "review",
            {
                "status": "ok",
                "exit": 0,
                "stdout": "Verdict: CHANGES REQUIRED",
                "stderr": "",
            },
            report,
        )

        with (
            patch.object(
                agent_runner_module,
                "run_agent_task",
                return_value=report,
            ),
            patch.object(agent_runner_module, "advance_task") as advance_task,
        ):
            actual_report, advance = run_agent_task_full_approval(
                self.root,
                "task-0001",
                mode="review",
            )

        self.assertEqual(actual_report, report)
        self.assertIsNone(advance)
        advance_task.assert_not_called()


if __name__ == "__main__":
    unittest.main()
