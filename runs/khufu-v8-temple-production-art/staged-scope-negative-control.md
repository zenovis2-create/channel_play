# Khufu V8 Aggregate Validation

- Verdict: **failed**
- Fable required: `True`
- Staged scope checked: `True`
- Facts: `{"frozen_inputs": 10, "player_sha256": "ab5809518c33adf6dad28c9ffe467d2f78f0c00bf78991fef991a7dd04a8fc48", "scene_scope_v5_disabled": 0, "scene_scope_v6_disabled": 0, "scene_scope_v8_renderers": 0, "scene_sha256": "4f15673e1de7eeb9f92dbfa058c40ae263549449c9ee2c5b98b59c7161a5d32f", "staged_files": 1}`
- Failure: `scene renderer state delta is not exactly sixteen enabled-to-disabled changes`
- Failure: `scene renderer state delta is not V5=5 and V6=11`
- Failure: `scene contains 0 enabled V8 MeshRenderers, expected 10`
- Failure: `out-of-scope staged path: Packages/manifest.json`
- Failure: `required V8 path not staged: Assets/_Project/Scenes/School_MVP.unity`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtAudit.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtPipeline.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtBuilder.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtScreenshotExporter.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8WindowsBuild.cs`
- Failure: `required V8 path not staged: Assets/_Project/Scripts/Gameplay/KhufuV8TempleProofProbe.cs`
- Failure: `required V8 path not staged: tools/validate_khufu_v8_temple_production_art.py`

V8_AGGREGATE_VERDICT: failed
