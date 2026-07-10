# Khufu V5 Windows Build Input Binding

- Verdict: **passed**
- Date: `2026-07-11`
- Decision: `KV5-D-013`
- Implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Manifest: [`build-input-binding.json`](build-input-binding.json)
- Manifest SHA256: `b023b46f3fd27a9632f6cab8b9adb9028ddf06971ba95db678fad2e5efa6cc09`

## Why This Binding Exists

The Windows Development Player was built from the committed V5 implementation while project and
package configuration files already had unrelated, uncommitted local changes. Staging those files
would violate worktree ownership, but omitting their state would leave build/performance evidence
under-bound. The committed manifest therefore records and continuously checks their content hashes
without committing the settings themselves.

Official Unity guidance treats Player, Quality, Graphics, and package manifest/lock state as build
inputs. The binding covers:

- `ProjectSettings.asset`
- `EditorBuildSettings.asset`
- `GraphicsSettings.asset`
- `QualitySettings.asset`
- `ProjectVersion.txt`
- `Packages/manifest.json`
- `Packages/packages-lock.json`
- the committed `School_MVP` scene

## Instrumentation Delta

`enableFrameTimingStats` was temporarily changed from `0` to `1` for the profiled Development
Player, then restored so the user's project setting was not left modified by the profiling run.
The manifest binds both states:

- post-build base SHA256: `9f230111f98d29203c5cd40c6f4da2aa53f609dbc1c5abcf776165808c7882e3`
- exact single replacement: `enableFrameTimingStats: 0` -> `enableFrameTimingStats: 1`
- derived build-time SHA256: `95a70db75f3c5bacde2dd6f66d50b54accb8fa28fadf88935af79df30831afd7`

The validator requires exactly one replacement occurrence and recomputes the derived hash from raw
bytes. Any other project-settings drift fails the harness.

## Build Provenance

- Bee input snapshot SHA256:
  `5f8a648b0220775c3d066539f3693f45cd3f70b04104da789e4ad4639dd3780b`
- Normalized Bee build report snapshot SHA256:
  `12a7be792d981fb8ce5f097a7ff61199cccbfb4bcf7712812e24841ed72874bc`
- Raw Bee build report source SHA256:
  `a6deb2684a2701ca33f193d2be82773e28d9827c5db1fa370984f4569d7c4907`
- Proven destination: `Builds/KhufuV5/ChannelPlayKhufuV5.exe`
- Proven variant: `win64_player_development_mono`
- Proven scene: `Assets/_Project/Scenes/School_MVP.unity`

Output hashes remain the same values recorded in the Gate 6 receipt:

- executable: `ab5809518c33adf6dad28c9ffe467d2f78f0c00bf78991fef991a7dd04a8fc48`
- `UnityPlayer.dll`: `376ef4d7595a2d0848e9e3a1c4732fcdca9e33cfb844a002b020e5443cedb9b6`
- `level0`: `8d345bb9150cb20626588f4623212ecc13c3c6c63c67af998591fd8c785bebbc`

## Fail-Closed Checks

The harness now:

1. requires the binding manifest;
2. verifies scene, configuration, package, and provenance hashes;
3. verifies required Bee provenance tokens;
4. recomputes the exact frame-timing override hash;
5. includes the manifest in the harness artifact fingerprint;
6. requires the manifest itself to be committed in `--require-committed` mode;
7. has mutation tests for a missing manifest and a changed bound input.

Project/package settings remain unstaged. That is deliberate: the final claim is bound to their
exact local bytes, while ownership of those unrelated changes remains untouched.

BUILD_INPUT_BINDING_VERDICT: passed
