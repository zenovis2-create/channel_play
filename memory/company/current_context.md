# Current Context

Project: `channel_play`

Date: 2026-06-01

Current production direction:

- Unity game is the product.
- Channel Play Studio is the production cockpit.
- Channel Play Agent Company is the team/orchestration layer.
- Mac Studio is the Unity/Blender/OBS implementation machine.
- gdx1 is reserved for server, bot, soak-test, and background worker jobs after SSH authentication is fixed.

Current constraints:

- One writer per Unity scene, prefab folder, or script system.
- Agent work must produce evidence before completion.
- Shared memory must be updated after meaningful decisions.
