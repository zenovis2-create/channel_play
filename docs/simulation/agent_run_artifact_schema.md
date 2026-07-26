# Agent Run Artifact Schema

Updated: 2026-06-07

## Run Directory

Every agent playtest run must write:

```text
runs/agent-playtest-<environment>-<agent>-<timestamp>/
  Editor.log
  unity_agent_playtest.md
  command.json
  scene_state.json
  semantic_labels.json
  actions.jsonl
  metrics.jsonl
  trajectory.json
  collisions.jsonl
  review.md
  receipt.md
  observations/
    frame_000_rgb.png
    frame_000_segmentation.png
    frame_000_depth.png
    frame_000.json
```

## Required Status Values

Receipt status:

- `agent_playtest_passed`
- `agent_playtest_failed`

Review status:

- `agent_playtest_review_ready`
- `sim_review_passed`
- `sim_review_failed`

## Minimum Pass Criteria

- Unity exit code 0
- compile errors 0
- marker line contains `CHANNEL_PLAY_AGENT_PLAYTEST result=passed`
- route markers `6/6`
- RGB observations at least 5
- `actions.jsonl` non-empty
- `metrics.jsonl` non-empty
- `trajectory.json` exists
- `receipt.md` exists
- `review.md` exists

## Review Command

```bash
tools/channelctl unity sim-review <run-dir>
```

The review must check artifact presence, observation count, action count, metric count, and write a receipt-like markdown file under `runs/unity-sim-review-*`.

## Replay Command

```bash
tools/channelctl unity sim-replay <run-dir>
```

The replay command does not rerun Unity. It indexes existing observations, actions, and metrics for Studio/review consumption.
