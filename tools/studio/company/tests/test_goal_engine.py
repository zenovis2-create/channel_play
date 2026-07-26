from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.goal_engine import goal_state, run_goal, set_goal


class GoalEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "channel_play_agent_company_plan.md").write_text("# plan\n", encoding="utf-8")
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (memory / "state.json").write_text(
            json.dumps({"project": "channel_play", "active_session": None, "current_orchestrator_task": None}),
            encoding="utf-8",
        )
        (memory / "agent_registry.json").write_text(
            json.dumps(
                {
                    "agents": [
                        {"id": "production_planner", "profile": "agents/roles/production_planner.agent.md"},
                        {"id": "research_librarian", "profile": "agents/roles/research_librarian.agent.md"},
                        {"id": "coding_specialist", "profile": "agents/roles/coding_specialist.agent.md"},
                        {"id": "toolchain_integrator", "profile": "agents/roles/toolchain_integrator.agent.md"},
                        {
                            "id": "operator_broadcast_designer",
                            "profile": "agents/roles/operator_broadcast_designer.agent.md",
                        },
                        {"id": "unity_gameplay", "profile": "agents/roles/unity_gameplay.agent.md"},
                        {"id": "critic_reviewer", "profile": "agents/roles/critic_reviewer.agent.md"},
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

    def test_set_goal_creates_active_goal_and_receipt(self) -> None:
        receipt = set_goal(self.root, "Unity MVP 목표 구현", max_iterations=7)

        state = goal_state(self.root)
        goal = state["activeGoal"]

        self.assertTrue(receipt.exists())
        self.assertEqual(goal["objective"], "Unity MVP 목표 구현")
        self.assertEqual(goal["status"], "active")
        self.assertEqual(goal["max_iterations"], 7)
        self.assertEqual(goal["lastReceipt"], receipt.relative_to(self.root).as_posix())

    def test_run_goal_dry_run_completes_seeded_tasks(self) -> None:
        set_goal(self.root, "Unity에서 플레이어 이동과 포인트 UI를 구현하고 검증", max_iterations=12)

        receipt = run_goal(self.root, dry_run=True, max_iterations=12)
        state = goal_state(self.root)
        goal = state["activeGoal"]

        self.assertTrue(receipt.exists())
        self.assertEqual(goal["status"], "complete")
        self.assertIn("완벽하게 됐습니다", goal["answer"])
        self.assertEqual(goal["completion"]["passed"], goal["completion"]["total"])
        self.assertGreaterEqual(goal["completion"]["total"], 2)
        self.assertEqual({task["stage"] for task in goal["tasks"]}, {"planning", "research", "implementation"})

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        self.assertTrue(all(task["status"] == "closed" for task in board["tasks"]))
        self.assertTrue(all(task["verification_status"] == "passed" for task in board["tasks"]))
        self.assertTrue(all(task["orchestrated_by"] == "chief_orchestrator" for task in board["tasks"]))

    def test_goal_seeds_specialist_tasks_from_objective(self) -> None:
        set_goal(
            self.root,
            "Codex SDK Docker host-runner와 OBS 방송용 운영자 화면 코딩 검증",
            max_iterations=1,
        )

        run_goal(self.root, dry_run=True, max_iterations=1)
        goal = goal_state(self.root)["activeGoal"]

        self.assertEqual(goal["status"], "active")
        self.assertEqual(
            {task["stage"] for task in goal["tasks"]},
            {"planning", "research", "toolchain", "coding", "broadcast", "implementation"},
        )


if __name__ == "__main__":
    unittest.main()
