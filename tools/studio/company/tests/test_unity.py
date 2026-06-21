from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.unity import resolve_unity_editor


class UnityPathTests(unittest.TestCase):
    def test_unity_editor_env_override_wins(self) -> None:
        configured = r"C:\Unity\Editor\Unity.exe"
        with patch.dict(os.environ, {"UNITY_EDITOR": configured}):
            self.assertEqual(resolve_unity_editor(), Path(configured))


if __name__ == "__main__":
    unittest.main()
