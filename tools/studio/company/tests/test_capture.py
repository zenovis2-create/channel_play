from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company import capture as capture_module
from tools.studio.company.capture import PNG_SIGNATURE, capture_screen
from tools.studio.company.errors import CompanyError


class CaptureTests(unittest.TestCase):
    def test_capture_screen_returns_real_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def write_png(*args, **kwargs):
                Path(kwargs["env"]["CHANNEL_PLAY_CAPTURE_PATH"]).write_bytes(
                    PNG_SIGNATURE + b"test"
                )
                return subprocess.CompletedProcess(args[0], 0, "", "")

            with (
                patch.object(capture_module, "_capture_command", return_value=["capture"]),
                patch.object(capture_module.subprocess, "run", side_effect=write_png),
            ):
                path = capture_screen(root)

            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes()[:8], PNG_SIGNATURE)

    def test_capture_failure_does_not_leave_fake_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.CompletedProcess(
                ["capture"],
                1,
                "",
                "desktop unavailable",
            )

            with (
                patch.object(capture_module, "_capture_command", return_value=["capture"]),
                patch.object(capture_module.subprocess, "run", return_value=result),
            ):
                with self.assertRaisesRegex(CompanyError, "desktop unavailable"):
                    capture_screen(root)

            self.assertEqual(list((root / "reviews" / "captures").glob("*.png")), [])


if __name__ == "__main__":
    unittest.main()
