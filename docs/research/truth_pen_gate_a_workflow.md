# Truth Pen Source and Production Gates

Task: `task-0010`

Status: implemented; Truth Pen remains blocked

## Purpose

Gate A authorizes one source strategy before a concept image is generated or
downloaded. Gate B then binds the resulting source file, its SHA-256, its
creation records, and exactly one 3D provider before production.

## Commands

```powershell
python tools/channelctl asset gate-a-init truth_pen --path openai
python tools/channelctl asset gate-a-check truth_pen
python tools/channelctl asset gate-b-init truth_pen
python tools/channelctl asset gate-b-check truth_pen
```

Gate B initialization fails until Gate A passes. Protected lifecycle transitions
(`generated`, `cleanup`, `unity_ready`, and `accepted`) and
`asset generate3d` fail until Gate B passes.

## Gate A Record

Select `commissioned_human`, `openai`, or `cc0`. Complete the common rights,
jurisdiction, input-clearance, and repository evidence fields. Human work must
grant downstream asset creation. OpenAI work must record non-uniqueness, human
review, output-allocation and indemnity limits, AI provenance, and the
disclosure decision. CC0 work must include a retrieval snapshot and affirmer
authority evidence.

The critic receipt must be structured JSON. It is accepted only when it names
the `critic_reviewer` role, asset, task, gate, review time, authorization scope,
and the exact current manifest SHA-256. Gate-record CRLF/CR line endings are
normalized to LF before hashing, while approved binary source files retain
exact byte hashes. An unrelated `APPROVED` document cannot unlock a gate.

## Gate B Record

Record the repository-relative source path and hash, source timestamp,
provider/model, prompt and edit history, clearance and disclosure records,
rights, and one approved 3D provider. Absolute sources, changed files, provider
mismatches, `auto`/`both`, and unreviewed local fallback fail closed.

Gate state is separate from the asset lifecycle `status`; scaffold refreshes do
not convert `briefed` or `accepted` into a gate state.

Asset preparation stamps every Blender/Unity scaffold with the current gate
state. The generated Blender batch template also calls the Gate B evaluator at
execution time, so a stale template cannot bypass a revoked or changed record.

## Current Truth Pen Result

Task `task-0011` selected `commissioned_human` as the procurement path and
created `docs/research/truth_pen_gate_a_commissioning_packet.md`. This selection
is not an authorization. `runs/asset-gate-a-truth_pen/gate_a_check.md` still
records `FAIL` because no named creator, signed rights instrument, jurisdiction,
input-clearance evidence, or bound critic approval has been supplied. Source
creation and all downstream production remain blocked.
