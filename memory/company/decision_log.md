# Decision Log

## 2026-06-01

Decision: Add `Channel Play Agent Company` as the orchestration layer for `Channel Play Studio`.

Reason:

- The project needs shared memory, role-specific agents, explicit work orders, locks, and verification gates.
- A simple list of AI tools is not enough for Unity game production.

Impact:

- Agent role profiles live under `agents/`.
- Operational shared memory starts under `memory/company/`.
- Future `channelctl company` commands should read and write these files.
