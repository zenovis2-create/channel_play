from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.feedback import feedback_process


class FeedbackRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (memory / "state.json").write_text(json.dumps({"active_session": None}), encoding="utf-8")
        (memory / "agent_registry.json").write_text(
            json.dumps(
                {
                    "agents": [
                        {"id": "qa_playtest"},
                        {"id": "unity_gameplay"},
                        {"id": "asset_factory"},
                        {"id": "multiplayer_server"},
                        {"id": "performance_build"},
                        {"id": "critic_reviewer"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        (memory / "locks.json").write_text(json.dumps({"locks": []}), encoding="utf-8")
        (memory / "current_context.md").write_text("context\n", encoding="utf-8")
        (memory / "current_brief.md").write_text("brief\n", encoding="utf-8")
        (memory / "decision_log.md").write_text("decisions\n", encoding="utf-8")
        feedback_dir = self.root / "reviews" / "2026-06-03" / "feedback-0001"
        feedback_dir.mkdir(parents=True)
        self.feedback = feedback_dir / "feedback.md"
        self.feedback.write_text(
            "\n".join(
                [
                    "# Feedback 0001",
                    "",
                    "Status: open",
                    "",
                    "## Observation",
                    "",
                    "포인트 HUD 텍스트가 너무 작다.",
                    "",
                    "## Requested Change",
                    "",
                    "점수 UI를 더 크게 만들고 화면 오른쪽 위에 고정해줘.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.baseline = self.root / "runs" / "unity-check-fake" / "unity_check.md"
        self.baseline.parent.mkdir(parents=True)
        self.baseline.write_text("Compile errors: 0\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_feedback_process_routes_tasks_without_closing_them(self) -> None:
        with patch("tools.studio.company.feedback.unity_check", return_value=self.baseline):
            feedback_process(self.root, self.feedback.relative_to(self.root).as_posix())

        text = self.feedback.read_text(encoding="utf-8")
        board = json.loads((self.root / "memory/company/task_board.json").read_text(encoding="utf-8"))
        tasks = board["tasks"]

        self.assertIn("Status: routed", text)
        self.assertIn("routing_receipt.md", text)
        self.assertEqual(len(tasks), 3)
        self.assertIn("unity_gameplay", {task["assigned_agent"] for task in tasks})
        self.assertTrue(all(task["status"] == "assigned" for task in tasks))
        self.assertFalse(any(task.get("closed_at") for task in tasks))
        self.assertTrue((self.feedback.parent / "routing_receipt.md").exists())


if __name__ == "__main__":
    unittest.main()
