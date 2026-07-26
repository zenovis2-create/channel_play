from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company import unity as unity_module
from tools.studio.company.unity import resolve_unity_editor


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


if __name__ == "__main__":
    unittest.main()
