# Khufu V5 Social-Deduction Rehearsal

- Verdict: **passed for the simulated eight-state roster**
- Date: `2026-07-11`
- Reviewer: `Codex interactive Unity/visual review`
- Reviewer type: `local implementation reviewer, not a human multiplayer participant`
- Tested implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Scene SHA256: `7606cfb305d7b0269af5db6f35544583765a56ebee2bb68844b5b239bf5e65ff`

## Replay Evidence

The committed PlayMode probe is the route replay. It drove a real CharacterController for
`1758.6 m` over `3533` steps with maximum step error `0.338 m`; the critical route was `898.6 m`.
The Gate 4 validator supplied `415` clearance samples, `8/8` hub positions, six connected major
loops, and three far-side shortcut unlock/reset checks. Source receipts:

- [`playmode-probe.md`](playmode-probe.md)
- [`gate4-final.md`](gate4-final.md)
- [`top_down_route_graph.png`](captures/top_down_route_graph.png)
- [`player_temple_hub.png`](captures/player_temple_hub.png)

An interactive PlayMode roster snapshot placed the participant at the hub centre and retained the
seven runtime proxies on the authored circulation ring:

| Actor | Position `(x,y,z)` m |
| --- | --- |
| MVP_Player | `(62.00,1.20,0.00)` |
| Runtime_Bot_P2 | `(69.03,1.10,2.85)` |
| Runtime_Bot_P3 | `(64.63,1.10,7.30)` |
| Runtime_Bot_P4 | `(58.49,1.10,7.43)` |
| Runtime_Bot_P5 | `(54.21,1.10,3.22)` |
| Runtime_Bot_P6 | `(54.31,1.10,-2.80)` |
| Runtime_Bot_P7 | `(58.78,1.10,-7.06)` |
| Runtime_Bot_P8 | `(65.07,1.10,-7.04)` |

Minimum horizontal actor spacing was `6.002 m`; maximum hub-centre radius was `8.430 m`. Runtime
bot colliders are triggers, so the simulated roster cannot create persistent body blocking. This
proves the scoped proxy-circulation claim, not networked player collision.

## Per-Key Review Form

| Route | Controller evidence | Public interaction | Private-risk segment | Reconnection observation | Verdict |
| --- | --- | --- | --- | --- | --- |
| Sun | `216.2 m`, `48.0 s` | `(80.0,0.6,50.0)` | `(40.0,0.6,60.0)` | Connected surface loop returns to Temple Hub; far-side shortcut contract passed | passed |
| Crown | `332.9 m`, `74.0 s` | `(30.0,3.4,-60.0)` | `(-74.3,4.4,38.3)` | Upper branch reconnects through the six-loop graph; no permanent one-way objective trap | passed |
| Earth | `310.9 m`, `69.1 s` | `(45.0,-4.6,-70.0)` | `(-85.0,-18.6,-55.0)` | Underworld cutaway shows the return loop; shortcut unlock/reset contract passed | passed |

The public/private coordinates were read from live committed-scene marker transforms. The
reconnection statement is an inference from the passing graph, controller route, and shortcut
evidence; it is not an archaeological claim.

## Review Observations

1. The Temple Hub supports a central participant plus seven proxies with more than six metres of
   minimum authored spacing.
2. Each key path has a distinct public interaction marker before a private-risk marker, so social
   visibility can change without putting the objective behind a permanent isolated trap.
3. Sun is the shortest and most public route; Crown is the longest observation-heavy route; Earth
   has the strongest private-risk language and vertical change. These differences support role
   inference without changing key order.
4. The operator overview and top-down route proof keep all three objectives and return structure
   readable.

## Issue List And Limits

- Closed issues: no missing public/private marker; no missing hub proxy; no permanent required
  one-way objective; no persistent proxy body blocking in the simulated contract.
- Accepted scope limit: no real networked multiplayer or human eight-player session was run.
- Release-language rule: describe this only as a tested simulated eight-state roster. Do not claim
  real multiplayer balance, latency behavior, or human deception quality.

SOCIAL_REHEARSAL_VERDICT: passed_simulated_roster
