# Agent Observation / Action Schema

Updated: 2026-06-07

## Scope

This schema is the shared contract for scripted agents first, then Codex/Hermes/OpenClaw/agy later.

## Observation Packet

Each observation frame writes:

```text
runs/agent-playtest-*/observations/frame_000_rgb.png
runs/agent-playtest-*/observations/frame_000_segmentation.png
runs/agent-playtest-*/observations/frame_000_depth.png
runs/agent-playtest-*/observations/frame_000.json
```

Frame metadata:

```json
{
  "frame": 0,
  "agentId": "scripted-agent-001",
  "routeMarker": "MazeV2_Entrance_Threshold",
  "position": [0.0, 0.0, 0.0],
  "depthStatus": "placeholder",
  "sensors": {
    "rgb": "runs/.../frame_000_rgb.png",
    "segmentation": "runs/.../frame_000_segmentation.png",
    "depth": "runs/.../frame_000_depth.png"
  }
}
```

## Semantic Label

```json
{
  "objectId": "MazeV2_Entrance_Threshold",
  "category": "entrance",
  "segmentationColor": "#ff0000",
  "worldPosition": [0.0, 0.0, 0.0]
}
```

Supported first-pass categories:

- entrance
- corridor
- chamber
- sarcophagus
- exit
- landmark
- trap
- pressure_plate
- hazard
- occluder

## Action Log Entry

Each line in `actions.jsonl` is one action:

```json
{"step":0,"action":"spawn_at_marker","target":"MazeV2_Entrance_Threshold"}
{"step":1,"action":"move_to_marker","target":"MazeV2_Djoser_Gallery"}
{"step":6,"action":"finish_run","target":"route_complete"}
```

Supported v1 actions:

- `spawn_at_marker`
- `move_to_marker`
- `look_at_marker`
- `wait`
- `capture_observation`
- `interact`
- `finish_run`

## Metrics Entry

Each line in `metrics.jsonl` is one route/progress sample:

```json
{
  "step": 1,
  "marker": "MazeV2_Djoser_Gallery",
  "progressPercent": 33.3,
  "collisionCount": 0,
  "stuckSeconds": 0,
  "observationCount": 2
}
```

## External Agent Rule

External AI agents may read observations, scene state, semantic labels, and prior actions. They must return only valid action entries. The action validator rejects unknown actions before Unity execution.
