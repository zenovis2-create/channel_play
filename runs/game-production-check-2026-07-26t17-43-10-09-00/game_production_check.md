# Game Production Check

Checked: 2026-07-26T17:43:51+09:00
Readiness: 6/6 (ready)

## Artifacts

- Unity compile: runs/unity-check-2026-07-26t17-43-10-09-00/unity_check.md
- Unity playtest smoke: runs/unity-playtest-2026-07-26t17-43-21-09-00/unity_playtest.md
- Development build: runs/unity-build-windows-dev-2026-07-26t17-43-27-09-00/unity_build.md
- gdx1 probe: runs/gdx-probe-2026-07-26t17-43-50-09-00/gdx_probe.md

## Checks

- [x] Unity compile: runs/unity-check-2026-07-26t17-43-10-09-00/unity_check.md
- [x] Playtest smoke: runs/unity-playtest-2026-07-26t17-43-21-09-00/unity_playtest.md
- [x] Development build: runs/unity-build-windows-dev-2026-07-26t17-43-27-09-00/unity_build.md
- [x] gdx1 probe evidence: runs/gdx-probe-2026-07-26t17-43-50-09-00/gdx_probe.md
- [x] Capture evidence: reviews/captures/screen-2026-06-01t14-51-50-09-00.png
- [x] MVP spec: Assets/_Project/Scripts/Gameplay/TraitorEscapeMvpSpec.md

## Known Limitations

- Readiness `6/6` requires a recorded gdx1 probe, not healthy remote execution.
- Tailscale is reachable, but the current SSH probe is blocked by host-key
  verification. Server and bot soak remain pending outside this build gate.
