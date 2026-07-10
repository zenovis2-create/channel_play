# Khufu V6 Visual Fidelity Slice

V6 is a bounded visual-fidelity pass over the accepted Khufu V5 mega-labyrinth. It improves the
Temple Hub and dense core with deterministic limestone, basalt, granite, casing, causeway, and
scan-inlay materials plus a small colonnade dressing set. It does not replace V5 topology.

This is a fictionalized production-readability slice inspired by Khufu's pyramid complex. It is
not a claim that the internal mega-labyrinth or the dressed temple form is an archaeological
reconstruction. Historical grounding remains in
[`KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md`](../research/KHUFU_MEGA_LABYRINTH_MAP_RESEARCH.md).

## Key Artifacts

- Scene: `Assets/_Project/Scenes/School_MVP.unity`
- Builder: `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs`
- Unity validator: `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs`
- Aggregate validator: `tools/validate_khufu_v6_visual_slice.py`
- Evidence root: `runs/khufu-v6-visual-slice/`
- Windows player: `Builds/KhufuV6/ChannelPlayKhufuV6.exe`

## Current Result

The Unity static validator, rebuild-idempotence check, V5 Gate 4 regression, CharacterController
PlayMode regression, four-view visual delta check, Windows Development Player build, and visible
player performance budget all pass. External Fable final review returned `ship`, and the aggregate
validator passes with scene/player/performance binding plus generated-asset GUID checks.

Unity MCP is not part of the acceptance proof: the HTTP server started, but the Unity package did
not register an Editor instance. NotebookLM research also remained unavailable because its local
authentication had expired. Both are reported as tooling gaps, not as completed integrations.
