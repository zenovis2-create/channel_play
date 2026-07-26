from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.assets import asset_prepare


class AssetPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_asset_prepare_writes_full_game_asset_packet(self) -> None:
        receipt = asset_prepare(self.root, "prop_school_desk")

        self.assertTrue(receipt.exists())
        self.assertTrue((self.root / "asset_pipeline/incoming_2d/prop_school_desk/source_drop.md").exists())
        self.assertTrue((self.root / "asset_pipeline/generated_3d/prop_school_desk/generation_handoff.md").exists())
        self.assertTrue((self.root / "asset_pipeline/blender_work/prop_school_desk/blender_batch_template.py").exists())
        self.assertTrue((self.root / "asset_pipeline/unity_ready/prop_school_desk/unity_import_manifest.md").exists())

        index = json.loads((self.root / "asset_pipeline/index.json").read_text(encoding="utf-8"))
        asset = index["assets"][0]
        self.assertEqual(asset["id"], "prop_school_desk")
        self.assertEqual(asset["status"], "generated")
        self.assertEqual(asset["pipeline_receipt"], "runs/asset-pipeline-prop_school_desk/asset_pipeline_receipt.md")


if __name__ == "__main__":
    unittest.main()
