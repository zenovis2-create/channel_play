# Khufu V5 Gate 6 Acceptance

- Verdict: **passed**
- Tested implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Windows build receipt SHA256: `d1aedeec6200c8b39a1efe56c20abe3b811a0f60ca8743c750152bfa8c3fb29a`
- Frozen budget: `performance-budget.json`, decision `KV5-D-011`
- Baseline validation: `performance-baseline/baseline-validation.md`
- Final validation SHA256: `27ffdb2c61bc23aa6564fbe24b6efe54b00018574a0b619500aa84ac85eac3e5`
- Build: `StandaloneWindows64` Development Player, errors `0`, output `138.57 MB`
- Final samples: `3580`
- Final p95 frame: `8.337 ms` (budget `9.0 ms`)
- Final p95 main/render/GPU: `2.401 / 2.794 / 2.240 ms` (budget `4.5 ms` each)
- Final maximum allocated/reserved/managed: `149.7 / 268.7 / 2.8 MB`
- Final visible renderers/vertices/triangles: `781 / 23710 / 16888`
- 1536x1024 initial and operator PNGs: valid, non-empty, distinct
- Final player log error markers: `0`
- Performance validator mutation tests: `5/5 passed`
- Harness validator regression tests: `9/9 passed`

GATE6_VERDICT: passed
