from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.studio.company.agent_runner import DEFAULT_ADAPTERS


class AgentTeamStructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[4]
        self.registry = json.loads((self.root / "memory" / "company" / "agent_registry.json").read_text(encoding="utf-8"))

    def test_structural_agents_are_registered_with_profiles_and_tools(self) -> None:
        expected = {
            "production_planner": "codex",
            "research_librarian": "notebooklm",
            "coding_specialist": "codex",
            "toolchain_integrator": "codex",
            "operator_broadcast_designer": "hermes",
        }
        agents = {agent["id"]: agent for agent in self.registry["agents"]}

        for agent_id, tool in expected.items():
            with self.subTest(agent_id=agent_id):
                agent = agents[agent_id]
                profile = self.root / agent["profile"]
                self.assertTrue(profile.exists(), agent["profile"])
                self.assertEqual(agent["goal_setting"]["goal_id"], "mvp_traitor_escape_gameshow")
                self.assertEqual(agent["goal_setting"]["tool"], tool)
                self.assertTrue(agent["goal_setting"]["required_outputs"])
                self.assertEqual(DEFAULT_ADAPTERS["role_defaults"][agent_id], tool)

    def test_agent_team_structure_doc_exists(self) -> None:
        text = (self.root / "docs" / "agent_team_structure.md").read_text(encoding="utf-8")

        self.assertIn("production_planner", text)
        self.assertIn("research_librarian", text)
        self.assertIn("coding_specialist", text)
        self.assertIn("toolchain_integrator", text)
        self.assertIn("operator_broadcast_designer", text)


if __name__ == "__main__":
    unittest.main()
