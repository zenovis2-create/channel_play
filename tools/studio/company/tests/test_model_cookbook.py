from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.model_cookbook import refresh_model_cookbook, render_model_cookbook


class ModelCookbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (memory / "worker_fleet.json").write_text(json.dumps(self._worker_fleet(gdx_available=True)), encoding="utf-8")
        (memory / "tool_adapters.json").write_text(json.dumps({"tools": {}, "role_defaults": {}}), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_refresh_records_hardware_budget_gdx_probe_and_use_case_statuses(self) -> None:
        with patch("tools.studio.company.model_cookbook.collect_agent_adapter_state", return_value=self._adapters()):
            data = refresh_model_cookbook(self.root)

        self.assertEqual(data["hardware_profile"]["chip"], "Apple M2 Ultra")
        self.assertEqual(data["hardware_profile"]["ram_gb"], 64)
        self.assertEqual(data["hardware_profile"]["backend"], "Metal")
        self.assertEqual(data["hardware_profile"]["gpu_budget_gb"], 48)
        self.assertEqual(data["gdx1_probe"]["status"], "available")
        self.assertEqual(data["summary"]["total"], 9)
        self.assertEqual(data["summary"]["verified"], 8)
        self.assertEqual(data["summary"]["blocked"], 1)
        self.assertEqual({row["use_case"] for row in data["use_cases"]}, {
            "unity_code",
            "game_design",
            "qa_review",
            "asset_prompt",
            "blender_python",
            "audio_design",
            "long_research",
            "gdx_soak",
            "x86_server_soak",
        })
        for row in data["use_cases"]:
            self.assertIn("verification_status", row)
            self.assertIn("verification_status", row["primary"])
            self.assertIn("runtime", row["primary"])
            self.assertIn("model", row["primary"])
        self.assertTrue((self.root / "memory" / "company" / "model_cookbook.json").exists())

    def test_gdx_soak_is_worker_blocked_when_gdx_probe_is_blocked(self) -> None:
        (self.root / "memory" / "company" / "worker_fleet.json").write_text(
            json.dumps(self._worker_fleet(gdx_available=False)),
            encoding="utf-8",
        )

        with patch("tools.studio.company.model_cookbook.collect_agent_adapter_state", return_value=self._adapters()):
            data = refresh_model_cookbook(self.root)

        gdx_soak = next(row for row in data["use_cases"] if row["use_case"] == "gdx_soak")
        self.assertEqual(gdx_soak["verification_status"], "worker_blocked")
        self.assertEqual(gdx_soak["primary"]["worker_status"], "blocked")

    def test_x86_server_soak_is_blocked_until_runner_exists(self) -> None:
        with patch("tools.studio.company.model_cookbook.collect_agent_adapter_state", return_value=self._adapters()):
            data = refresh_model_cookbook(self.root)

        server_soak = next(row for row in data["use_cases"] if row["use_case"] == "x86_server_soak")
        self.assertEqual(server_soak["verification_status"], "worker_blocked")
        self.assertEqual(server_soak["primary"]["worker"], "x86_linux_runner")

    def test_render_model_cookbook_includes_budget_and_gdx(self) -> None:
        with patch("tools.studio.company.model_cookbook.collect_agent_adapter_state", return_value=self._adapters()):
            text = render_model_cookbook(self.root, refresh=True)

        self.assertIn("GPU budget 48GB", text)
        self.assertIn("unity_code", text)
        self.assertIn("gdx_soak", text)
        self.assertIn("x86_server_soak", text)

    def _worker_fleet(self, gdx_available: bool) -> dict:
        return {
            "version": 1,
            "updated_at": "2026-06-03T00:00:00+09:00",
            "workers": [
                {
                    "id": "mac_studio",
                    "label": "Mac Studio M2 Ultra",
                    "enabled": True,
                    "status": "available",
                    "hardware": {
                        "machine": "Mac Studio",
                        "chip": "Apple M2 Ultra",
                        "ram_gb": 64,
                        "gpu": "Apple M2 Ultra",
                        "gpu_cores": "60",
                        "backend": "Metal",
                    },
                    "last_probe": {"summary": "Mac Studio / Apple M2 Ultra / 64GB RAM"},
                    "capabilities": [],
                    "recommended_jobs": [],
                },
                {
                    "id": "gdx1",
                    "label": "ASUS GX10 gdx1",
                    "enabled": gdx_available,
                    "status": "available" if gdx_available else "blocked",
                    "hardware": {"host": "gdx1", "remote": "gdx1\nLinux aarch64", "ssh": "ok" if gdx_available else "failed"},
                    "last_probe": {"summary": "SSH ok" if gdx_available else "SSH blocked"},
                    "capabilities": [],
                    "recommended_jobs": [],
                },
                {
                    "id": "local_ollama",
                    "label": "Local Ollama",
                    "enabled": True,
                    "status": "available",
                    "hardware": {"version": "ollama version is 0.22.1"},
                    "last_probe": {"summary": "ollama version is 0.22.1"},
                    "capabilities": [],
                    "recommended_jobs": [],
                },
            ],
        }

    def _adapters(self) -> dict:
        tools = {}
        for name in ("codex", "agy", "hermes", "openclaw"):
            tools[name] = {
                "status": "available",
                "available": True,
                "version": f"{name} 1.0.0",
                "lastCheck": "2026-06-03T00:00:00+09:00",
            }
        return {"tools": tools}


if __name__ == "__main__":
    unittest.main()
