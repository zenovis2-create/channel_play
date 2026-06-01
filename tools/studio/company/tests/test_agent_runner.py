from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.agent_runner import collect_agent_adapter_state, run_agent_task
from tools.studio.company.planner import assign_task, plan_task
from tools.studio.company.sessions import start_session
from tools.studio.company.state import load_task_board


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
        self.assertEqual(task["agent_runs"][0]["mode"], "run")

    def test_adapter_state_creates_default_config(self) -> None:
        state = collect_agent_adapter_state(self.root)

        self.assertIn("codex", state["tools"])
        self.assertTrue((self.root / "memory" / "company" / "tool_adapters.json").exists())

        config = json.loads((self.root / "memory" / "company" / "tool_adapters.json").read_text(encoding="utf-8"))
        self.assertEqual(config["tools"]["claude"]["stdin"], "{prompt}")
        agy_argv = config["tools"]["agy"]["argv"]
        self.assertLess(agy_argv.index("--print-timeout"), agy_argv.index("--print"))


if __name__ == "__main__":
    unittest.main()
