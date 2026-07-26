"""Blender cleanup template for Channel Play assets."""

from pathlib import Path
import sys

import bpy

ASSET_ID = 'truth_pen'
GATE_STATUS = 'blocked_by_gate_a'
REPO_ROOT = Path(__file__).resolve().parents[3]

def require_production_gate():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tools.studio.company.asset_gate import require_asset_gate_b
    require_asset_gate_b(REPO_ROOT, ASSET_ID)

def main():
    require_production_gate()
    # Load generated GLB/FBX manually or extend this template with an import path.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.wm.save_as_mainfile(filepath=f'asset_pipeline/blender_work/{ASSET_ID}/{ASSET_ID}.blend')

if __name__ == '__main__':
    main()
