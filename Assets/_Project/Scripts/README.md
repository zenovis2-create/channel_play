# Scripts

Code is split by gameplay responsibility.

- `Core`: session lifecycle and shared primitives
- `Networking`: Netcode bootstrap and server/client boundaries
- `Player`: movement, camera, nameplate, team color
- `Operator`: operator commands and spectator camera
- `Points`: point state and server-side mutation
- `Shop`: shop requests and purchase validation
- `Items`: item definitions, inventory, and use effects
- `Missions`: mission definitions and completion checks
- `UI`: player, operator, and broadcast UI
- `Logging`: JSON Lines game session logs

Rules:

- Server owns points, item effects, missions, and timer.
- UI requests actions; it does not mutate authoritative state.
- Avoid global manager objects until a real need appears.
