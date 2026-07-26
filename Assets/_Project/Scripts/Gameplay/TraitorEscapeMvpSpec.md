# Traitor Escape MVP Gameplay Spec

Task: task-0018
Goal: Make one playable Unity session that can support a pilot recording.
Write scope: Assets/_Project/Scripts/Gameplay
Current slice: runtime playable foundation for the first Traitor Escape pilot.

## Player Promise

One local participant can enter a small 3D game-show map, move around, collect keys and points, buy three items, use those items, open the final door, and switch into an operator camera for OBS-friendly overview shots.

This is not the final networked show. It is the playable foundation for the first pilot video.

## MVP Slice

- Runtime 3D map: enclosed stage, cover blocks, mission terminal, shop terminal, final door.
- Local player: CharacterController movement, sprint, jump, follow camera.
- Roster: eight participant states with two teams and one hidden traitor.
- Timer: 35 minute pilot session clock.
- Progress: three keys required to open the final door.
- Points: pickups and mission terminal award points.
- Shop: buy Truth Pen, Location Scanner, and Doppelganger Serum.
- Items:
  - Truth Pen reveals one participant as traitor or clear.
  - Location Scanner points toward the nearest remaining key or the final door.
  - Doppelganger Serum temporarily changes the local player to the red team material.
- Operator mode: top-down camera, point grant, item pack grant, role reveal, timer reset, full session reset.
- Pilot pacing: operator key assist can unblock a recording take without changing the normal key-search path.
- Readability: key and point pickups have runtime labels for quick OBS/playtest recognition.
- OBS readiness: all HUD state is visible in one game view.

## Implementation Checklist

- [x] Auto-create the MVP session at runtime after any scene load.
- [x] Build a small enclosed 3D map without editing scene assets.
- [x] Spawn a local controllable participant with follow camera.
- [x] Show points, keys, timer, objective, item inventory, and last event in HUD.
- [x] Show an eight-participant roster with teams and one hidden traitor.
- [x] Support point pickups and a mission terminal point source.
- [x] Support shop purchases for all three MVP items.
- [x] Support item usage for Truth Pen, Location Scanner, and Doppelganger Serum.
- [x] Support final door unlock after three keys.
- [x] Support operator overview mode with pilot controls.
- [x] Support operator key assist for pilot pacing.
- [x] Label key and point pickups in the runtime map.
- [ ] Replace simulated roster with real multiplayer transport.
- [ ] Replace runtime primitives with art-directed scene/prefab assets.
- [ ] Add production audio and final OBS overlay styling.

## Pilot Checklist

- [ ] Start scene and confirm the runtime map appears.
- [ ] Move the local player away from spawn.
- [ ] Collect at least one point pickup.
- [ ] Collect all three keys.
- [ ] Open the shop and buy at least one item.
- [ ] Use Truth Pen, Location Scanner, and Doppelganger Serum at least once.
- [ ] Run the mission terminal once.
- [ ] Open the final door.
- [ ] Switch to operator view and confirm the overview camera, point grant, and item pack grant work.
- [ ] Record a short OBS take with HUD, scoreboard, and operator panel visible.

## Acceptance Criteria For This Task

- Play mode creates a visible game-show test arena with no scene or prefab edit required.
- The first milestone is testable: player movement works and points are visible in the HUD.
- The shop and all three MVP items are usable from keyboard or IMGUI buttons.
- The operator can switch to an overview shot and grant points/items for pilot pacing.
- The right-side checklist reaches a visible pilot-ready state after movement, points, keys, shop, all three item uses, mission, exit, operator view, operator point grant, and operator item grant are exercised.
- Unity compile or playtest evidence is reported before closing the task.

## Task 0029 Verification

- Unity compile check: `runs/unity-check-2026-06-04t15-34-07-09-00/unity_check.md` reports exit code 0 and compile errors 0.
- Unity playtest smoke: `runs/unity-playtest-2026-06-04t15-35-03-09-00/unity_playtest.md` reports exit code 0, compile errors 0, and `CHANNEL_PLAY_PLAYTEST_SMOKE result=passed`.
- Studio goal audit: task-0029 is closed with verification passed and three evidence links attached.

## Controls

- WASD or arrows: move.
- Left Shift: sprint.
- Space: jump.
- E: interact with nearby shop, mission terminal, or final door.
- B: open or close shop.
- 1, 2, 3: buy while shop is open; use items while shop is closed.
- Tab: toggle operator view.
- Operator view: WASD pan, Q/E or mouse wheel zoom, R reset.

## Known Non-Goals For This Slice

- Real multiplayer transport.
- Server-authoritative points.
- Persistent inventory.
- Final art, audio, or production lighting.
- Scene/prefab edits outside the assigned lock.
