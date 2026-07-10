import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.validate_khufu_v5_performance import validate


class KhufuV5PerformanceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.budget = self.root / "budget.json"
        self.receipt = self.root / "performance.md"
        self.raw = self.root / "profile.raw"
        self.log = self.root / "player.log"
        self.initial = self.root / "initial.png"
        self.operator = self.root / "operator.png"
        self.budget.write_text(
            json.dumps(
                {
                    "target": {"resolution": "1536x1024", "quality": "Ultra"},
                    "limits": {
                        "minimum_samples": 3000,
                        "frame_p95_ms": 9.0,
                        "main_thread_p95_ms": 4.5,
                        "render_thread_p95_ms": 4.5,
                        "gpu_p95_ms": 4.5,
                        "maximum_allocated_mb": 190.0,
                        "maximum_reserved_mb": 340.0,
                        "maximum_managed_mb": 16.0,
                        "maximum_visible_renderers": 820,
                        "maximum_visible_vertices": 25000,
                        "maximum_visible_triangles": 18000,
                        "minimum_profiler_raw_bytes": 32,
                        "maximum_profiler_raw_bytes": 1024,
                        "minimum_screenshot_bytes": 24,
                    },
                }
            ),
            encoding="utf-8",
        )
        self.receipt.write_text(self.valid_receipt(), encoding="utf-8")
        self.raw.write_bytes(b"profile" * 16)
        self.log.write_text("player completed normally\n", encoding="utf-8")
        self.write_png_header(self.initial, b"A")
        self.write_png_header(self.operator, b"B")

    def tearDown(self):
        self.temp.cleanup()

    def args(self):
        return SimpleNamespace(
            budget=self.budget,
            receipt=self.receipt,
            profiler_raw=self.raw,
            player_log=self.log,
            screenshots=[self.initial, self.operator],
        )

    def test_valid_receipt_passes(self):
        passed, failures, _ = validate(self.args())
        self.assertTrue(passed, failures)

    def test_p95_over_budget_fails(self):
        self.receipt.write_text(self.valid_receipt().replace("p95: `8.3 ms`", "p95: `9.1 ms`", 1), encoding="utf-8")
        passed, failures, _ = validate(self.args())
        self.assertFalse(passed)
        self.assertTrue(any("frame_p95_ms" in failure for failure in failures))

    def test_duplicate_screenshots_fail(self):
        self.operator.write_bytes(self.initial.read_bytes())
        passed, failures, _ = validate(self.args())
        self.assertFalse(passed)
        self.assertIn("screenshots are missing or duplicate", failures)

    def test_error_log_fails(self):
        self.log.write_text("Fatal Error: render failure\n", encoding="utf-8")
        passed, failures, _ = validate(self.args())
        self.assertFalse(passed)
        self.assertTrue(any("player log" in failure for failure in failures))

    def test_missing_gpu_metric_fails(self):
        lines = [line for line in self.valid_receipt().splitlines() if not line.startswith("- GPU frame")]
        self.receipt.write_text("\n".join(lines), encoding="utf-8")
        passed, failures, _ = validate(self.args())
        self.assertFalse(passed)
        self.assertTrue(any("GPU frame p95" in failure for failure in failures))

    @staticmethod
    def write_png_header(path: Path, suffix: bytes):
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1536, 1024) + suffix)

    @staticmethod
    def valid_receipt():
        return """# Performance
- Resolution: `1536x1024`, quality `Ultra`
- Samples: `3500`
- Frame time median: `8.0 ms`; p95: `8.3 ms`
- Main thread median: `1.0 ms`; p95: `2.4 ms`
- Render thread median: `1.0 ms`; p95: `2.8 ms`
- GPU frame median: `1.0 ms`; p95: `2.2 ms`
- Maximum total allocated memory: `150.0 MB`
- Maximum total reserved memory: `270.0 MB`
- Maximum managed memory: `3.0 MB`
- Visible renderers: `781`
- Visible mesh vertices: `23710`
- Visible mesh triangles: `16888`

PROFILE_RESULT: recorded
"""


if __name__ == "__main__":
    unittest.main()
