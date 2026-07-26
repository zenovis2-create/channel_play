"""Blender cleanup template for Channel Play assets."""

import bpy

ASSET_ID = 'truth_pen'

def main():
    # Load generated GLB/FBX manually or extend this template with an import path.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.wm.save_as_mainfile(filepath=f'asset_pipeline/blender_work/{ASSET_ID}/{ASSET_ID}.blend')

if __name__ == '__main__':
    main()
