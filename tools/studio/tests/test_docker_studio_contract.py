from __future__ import annotations

import unittest
from pathlib import Path


class DockerStudioContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[3]
        self.compose = (self.root / "docker-compose.studio.yml").read_text(
            encoding="utf-8"
        )
        self.app = (self.root / "tools" / "studio" / "app" / "app.js").read_text(
            encoding="utf-8"
        )
        self.index = (
            self.root / "tools" / "studio" / "app" / "index.html"
        ).read_text(encoding="utf-8")
        self.style = (
            self.root / "tools" / "studio" / "app" / "style.css"
        ).read_text(encoding="utf-8")

    def test_admin_console_is_published_on_host_loopback_only(self) -> None:
        self.assertIn(
            '"127.0.0.1:${CHANNEL_PLAY_STUDIO_PORT:-8776}:8776"',
            self.compose,
        )

    def test_container_has_no_privileged_or_docker_socket_access(self) -> None:
        self.assertNotIn("privileged:", self.compose)
        self.assertNotIn("/var/run/docker.sock", self.compose)

    def test_game_next_action_can_open_guidance_artifact(self) -> None:
        self.assertIn("next.artifact", self.app)
        self.assertIn(
            'data-game-artifact-path="${esc(next.artifact)}"',
            self.app,
        )
        self.assertIn(
            'next.actionLabel || "안내서 열기"',
            self.app,
        )

    def test_procurement_checklist_is_read_only_and_accessible(self) -> None:
        self.assertIn('id="gameProcurementChecklist"', self.index)
        self.assertIn('aria-label="작가 조달 미결정 항목"', self.index)
        self.assertNotIn('aria-live="polite"', self.index)
        start = self.app.index(
            '$("#gameProcurementChecklist").innerHTML'
        )
        end = self.app.index(
            '$("#gameProductionChecks").innerHTML',
            start,
        )
        checklist = self.app[start:end]

        self.assertIn("procurement.errors", self.app)
        self.assertIn(
            "procurement.passed\n    && Boolean(procurement.receipt)",
            self.app,
        )
        self.assertIn("procurementContactReady", checklist)
        self.assertIn("최신 PASS 영수증 전에는 작가 연락 금지", self.app)
        self.assertIn("의사결정 통과 · 최신 PASS 영수증 대기", self.app)
        self.assertIn("procurementErrors.map", checklist)
        self.assertIn("${esc(error)}", checklist)
        self.assertIn("game-procurement-item", checklist)
        self.assertIn('role="listitem"', checklist)
        self.assertIn(
            'class="game-procurement-empty" role="listitem"',
            checklist,
        )
        self.assertIn("data-game-artifact-path", checklist)
        self.assertNotIn("data-command", checklist)
        self.assertIn(".game-procurement-checklist", self.style)


if __name__ == "__main__":
    unittest.main()
