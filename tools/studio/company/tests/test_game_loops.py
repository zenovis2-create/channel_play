from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.studio.company.capture import PNG_SIGNATURE
from tools.studio.company.errors import CompanyError
from tools.studio.company.game_loops import game_feedback_loop


class GameFeedbackLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        self.playtest = (
            self.root / "runs" / "unity-playtest-test" / "unity_playtest.md"
        )
        self.playtest.parent.mkdir(parents=True)
        self.playtest.write_text(
            "Exit code: 0\n"
            "Compile errors: 0\n"
            "Playtest smoke: passed\n",
            encoding="utf-8",
        )
        self.capture_receipt = (
            self.root
            / "runs"
            / "unity-feedback-capture-test"
            / "unity_feedback_capture.md"
        )
        self.capture_receipt.parent.mkdir(parents=True)
        self.capture_receipt.write_text(
            "Feedback capture: passed\n",
            encoding="utf-8",
        )
        self.capture = (
            self.root / "reviews" / "captures" / "game-test.png"
        )
        self.capture.parent.mkdir(parents=True)
        self.capture.write_bytes(PNG_SIGNATURE + b"game")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_loop_links_unity_render_to_feedback(self) -> None:
        with (
            patch(
                "tools.studio.company.game_loops.unity_playtest",
                return_value=self.playtest,
            ),
            patch(
                "tools.studio.company.game_loops.unity_feedback_capture",
                return_value=(self.capture_receipt, self.capture),
            ),
        ):
            receipt = game_feedback_loop(self.root, [])

        text = receipt.read_text(encoding="utf-8")
        notes = list((self.root / "reviews").glob("20*/feedback-*/feedback.md"))
        self.assertEqual(len(notes), 1)
        self.assertIn("Status: ready_for_review", text)
        self.assertIn("Game capture:", text)
        self.assertIn("Capture receipt:", text)
        self.assertIn(
            "Screenshot: reviews/captures/game-test.png",
            notes[0].read_text(encoding="utf-8"),
        )

    def test_loop_stops_before_capture_when_playtest_fails(self) -> None:
        self.playtest.write_text(
            "Exit code: 1\n"
            "Compile errors: 0\n"
            "Playtest smoke: failed\n",
            encoding="utf-8",
        )
        capture = Mock()

        with (
            patch(
                "tools.studio.company.game_loops.unity_playtest",
                return_value=self.playtest,
            ),
            patch(
                "tools.studio.company.game_loops.unity_feedback_capture",
                capture,
            ),
        ):
            with self.assertRaisesRegex(CompanyError, "playtest smoke failed"):
                game_feedback_loop(self.root, [])

        capture.assert_not_called()
        receipts = list(
            (self.root / "runs").glob(
                "game-feedback-loop-*/game_feedback_loop.md"
            )
        )
        self.assertEqual(receipts, [])


if __name__ == "__main__":
    unittest.main()
