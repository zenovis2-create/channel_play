from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.studio.company.worker_fleet import probe_worker_fleet, render_worker_fleet


class WorkerFleetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "memory" / "company").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_probe_records_local_hardware_and_tool_workers_without_sensitive_ids(self) -> None:
        with patch("tools.studio.company.worker_fleet.shutil.which", side_effect=self._which):
            data = probe_worker_fleet(self.root, runner=self._runner_ok)

        workers = {worker["id"]: worker for worker in data["workers"]}
        self.assertEqual(workers["mac_studio"]["status"], "available")
        self.assertEqual(workers["mac_studio"]["hardware"]["chip"], "Apple M2 Ultra")
        self.assertEqual(workers["mac_studio"]["hardware"]["ram_gb"], 64)
        self.assertEqual(workers["gdx1"]["status"], "available")
        self.assertTrue(workers["gdx1"]["enabled"])
        self.assertIn("remote_ai_ops", workers["gdx1"]["capabilities"])
        self.assertIn("x86_linux_runner", workers)
        self.assertFalse(workers["x86_linux_runner"]["enabled"])
        self.assertEqual(workers["local_ollama"]["status"], "available")
        self.assertEqual(workers["hermes"]["status"], "available")
        self.assertEqual(workers["openclaw"]["status"], "available")

        text = json.dumps(data)
        self.assertNotIn("SECRET-SERIAL", text)
        self.assertNotIn("SECRET-UUID", text)
        self.assertTrue((self.root / "memory" / "company" / "worker_fleet.json").exists())

    def test_gdx1_is_disabled_when_ssh_probe_fails(self) -> None:
        with patch("tools.studio.company.worker_fleet.shutil.which", return_value=""):
            data = probe_worker_fleet(self.root, runner=self._runner_gdx_blocked)

        workers = {worker["id"]: worker for worker in data["workers"]}
        self.assertFalse(workers["gdx1"]["enabled"])
        self.assertEqual(workers["gdx1"]["status"], "blocked")
        self.assertEqual(workers["gdx1"]["hardware"]["ssh"], "failed")
        self.assertEqual(workers["local_ollama"]["status"], "missing")

    def test_render_worker_fleet_includes_capabilities_and_recommended_jobs(self) -> None:
        with patch("tools.studio.company.worker_fleet.shutil.which", side_effect=self._which):
            probe_worker_fleet(self.root, runner=self._runner_ok)
            text = render_worker_fleet(self.root)

        self.assertIn("mac_studio", text)
        self.assertIn("unity_editor", text)
        self.assertIn("remote_ai_ops", text)
        self.assertIn("x86_linux_runner", text)

    def _which(self, executable: str) -> str:
        return f"/usr/local/bin/{executable}"

    def _runner_ok(self, command, **kwargs):
        if command[:3] == ["system_profiler", "SPHardwareDataType", "SPDisplaysDataType"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    {
                        "SPHardwareDataType": [
                            {
                                "machine_name": "Mac Studio",
                                "chip_type": "Apple M2 Ultra",
                                "serial_number": "SECRET-SERIAL",
                                "platform_UUID": "SECRET-UUID",
                            }
                        ],
                        "SPDisplaysDataType": [
                            {
                                "sppci_model": "Apple M2 Ultra",
                                "sppci_cores": "60",
                                "spdisplays_mtlgpufamilysupport": "spdisplays_metal4",
                            }
                        ],
                    }
                ),
                stderr="",
            )
        if command[:3] == ["sysctl", "-n", "hw.memsize"]:
            return subprocess.CompletedProcess(command, 0, stdout=str(64 * 1024**3), stderr="")
        if command[:3] == ["sysctl", "-n", "machdep.cpu.brand_string"]:
            return subprocess.CompletedProcess(command, 0, stdout="Apple M2 Ultra", stderr="")
        if command[:1] == ["ssh"]:
            return subprocess.CompletedProcess(command, 0, stdout="gdx1\nLinux x86_64", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout=f"{command[0]} 1.0.0", stderr="")

    def _runner_gdx_blocked(self, command, **kwargs):
        if command[:1] == ["ssh"]:
            return subprocess.CompletedProcess(command, 255, stdout="", stderr="Permission denied")
        return self._runner_ok(command, **kwargs)


if __name__ == "__main__":
    unittest.main()
