from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company import unity as unity_module
from tools.studio.company.capture import PNG_SIGNATURE
from tools.studio.company.unity import (
    resolve_unity_editor,
    unity_feedback_capture,
)


class UnityPathTests(unittest.TestCase):
    def test_unity_editor_env_override_wins(self) -> None:
        configured = r"C:\Unity\Editor\Unity.exe"
        with patch.dict(os.environ, {"UNITY_EDITOR": configured}):
            self.assertEqual(resolve_unity_editor(), Path(configured))

    def test_windows_hub_path_uses_project_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version = "6000.0.76f1"
            version_file = root / "ProjectSettings" / "ProjectVersion.txt"
            version_file.parent.mkdir(parents=True)
            version_file.write_text(
                f"m_EditorVersion: {version}\n",
                encoding="utf-8",
            )
            fake_home = root / "home"
            unity = (
                fake_home
                / "Unity"
                / "Hub"
                / "Editor"
                / version
                / "Editor"
                / "Unity.exe"
            )
            unity.parent.mkdir(parents=True)
            unity.touch()

            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(unity_module.sys, "platform", "win32"),
                patch.object(unity_module.Path, "home", return_value=fake_home),
            ):
                self.assertEqual(resolve_unity_editor(root), unity)

    def test_feedback_capture_requires_unity_marker_and_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unity = root / "Unity.exe"
            unity.touch()

            def run_capture(
                project_root,
                editor,
                editor_log,
                *,
                timeout,
                execute_method="",
                env=None,
            ):
                self.assertEqual(project_root, root)
                self.assertEqual(editor, unity)
                self.assertEqual(
                    execute_method,
                    "ChannelPlayProductionValidator.CaptureFeedbackFrame",
                )
                capture = Path(env["CHANNEL_PLAY_FEEDBACK_CAPTURE_PATH"])
                capture.write_bytes(PNG_SIGNATURE + b"game")
                editor_log.write_text(
                    "CHANNEL_PLAY_FEEDBACK_CAPTURE "
                    "result=passed camera=\"Camera\"\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess([], 0, "", "")

            with (
                patch.object(
                    unity_module,
                    "_resolve_unity_editor",
                    return_value=unity,
                ),
                patch.object(
                    unity_module,
                    "_run_unity_batch",
                    side_effect=run_capture,
                ),
            ):
                receipt, capture = unity_feedback_capture(root)

            self.assertTrue(receipt.is_file())
            self.assertTrue(capture.is_file())
            self.assertIn(
                "Feedback capture: passed",
                receipt.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
