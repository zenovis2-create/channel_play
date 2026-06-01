from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.errors import CompanyError
from tools.studio.company.locks import lock_path
from tools.studio.company.planner import assign_task, plan_task
from tools.studio.company.sessions import end_session, start_session


class CompanyCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "channel_play_agent_company_plan.md").write_text("# plan\n", encoding="utf-8")
        (memory / "state.json").write_text(
            json.dumps({"project": "channel_play", "active_session": None, "current_orchestrator_task": None}),
            encoding="utf-8",
        )
        (memory / "agent_registry.json").write_text(
            json.dumps({"agents": [{"id": "unity_gameplay", "profile": "agents/roles/unity_gameplay.agent.md"}]}),
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        (memory / "locks.json").write_text(json.dumps({"locks": []}), encoding="utf-8")
        (memory / "current_context.md").write_text("# context\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_session_prevents_double_start(self) -> None:
        start_session(self.root, "first")
        with self.assertRaises(CompanyError):
            start_session(self.root, "second")
        end_session(self.root)

    def test_assign_rejects_unknown_agent(self) -> None:
        start_session(self.root, "assign")
        plan_task(self.root, "fix player movement")
        with self.assertRaises(CompanyError):
            assign_task(self.root, "task-0001", "unknown_agent")

    def test_lock_conflict_detects_parent_child(self) -> None:
        lock_path(self.root, "Assets/_Project/Scripts", "unity_gameplay", "task-0001")
        with self.assertRaises(CompanyError):
            lock_path(self.root, "Assets/_Project/Scripts/Gameplay", "unity_gameplay", "task-0002")


if __name__ == "__main__":
    unittest.main()
