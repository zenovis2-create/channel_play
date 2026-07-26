# Blender Cleanup Work Order

Asset ID: truth_pen
Status: blocked_by_gate_a
Scale: 0.22m total length against the 2m player reference
Origin: grip center; orient the tip along local +Z
Object names: CP_TruthPen_Body, CP_TruthPen_Clip, CP_TruthPen_Nib
Materials: MAT_TruthPen_Body and MAT_TruthPen_Emissive
Geometry: apply transforms, recalculate normals, remove hidden shells
Budget: 3,000 triangles maximum; one 512-1024px material set
Collider proxy: one simplified convex pickup collider
Export: GLB to asset_pipeline/unity_ready/truth_pen/

Do not execute this handoff until Gate B passes.
