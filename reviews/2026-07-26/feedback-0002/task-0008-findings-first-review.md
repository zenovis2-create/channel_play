# Task 0008 Findings-First Review

- Reviewer: `critic_reviewer`
- Disposition: accepted
- Scope: task-0007 camera composition and evidence

## Findings

1. **[P3] The automated framing gate does not measure occlusion or minimum
   projected size.** The validator confirms that each landmark's renderer-bounds
   center remains inside a 3% viewport margin, but an included landmark could
   become visually small or hidden after future geometry changes. The current
   refreshed capture was manually inspected and is legible, so this is not a
   blocker for feedback closure. If the map expands again, add a minimum
   screen-space bounds or visibility check in
   [`ChannelPlayProductionValidator.cs`](../../../Assets/_Project/Scripts/Editor/ChannelPlayProductionValidator.cs#L364).

No P0-P2 findings were identified.

## Evidence Reviewed

- [Original feedback](feedback.md)
- [QA reproduction](task-0006-qa-reproduction.md)
- [Before capture](../../captures/game-2026-07-26t16-19-14-09-00.png)
- [After capture](../../captures/game-2026-07-26t17-15-41-09-00.png)
- [Unity compile receipt](../../../runs/unity-check-2026-07-26t17-15-19-09-00/unity_check.md)
- [Playtest receipt](../../../runs/unity-playtest-2026-07-26t17-15-32-09-00/unity_playtest.md)
- [Capture receipt](../../../runs/unity-feedback-capture-2026-07-26t17-15-41-09-00/unity_feedback_capture.md)

## Acceptance Check

- Deterministic `1600x900` capture: passed.
- Full playable route visible without the former foreground-wall obstruction:
  passed.
- Player, Earth, Sun, Crown, and Exit anchors inside the frame: passed at
  viewport coordinates `0.40/0.51`, `0.37/0.46`, `0.64/0.50`, `0.46/0.54`,
  and `0.52/0.68`.
- Disabled evidence camera preserved: passed.
- Compile, playtest, and non-blank PNG gates: passed with 0 compile errors,
  10 playtest checks, 209,410 PNG bytes, and luminance range `0.9298`.

## Conclusion

Task 0007 satisfies the requested camera-composition correction without
changing gameplay camera behavior. Feedback 0002 can be resolved; retain the P3
note as a future hardening recommendation rather than reopening this fix.
