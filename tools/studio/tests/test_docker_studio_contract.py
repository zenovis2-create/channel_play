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


if __name__ == "__main__":
    unittest.main()
