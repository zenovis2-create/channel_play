# Channel Sim Runtime Implementation Spec

Updated: 2026-06-07

Source plan:

- `docs/research/simworld_absorption_plan.md`

## 0. Decision

Channel Play absorbs SimWorld as an agent-simulation operating pattern, not as an engine migration.

Keep:

- Unity as the production game engine
- Mac Studio as the Unity authority
- gdx1 as AI/ops/research/background worker only until compatibility is proven
- Pyramid Maze V2 as the first benchmark environment
- receipt-backed completion

Build:

```text
Unity scene
  -> sensor observations
  -> scene state
  -> agent actions
  -> trajectory / metrics
  -> replay / review
  -> Studio visible result
```

## 1. Goals

The runtime must let a Channel Play agent see, act, and prove work inside Unity.

Primary goal:

```bash
tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted
```

That command must create a complete run directory with observations, actions, metrics, trajectory, review, and receipt.

Secondary goals:

- Give Codex/Hermes/OpenClaw/agy the same action schema later.
- Make agent progress visible in Channel Play Studio.
- Attach human review to frames, actions, and receipts.
- Connect Asset Forge maps to semantic labels and test scenarios.

## 2. Non-Goals

Do not:

- migrate Channel Play from Unity to Unreal
- import SimWorld demo assets
- require gdx1 for local Unity playtest
- call an agent text answer "done" without artifacts
- build a database before JSON/Markdown receipts are reliable
- implement all sensors at once before RGB/playtest works

## 3. System Boundary

### 3.1 Unity Runtime

Unity owns:

- scene objects
- route markers
- camera/sensor capture
- player/agent placement
- action execution
- collision/progress tracking
- local playtest proof

### 3.2 `channelctl`

`tools/channelctl` owns:

- command entrypoints
- run directory creation
- Unity batch invocations
- artifact discovery
- receipt writing
- Studio/job state updates

### 3.3 Studio

Channel Play Studio owns:

- command chat
- active agent run visibility
- viewport/replay surface
- metrics panel
- artifact/receipt links
- human feedback capture

### 3.4 Agent Company

Agent Company owns:

- role selection
- goal decomposition
- work orders
- run review
- memory summary
- handoff to implementation agents

### 3.5 gdx1

gdx1 owns only proven-compatible work:

- long-running research
- model/asset generation
- logs
- repository sync
- optional SimWorld/UE experiments after smoke proof

## 4. Unity Script Layout

Create scripts under:

```text
Assets/_Project/Scripts/Simulation/
```

Required files:

```text
ChannelSimRuntime.cs
ChannelSensorRig.cs
ChannelSegmentationId.cs
ChannelDepthCapture.cs
ChannelActionExecutor.cs
ChannelAgentController.cs
ChannelWorldStateExporter.cs
ChannelRunMetricsWriter.cs
ChannelScenarioLoader.cs
ChannelRouteGraph.cs
ChannelRunArtifactWriter.cs
```

### 4.1 `ChannelSimRuntime`

Purpose:

- top-level runtime coordinator
- binds sensor rig, action executor, world exporter, and metrics writer

Public responsibilities:

- initialize run
- locate `Runtime_Pyramid_Maze_V2`
- locate route markers
- spawn or bind scripted agent
- tick simulation steps
- finish run with pass/fail reason

Done when:

- runtime can start from Editor/batch mode
- missing scene objects produce explicit failure
- receipt includes runtime version and scene name

### 4.2 `ChannelSensorRig`

Purpose:

- capture agent-observable frames

Minimum sensors:

- RGB camera image
- segmentation image

Deferred sensor:

- depth image, can start as placeholder metadata if real depth texture is not ready

Output:

```text
observations/
  frame_000_rgb.png
  frame_000_segmentation.png
  frame_000_depth.png
  frame_000.json
```

Frame metadata:

```json
{
  "frame": 0,
  "time": 0.0,
  "agentId": "scripted-agent-001",
  "position": [0, 0, 0],
  "rotationY": 0,
  "sensors": {
    "rgb": "observations/frame_000_rgb.png",
    "segmentation": "observations/frame_000_segmentation.png",
    "depth": "observations/frame_000_depth.png"
  }
}
```

### 4.3 `ChannelSegmentationId`

Purpose:

- assign stable semantic/category IDs to scene objects

Categories:

- entrance
- corridor
- chamber
- false_door
- trap
- pressure_plate
- climbable_step
- cover
- collectible
- sarcophagus
- exit
- hazard
- occluder
- landmark

Output:

```text
semantic_labels.json
```

Required fields:

```json
{
  "objectId": "MazeV2_Entrance_Threshold",
  "category": "entrance",
  "segmentationColor": "#ff0000",
  "worldPosition": [0, 0, 0],
  "bounds": {
    "center": [0, 0, 0],
    "size": [1, 1, 1]
  }
}
```

### 4.4 `ChannelActionExecutor`

Purpose:

- execute normalized agent actions

Action schema:

```json
{
  "step": 1,
  "agentId": "scripted-agent-001",
  "action": "move_to_marker",
  "target": "MazeV2_Djoser_Gallery",
  "parameters": {
    "speed": 2.5,
    "timeoutSeconds": 20
  }
}
```

Supported v1 actions:

| Action | Meaning |
|---|---|
| `spawn_at_marker` | place agent at route marker |
| `move_to_marker` | move agent to named route marker |
| `look_at_marker` | rotate toward named marker |
| `wait` | wait fixed seconds |
| `capture_observation` | save sensor frame |
| `interact` | trigger named interactable |
| `finish_run` | request run completion |

Unsupported action rule:

- write failure to `actions.jsonl`
- continue only if action is marked optional

### 4.5 `ChannelAgentController`

Purpose:

- own the active agent body
- execute scripted route for v1
- expose same interface for future AI agents

Agent modes:

| Mode | Description |
|---|---|
| `scripted` | deterministic waypoint runner |
| `replay` | reads prior actions |
| `external` | future Codex/Hermes/OpenClaw/agy bridge |

### 4.6 `ChannelWorldStateExporter`

Purpose:

- export a machine-readable scene state snapshot

Output:

```text
scene_state.json
```

Required fields:

```json
{
  "scene": "School_MVP",
  "environment": "Runtime_Pyramid_Maze_V2",
  "routeMarkers": [],
  "semanticObjects": [],
  "agents": [],
  "interactables": [],
  "hazards": [],
  "timestamp": "2026-06-07T00:00:00+09:00"
}
```

### 4.7 `ChannelRunMetricsWriter`

Purpose:

- write time-series progress and pass/fail evidence

Output:

```text
metrics.jsonl
trajectory.json
collisions.jsonl
```

Metrics:

- elapsed seconds
- current route marker
- distance to target
- progress percent
- collision count
- stuck seconds
- observation count
- action count
- route gate pass/fail

### 4.8 `ChannelScenarioLoader`

Purpose:

- load scenario contracts from Asset Forge or built-in benchmark configs

Input:

```text
asset_pipeline/forge/<asset-id>/test_scenarios.json
```

Fallback:

- built-in Pyramid Maze V2 route if no scenario file exists

## 5. Run Directory Contract

Every sim/agent command must write:

```text
runs/agent-playtest-YYYYMMDD-HHMMSS/
  command.json
  scene_state.json
  semantic_labels.json
  observations/
  actions.jsonl
  metrics.jsonl
  trajectory.json
  collisions.jsonl
  screenshots/
  review.md
  receipt.md
```

### 5.1 `command.json`

```json
{
  "command": "tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted",
  "scene": "School_MVP",
  "environment": "pyramid-maze-v2",
  "agent": "scripted",
  "createdAt": "2026-06-07T00:00:00+09:00"
}
```

### 5.2 `receipt.md`

Must include:

- command
- scene
- agent mode
- result: pass/fail/blocked
- artifacts
- action count
- observation count
- route completion
- compile receipt link
- playtest receipt link
- failure reason if any
- next command

## 6. `channelctl` Command Spec

### 6.1 `unity sim-check`

Purpose:

- validate that simulation runtime files and scene objects exist

Checks:

- Unity project exists
- simulation scripts exist
- `School_MVP` exists
- `Runtime_Pyramid_Maze_V2` exists
- required route markers exist

Output:

```text
runs/unity-sim-check-<timestamp>/receipt.md
```

### 6.2 `unity agent-playtest pyramid-maze-v2 --agent scripted`

Purpose:

- first full absorption proof

Execution:

1. run Unity compile check
2. open/load `School_MVP`
3. bind Pyramid Maze V2 runtime
4. spawn scripted agent at entrance
5. move through route markers
6. capture observations at each gate
7. write metrics and trajectory
8. run review gate
9. write receipt

Pass criteria:

- compile passes
- route markers found
- at least 5 observations saved
- action log non-empty
- route completion is true
- receipt says pass

### 6.3 `unity sim-replay <run-dir>`

Purpose:

- review a prior agent run without rerunning Unity

Input:

- existing run directory

Output:

- replay summary
- frame/action index
- review file update

### 6.4 `unity sim-review <run-dir>`

Purpose:

- classify run as accepted, needs fix, blocked, or invalid

Review checks:

- artifacts exist
- route progress coherent
- screenshots/observations readable
- collision/stuck limits not exceeded
- receipt links valid

## 7. Studio UI Spec

Studio must show agent work like Codex app style, not a hidden task board.

Required panels:

| Panel | Content |
|---|---|
| Command Chat | user request, orchestrator command, agent replies |
| Live Run | current command, active step, status |
| Unity Viewport / Replay | latest RGB frame, frame scrubber |
| Agent Stack | selected roles, current task, cooperation state |
| Metrics | progress, collisions, stuck time, observations |
| Artifacts | receipt, scene state, action log, screenshots |
| Feedback | frame/action-specific notes |

Status labels:

- `대기`
- `진행 중`
- `막힘`
- `검토 필요`
- `완료`
- `증거 있음`

Forbidden UI behavior:

- no invisible review gate
- no task status without artifact link
- no completion badge without receipt
- no "검토 필요" dead-end without next command

## 8. Agent Company Spec

Add or strengthen these roles:

```text
agents/roles/simulation_architect.agent.md
agents/roles/agent_planner.agent.md
agents/roles/agent_playtester.agent.md
agents/roles/metrics_reviewer.agent.md
agents/roles/world_builder.agent.md
agents/roles/visual_qa.agent.md
```

Every agent playtest work order must include:

- objective
- scene
- target run command
- allowed write scope
- required evidence
- review criteria
- fallback if Unity fails

## 9. Asset Forge Simulation Contract

For map/zone assets, Asset Forge must add:

```text
asset_pipeline/forge/<asset-id>/
  simulation_contract.md
  semantic_labels.json
  nav_points.json
  interactables.json
  test_scenarios.json
  agent_eval_plan.md
```

Pyramid V2 first target:

```text
asset_pipeline/forge/pyramid_temple_full_environment/
```

Required route:

```text
MazeV2_Entrance_Threshold
MazeV2_Djoser_Gallery
MazeV2_Khufu_GrandGallery
MazeV2_Hawara_Labyrinth_Core
MazeV2_Burial_Chamber
MazeV2_Rear_Service_Exit
```

## 10. Phase Plan

### Phase 0. Spec Freeze

Deliver:

- this file
- implementation checklist
- observation/action schema locked

### Phase 1. Unity Sensor / Action Core

Deliver:

- simulation script folder
- RGB observation capture
- segmentation labels
- action executor
- scene state exporter

### Phase 2. Pyramid Agent Playtest

Deliver:

- scripted route runner
- `channelctl unity agent-playtest`
- complete run directory
- pass/fail receipt

### Phase 3. Studio Live Run UI

Deliver:

- live command stream
- run panel
- replay panel
- metrics/artifact drawer

### Phase 4. Asset Forge Semantic Pack

Deliver:

- semantic labels
- nav points
- interactables
- test scenarios
- agent eval plan

### Phase 5. gdx1 / SimWorld Probe

Deliver:

- compatibility probe only
- no production dependency until proven

### Phase 6. Replay / Mock Mode

Deliver:

- replay prior run without Unity
- compare runs
- attach feedback to frames/actions

## 11. External Reference Notes

Research anchors:

- SimWorld: UE backend, environment layer, agent layer, RGB/depth/segmentation sensors, Python communicator
- SimWorld-Studio: React UI, Express server, SSE, metrics hub, context manager, agent controller, asset browser, mock mode
- Unity: RenderTexture/camera capture, NavMeshAgent/route motion, command-line playtest pattern

Source URLs:

- https://github.com/SimWorld-AI/SimWorld
- https://arxiv.org/abs/2512.01078
- https://huggingface.co/datasets/SimWorld-AI/SimWorld/blob/main/README.md
- https://github.com/SimWorld-AI/SimWorld-Studio
- https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/AI/Components/NavMeshAgent.bindings.cs
- https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.high-definition/Documentation~/hdrp-camera-component-reference.md
