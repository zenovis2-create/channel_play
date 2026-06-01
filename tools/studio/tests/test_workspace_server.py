from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.workspace_server import build_command, collect_workspace_state, read_workspace_file
from tools.studio.company.errors import CompanyError


class WorkspaceServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        (self.root / "tools").mkdir()
        (self.root / "tools" / "channelctl").write_text("#!/bin/sh\n", encoding="utf-8")
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

    def test_build_command_rejects_unknown(self) -> None:
        with self.assertRaises(CompanyError):
            build_command(self.root, "shell.anything", {})

    def test_read_workspace_file_rejects_escape(self) -> None:
        with self.assertRaises(CompanyError):
            read_workspace_file(self.root, "../secret")


if __name__ == "__main__":
    unittest.main()
