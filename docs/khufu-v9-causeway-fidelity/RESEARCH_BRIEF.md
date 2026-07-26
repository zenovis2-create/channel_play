# Research Brief

## Source-Grounded Vocabulary

- Retain the V8 research boundary: east-side causeway approach, basalt paving, limestone structure,
  red-granite rhythm, and painted/relief fragments.
- Treat roof form, portal spacing, intact wall height, and decorative distribution as game-art interpretation.

## Unity 6000.0 Guidance

- `Mesh.CombineMeshes` can reduce renderer overhead, but larger combined meshes trade away fine-grained culling.
- Static batching is appropriate for immobile geometry but must be measured for memory and draw-call impact.
- LODGroup is deferred until more than one corridor/district uses the modular V9 kit.
- Detailed MeshColliders are unnecessary here; simple BoxCollider proxies are cheaper and easier to pair exactly.
- Frustum and optional occlusion culling supplement, rather than replace, geometry and batching budgets.
- CPU, GPU, Rendering, Physics, and Memory profiler evidence must be captured on the target Windows player.
- `CharacterController.Move` is collision-constrained, so commanded-versus-observed position is meaningful only
  when a separate perturbation proves that the error threshold can fail.
- `BuildReport.GetFiles()` supplies the authoritative player output inventory; the V9 receipt and bindings hash it.
- `-nographics` does not initialize a graphics device and therefore is not used for editor camera evidence.

## Decision

Build one modular, combined visual kit for the approach corridor and pair only its structural pieces with simple
V9-owned BoxColliders. Preserve inherited V5 floor colliders and defer full-map LOD/occlusion until the pattern is
proven by traversal, mutation, and performance evidence.

## Unity Sources

- [Mesh.CombineMeshes](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh.CombineMeshes.html)
- [Static batching](https://docs.unity3d.com/6000.0/Documentation/Manual/static-batching-enable.html)
- [LOD Group](https://docs.unity3d.com/6000.0/Documentation/Manual/class-LODGroup.html)
- [Mesh Collider](https://docs.unity3d.com/6000.0/Documentation/Manual/class-MeshCollider.html)
- [Occlusion culling](https://docs.unity3d.com/6000.0/Documentation/Manual/OcclusionCulling.html)
- [Profiler command-line arguments](https://docs.unity3d.com/6000.0/Documentation/Manual/profiler-command-line-arguments.html)
- [CharacterController.Move](https://docs.unity3d.com/ja/current/ScriptReference/CharacterController.Move.html)
- [PhysicsScene.OverlapBox](https://docs.unity3d.com/kr/6000.0/ScriptReference/PhysicsScene.OverlapBox.html)
- [BuildReport.GetFiles](https://docs.unity3d.com/kr/2022.1/ScriptReference/Build.Reporting.BuildReport.GetFiles.html)
- [Editor command-line arguments](https://docs.unity.cn/Manual/EditorCommandLineArguments.html)
