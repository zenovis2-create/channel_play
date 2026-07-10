# Khufu V5 Channelctl Validation Receipt

- Overall V5 verdict: **passed with accepted legacy-surface substitution `KV5-D-012`**
- Date: `2026-07-11`
- Tested implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Unity: `6000.0.76f1`
- Editor executable: `C:\Users\User\Unity\Hub\Editor\6000.0.76f1\Editor\Unity.exe`

## Batch Compile

Command:

```powershell
$env:UNITY_EDITOR='C:\Users\User\Unity\Hub\Editor\6000.0.76f1\Editor\Unity.exe'
python tools/channelctl unity check --batch
```

Result: process exit `0`, Unity exit `0`, compile errors `0`.

- Receipt: [`unity_check.md`](../unity-check-2026-07-11t02-07-46-09-00/unity_check.md)
- Editor log summary: [`editor-log-summary.md`](../unity-check-2026-07-11t02-07-46-09-00/editor-log-summary.md)
- Receipt SHA256: `726f532c2db517277916a2cc9300540f45a60a3b9315976375d44dcc64c8dd97`
- Log SHA256: `b8e7f4db918d3d32a583c15cb9f9b63ab64151497a92b63c5de1ec4ae69eb4eb`

The first invocation without `UNITY_EDITOR` failed before Unity launch because the imported
project tool retained a macOS fallback path. The corrected Windows-path run above is the accepted
receipt; the empty failed run directory is not evidence.

## Generic Playtest Smoke

Command:

```powershell
python tools/channelctl unity playtest
```

Result: process exit `0`, Unity exit `0`, compile errors `0`, `15` scene checks passed.

```text
CHANNEL_PLAY_PLAYTEST_SMOKE result=passed checks=15 scene="Assets/_Project/Scenes/School_MVP.unity"
```

- Receipt: [`unity_playtest.md`](../unity-playtest-2026-07-11t02-08-52-09-00/unity_playtest.md)
- Editor log summary: [`editor-log-summary.md`](../unity-playtest-2026-07-11t02-08-52-09-00/editor-log-summary.md)
- Receipt SHA256: `fc50d6af348ae78a74132a92bb78d267bd846a2e8412be1f4e812d7ecf4c50fe`
- Log SHA256: `d3227a663ec158938a7a0a7d072fab1fcb470a713c26a377c71a87a2cc90357f`

## Legacy V2 Simulation Surface

`python tools/channelctl unity sim-check` exited `1` with zero compiler errors because the command
hard-codes `Runtime_Pyramid_Maze_V2` and six `MazeV2_*` markers. The committed Khufu V5 scene
correctly has none of those roots, and two expected markers contain Djoser/Hawara names explicitly
forbidden by `KV5-R-001`.

- Fail-closed receipt: [`unity_sim_check.md`](../unity-sim-check-2026-07-11t02-09-24-09-00/unity_sim_check.md)
- Detailed receipt: [`receipt.md`](../unity-sim-check-2026-07-11t02-09-24-09-00/receipt.md)
- Editor log summary: [`editor-log-summary.md`](../unity-sim-check-2026-07-11t02-09-24-09-00/editor-log-summary.md)

This failure is retained as applicability evidence, not reported as a V5 pass. The V2-only scripted
agent command was not rerun because its source accepts only `pyramid-maze-v2` and would repeat the
same wrong-root test.

## V5-Specific Replacement

Accepted decision `KV5-D-012` replaces only the V2 root/route portions of `KV5-T-011` with these
V5-specific surfaces:

| Required behavior | V5 evidence | Result |
| --- | --- | --- |
| Runtime map spawns | generic playtest plus authored-binding PlayMode startup | passed |
| Player moves on physical routes | `1758.6 m`, `3533` CharacterController steps | passed |
| Three named keys in any order | all `6/6` permutations | passed |
| Terminal, shop, early exit, final extraction | Gate 4 acceptance and PlayMode event assertions | passed |
| Scripted route | critical `898.6 m`; Sun/Crown/Earth routes all completed | passed |
| Collision and stuck behavior | `415` clearance samples, maximum path error `0.338 m` | passed |
| Unity errors | `0` in the accepted V5 probe | passed |

The replacement receipts are [`gate4-final.md`](gate4-final.md) and
[`playmode-probe.md`](playmode-probe.md). No claim is made that the V2 simulation itself passed.

CHANNELCTL_V5_VERDICT: passed_with_D012_substitution
