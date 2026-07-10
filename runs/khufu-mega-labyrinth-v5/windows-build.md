# Khufu V5 Windows Development Player Build

- Verdict: **passed**
- Build target: `StandaloneWindows64` Development Player
- Unity: `6000.0.76f1`
- Scene: `Assets/_Project/Scenes/School_MVP.unity`
- Output: `Builds/KhufuV5/ChannelPlayKhufuV5.exe`
- Build job: `build-c4886cfc96`
- Duration: `31.487 seconds`
- Total size: `138.57 MB`
- Errors: `0`
- Warnings: `185`
- Player executable SHA256: `ab5809518c33adf6dad28c9ffe467d2f78f0c00bf78991fef991a7dd04a8fc48`
- UnityPlayer SHA256: `376ef4d7595a2d0848e9e3a1c4732fcdca9e33cfb844a002b020e5443cedb9b6`
- Built level SHA256: `8d345bb9150cb20626588f4623212ecc13c3c6c63c67af998591fd8c785bebbc`
- Scene source SHA256: `7606cfb305d7b0269af5db6f35544583765a56ebee2bb68844b5b239bf5e65ff`
- Frame Timing Stats: `enabled`

## Target Machine

- Host: `ZENOVIS`
- CPU: `Intel(R) Core(TM) Ultra 9 275HX`, 24 cores / 24 logical processors
- GPU: `NVIDIA GeForce RTX 5090 Laptop GPU`, driver `32.0.15.9611`
- RAM: `95.7 GB`
- OS: `Microsoft Windows 11 Pro 10.0.26200`, build `26200`
- Display during inventory: `3840x2400`
- Profile window: `1536x1024`, `Ultra`, D3D11, 120fps target, vSync off

## Warning Classification

All sampled build warnings originate under
`Packages/com.unity.ai.inference/Runtime/Core/Resources/Sentis/PixelShaders/` and report D3D11
integer divide/modulus or signed/unsigned shader compiler diagnostics. No V5 script, scene, or
material error was emitted. The package warnings are retained as a non-blocking upstream risk;
package source was not modified.

## Player Runs

- Hidden-window diagnostic: **invalid**, because captures were black and render/GPU timings were
  unavailable. The compact failure receipt is retained as
  `performance-baseline/invalid-hidden-performance.md`; its 1.5 GB raw file was discarded.
- Visible baseline: **recorded and validated**, 3577 samples; see
  `performance-baseline/baseline-performance.md` and `performance-baseline/baseline-validation.md`.
- Frozen budget: `performance-budget.json`, decision `KV5-D-011`.
- Visible final: **passed**, 3580 samples; see `performance-final/final-performance.md` and
  `performance-final/validation.md`.

WINDOWS_BUILD_VERDICT: passed
