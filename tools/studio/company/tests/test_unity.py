from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest.mock import Mock, patch

from tools.studio.company import unity as unity_module
from tools.studio.company.capture import PNG_SIGNATURE
from tools.studio.company.errors import CompanyError
from tools.studio.company.unity import (
    resolve_unity_editor,
    unity_build,
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

    def test_linux_build_support_path_matches_editor_layouts(self) -> None:
        windows = PureWindowsPath(
            r"C:\Unity\Hub\Editor\6000.0.76f1\Editor\Unity.exe"
        )
        linux = PurePosixPath(
            "/opt/unity/Hub/Editor/6000.0.76f1/Editor/Unity"
        )
        mac = PurePosixPath(
            "/Applications/Unity/Hub/Editor/6000.0.76f1/"
            "Unity.app/Contents/MacOS/Unity"
        )

        self.assertEqual(
            unity_module._linux_build_support_path(windows),
            windows.parent
            / "Data"
            / "PlaybackEngines"
            / "LinuxStandaloneSupport",
        )
        self.assertEqual(
            unity_module._linux_build_support_path(linux),
            linux.parent
            / "Data"
            / "PlaybackEngines"
            / "LinuxStandaloneSupport",
        )
        self.assertEqual(
            unity_module._linux_build_support_path(mac),
            PurePosixPath(
                "/Applications/Unity/Hub/Editor/6000.0.76f1/"
                "Unity.app/Contents/PlaybackEngines/"
                "LinuxStandaloneSupport"
            ),
        )

    def test_linux_build_missing_editor_fails_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "Unity" / "Editor" / "Unity.exe"
            with patch.object(
                unity_module,
                "_resolve_unity_editor",
                return_value=missing,
            ):
                with self.assertRaisesRegex(
                    CompanyError,
                    "Unity editor not found",
                ):
                    unity_build(root, ["linux-server"])

            self.assertFalse((root / "runs").exists())

    def test_linux_build_missing_module_writes_windows_instructions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unity = (
                root
                / "Unity"
                / "Hub"
                / "Editor"
                / "6000.0.76f1"
                / "Editor"
                / "Unity.exe"
            )
            unity.parent.mkdir(parents=True)
            unity.touch()
            run_batch = Mock()

            with (
                patch.object(
                    unity_module,
                    "_resolve_unity_editor",
                    return_value=unity,
                ),
                patch.object(unity_module.sys, "platform", "win32"),
                patch.object(
                    unity_module,
                    "_run_unity_batch",
                    run_batch,
                ),
            ):
                receipt = unity_build(root, ["linux-server"])

            text = receipt.read_text(encoding="utf-8")
            expected_support = (
                unity.parent
                / "Data"
                / "PlaybackEngines"
                / "LinuxStandaloneSupport"
            )
            self.assertIn("Status: blocked", text)
            self.assertIn("Host platform: Windows", text)
            self.assertIn(f"Unity editor: {unity}", text)
            self.assertIn(
                f"Linux build support checked: {expected_support}",
                text,
            )
            self.assertIn("Linux Build Support (Mono)", text)
            self.assertIn("Dedicated Server Build Support", text)
            self.assertIn(
                "Rerun: python tools/channelctl unity build linux-server",
                text,
            )
            self.assertNotIn("this Mac", text)
            self.assertNotIn("then implement", text)
            run_batch.assert_not_called()

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
