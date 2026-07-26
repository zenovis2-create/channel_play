from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.brief import build_brief


class CurrentBriefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (memory / "state.json").write_text(
            json.dumps(
                {
                    "project": "channel_play",
                    "active_session": None,
                    "gdx1": {
                        "network": "online_via_tailscale",
                        "ssh": "auth_blocked",
                    },
                }
            ),
            encoding="utf-8",
        )
        (memory / "agent_registry.json").write_text(
            json.dumps({"agents": []}),
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(
            json.dumps({"tasks": []}),
            encoding="utf-8",
        )
        (memory / "locks.json").write_text(
            json.dumps({"locks": []}),
            encoding="utf-8",
        )
        (memory / "current_context.md").write_text(
            "# Current Context\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_brief_is_portable_and_recommends_an_available_command(self) -> None:
        with (
            patch(
                "tools.studio.company.brief.git_head",
                return_value="abc1234",
            ),
            patch(
                "tools.studio.company.brief.git_short_status",
                return_value=[],
            ),
            patch(
                "tools.studio.company.brief.ensure_brain_files",
                return_value={"projectBrain": "# Project Brain", "standards": []},
            ),
        ):
            text = build_brief(self.root)

        self.assertIn("Repo: channel_play", text)
        self.assertNotIn(str(self.root), text)
        self.assertIn(
            "`tools/channelctl company plan <request>`",
            text,
        )
        self.assertNotIn("Implement `company session start/end`", text)


if __name__ == "__main__":
    unittest.main()
