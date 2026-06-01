# Agent Memory Policy

Shared memory is a production asset. Agents must treat it as the source of continuity, not as optional notes.

## Required Reads

Before work, every agent reads:

- `agents/company.md`
- `agents/memory_policy.md`
- its own `agents/roles/*.agent.md`
- `memory/company/current_context.md` if present
- the relevant Obsidian note or work order

## Memory Types

Canonical memory:

- `obsidian/channel_play/`
- design, decisions, specs, accepted direction

Operational memory:

- `memory/company/`
- active state, locks, task board, current session

Evidence memory:

- `runs/`
- `reviews/`
- `artifacts/`
- `logs/`
- `asset_pipeline/`

## Write Rules

- Do not overwrite another agent's report.
- Do not edit canonical design decisions silently.
- Add new decisions with date, context, reason, and impact.
- If memory conflicts with current evidence, flag it in the agent report.
- If the target scope is unclear, do scout work only.

## Done Rule

An agent report must include:

- what changed
- what evidence proves it
- what still needs review
- what memory should be updated
