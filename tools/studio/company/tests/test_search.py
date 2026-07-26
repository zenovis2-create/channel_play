from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.search import rebuild_search_index, search_sessions


class SessionSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        company = self.root / "memory" / "company"
        (company / "jobs").mkdir(parents=True)
        (self.root / "memory" / "sessions" / "session-a").mkdir(parents=True)
        (self.root / "runs" / "agent-codex-task-0020").mkdir(parents=True)
        (self.root / "reviews" / "captures").mkdir(parents=True)
        (self.root / "docs").mkdir()
        (company / "task_board.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "task-0020",
                            "assigned_agent": "unity_gameplay",
                            "request": "Unity compile check for player points",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (company / "jobs" / "jobs.json").write_text(
            json.dumps({"jobs": [{"id": "job-7777", "taskId": "task-0020", "status": "succeeded"}]}),
            encoding="utf-8",
        )
        (self.root / "memory" / "sessions" / "session-a" / "summary.md").write_text(
            "# Session\nObserved error in Unity compile log for task-0020.\n",
            encoding="utf-8",
        )
        (self.root / "runs" / "agent-codex-task-0020" / "agent_run.md").write_text(
            "# Agent Run\nunity_gameplay produced file path Assets/_Project/Scripts/Gameplay/Player.cs\n",
            encoding="utf-8",
        )
        (self.root / "reviews" / "captures" / "screen-task-0020.png").write_bytes(b"\x89PNG\r\n")
        (self.root / "docs" / "search-note.md").write_text(
            "# Search Note\nUnity compile evidence and screenshot review path.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_rebuild_and_search_acceptance_terms(self) -> None:
        index = rebuild_search_index(self.root)
        self.assertGreaterEqual(index["documentCount"], 6)

        for query in ("task-0020", "unity_gameplay", "Assets/_Project/Scripts/Gameplay/Player.cs", "screenshot", "error", "Unity compile"):
            with self.subTest(query=query):
                result = search_sessions(self.root, query)
                self.assertGreater(result["count"], 0)
                self.assertIn("sourceType", result["results"][0])
                self.assertIn("preview", result["results"][0])

    def test_screenshot_result_has_screenshot_source_type(self) -> None:
        result = search_sessions(self.root, "screen task 0020", rebuild=True)

        source_types = {row["sourceType"] for row in result["results"]}
        self.assertIn("screenshot", source_types)


if __name__ == "__main__":
    unittest.main()
