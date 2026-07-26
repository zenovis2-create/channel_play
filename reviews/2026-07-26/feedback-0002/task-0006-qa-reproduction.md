# Task 0006 QA Reproduction

- Status: reproduced
- Severity: P2
- Scope: evidence-only; no Unity assets or scripts changed

## Observed Behavior

The deterministic `Operator_Overview_Camera` capture is technically valid but
does not function as an overview. A tall wall dominates the right side, the
camera points steeply upward, and the playable ground plane is largely outside
the frame. The player start, primary objective landmarks, and the route between
them cannot be identified from the image.

## Reproduction

1. Review the [1600x900 evidence frame](../../captures/game-2026-07-26t16-19-14-09-00.png).
2. Confirm the matching [Unity capture receipt](../../../runs/unity-feedback-capture-2026-07-26t16-19-14-09-00/unity_feedback_capture.md).
3. Verify the receipt names `Operator_Overview_Camera` and reports a successful
   deterministic capture with 0 compile errors, 1,226,458 bytes, and luminance
   range `0.8267`.
4. Inspect the frame for the playable route, player start, and primary objective
   landmarks. None are legible as distinct gameplay elements.

Result: reproduced from the committed capture and receipt. The PNG non-blank
gate passes, so the defect is camera composition rather than capture failure.

## Impact

The frame cannot serve as review or OBS-readiness evidence because it does not
communicate the School MVP play space or objective flow. Gameplay behavior is
not implicated; the suspected system is the disabled operator evidence camera.

## Acceptance Criteria for Task 0007

- Keep the capture deterministic at `1600x900`.
- Show the player start, playable route, and primary objective landmarks in one
  unobstructed frame.
- Prevent a foreground wall or steep upward angle from dominating the image.
- Preserve the PNG size/luminance validation and complete with 0 compile errors.
- Supply a refreshed capture and Unity receipt for before/after comparison.
