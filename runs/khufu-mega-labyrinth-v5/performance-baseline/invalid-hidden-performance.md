# Khufu V5 Windows Player Performance baseline

- Validity: **invalid and excluded**
- Exclusion reason: hidden Player window produced black captures, unavailable render/GPU timing,
  and an implausible `286750` samples in the nominal capture window.
- Replacement: visible-window baseline and independent visible-window final profile.
- Unity: `6000.0.76f1`
- OS: `Windows 11  (10.0.26200)`
- CPU: `Intel(R) Core(TM) Ultra 9 275HX` (24 logical)
- GPU: `NVIDIA GeForce RTX 5090 Laptop GPU` / `Direct3D 11.0 [level 11.1]`
- RAM: `97981 MB`; reported VRAM: `24137 MB`
- Resolution: `1536x1024`, quality `Ultra`
- Procedure: `5s warm-up + 15s participant route + 15s operator route`
- Samples: `286750`
- Frame time median: `0.091 ms`; p95: `0.176 ms`
- CPU frame median: `0.092 ms`; p95: `0.175 ms`
- Main thread median: `0.090 ms`; p95: `0.171 ms`
- Render thread: `unavailable`
- GPU frame: `unavailable`
- Maximum total allocated memory: `111.7 MB`
- Maximum total reserved memory: `220.7 MB`
- Maximum managed memory: `19.8 MB`
- Visible renderers: `781`
- Visible mesh vertices: `23710`
- Visible mesh triangles: `16888`

PROFILE_RESULT: invalid_hidden_window
