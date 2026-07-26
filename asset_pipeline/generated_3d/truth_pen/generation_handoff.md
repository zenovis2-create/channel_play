# 2D to 3D Generation Handoff

Asset ID: truth_pen
Status: blocked_by_gate_a
Tool: Pixel3D or equivalent image-to-3D service
Output: GLB preferred, FBX accepted

## Production Requirements

- Preserve the body, clip, and emissive nib as separate named parts.
- Target 3,000 triangles or fewer and one 512-1024px material set.
- Use a 0.22m real-world length with the long axis aligned consistently.
- Exclude text, logos, watermarks, hidden interior shells, and loose fragments.

## Quality Gate

- Gate A must authorize source creation/download.
- Gate B must bind the exact source hash and one approved 3D provider before
  generation, Blender cleanup, or Unity import.
- Shape readable from gameplay camera
- Source license and generation-provider terms recorded
- Clean manifold silhouette with no severe texture projection artifacts
- Low-poly enough for the MVP scene and suitable for Blender cleanup
