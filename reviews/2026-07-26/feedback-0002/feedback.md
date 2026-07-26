# Feedback 0002

Scene: Assets/_Project/Scenes/School_MVP.unity
Screenshot: reviews/captures/game-2026-07-26t16-19-14-09-00.png
Run: runs/unity-feedback-capture-2026-07-26t16-19-14-09-00/unity_feedback_capture.md
Frame: Operator_Overview_Camera, 1600x900
Action: ChannelPlayProductionValidator.CaptureFeedbackFrame
Priority: P2
Status: routed

## Observation

The Unity-rendered image is valid and no longer exposes unrelated desktop
applications. However, the overview framing is dominated by the tall wall on
the right and a steep upward angle. The player, objectives, and intended route
are not readable from this evidence frame.

## Requested Change

Reframe `Operator_Overview_Camera` to show the playable School MVP route,
player start, and primary objective landmarks in one legible overview. Keep
the capture deterministic and retain the non-blank PNG validation.

## Agent Interpretation

Treat this as a Unity camera-composition change. Preserve gameplay camera
behavior; only the disabled operator evidence camera and its validation should
change.

## Files Changed

Assets/_Project/Scripts/Editor/ChannelPlayProductionValidator.cs
tools/studio/company/game_loops.py
tools/studio/company/unity.py
tools/studio/company/feedback.py

## Verification

Unity playtest smoke passed with 9 checks and 0 compile errors.
Unity feedback capture passed at 1600x900; PNG size 1,226,458 bytes and
luminance range 0.8267.

## Routing Receipt

- reviews/2026-07-26/feedback-0002/routing_receipt.md
- Baseline evidence: runs/unity-check-2026-07-26t16-33-49-09-00/unity_check.md

## Routed Tasks

- task-0006 -> qa_playtest (memory/sessions/20260726-163349-process-feedback-md/work_orders/task-0006-qa_playtest.md)
- task-0007 -> unity_gameplay (memory/sessions/20260726-163349-process-feedback-md/work_orders/task-0007-unity_gameplay.md)
- task-0008 -> critic_reviewer (memory/sessions/20260726-163349-process-feedback-md/work_orders/task-0008-critic_reviewer.md)
