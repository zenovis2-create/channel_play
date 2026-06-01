# Channel Play Agent Company

Purpose: coordinate specialized AI agents for the `channel_play` Unity game without losing memory, scope, or verification.

Operating rules:

- The human producer owns taste, priority, and final acceptance.
- The chief orchestrator owns task breakdown, role selection, memory briefing, locks, and integration.
- Only one writer may modify a Unity scene, prefab folder, or script system at a time.
- Every agent reads the current context before working.
- Every agent returns a structured report.
- Work is not done until evidence is attached.
- Decisions that affect future work must be written to Obsidian or `memory/company/decision_log.md`.

Default company loop:

```text
request -> brief -> assign -> execute -> review -> verify -> memory update -> commit
```
