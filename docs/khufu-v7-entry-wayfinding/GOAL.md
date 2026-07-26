# Goal

Deliver a playable Khufu V7 entry in which the participant is not trapped behind Valley Gate geometry
and can read the route toward the Temple Hub from the first rendered frame.

## Observable Done Surface

- The final Windows player shows the participant fully inside the frame.
- At least two V7 guides project into the entry viewport.
- The center viewport sample resolves to a route floor or guide, not a blocking pylon.
- The exact-pylon name mutation fails the entry proof and visibly blocks the route.
- V5 acceptance, V5 PlayMode traversal, V7 static gates, Windows build, and performance all pass.

## False-Done Conditions

- A receipt says passed but the screenshot is wall-filled, black, or route-unreadable.
- The proof passes after exact pylon names are mutated.
- V5/V6 frozen inputs or package state change.
- The build, PlayMode receipt, or bindings refer to a stale scene hash.
- Completion is claimed without a Fable final-review ship decision.
