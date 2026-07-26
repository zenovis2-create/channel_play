# Khufu V6 Frozen Inputs Baseline

- Captured: `2026-07-11 Asia/Seoul`
- Git HEAD: `9f4158673f9b4cdcdea94c74b71638413c5d77fe`
- Scope: pre-implementation hashes for files V6 is forbidden to edit

| SHA256 | Path |
| --- | --- |
| `0a9f7a1f071db40fbab05e955e41acfbfa98c6b22aa7ee9d059f454392184faf` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs` |
| `405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs` |
| `c06e70f287b97cfdeaf8d8871f2c1387cbf1481c6f03db2a9c0f29d010051885` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5PlayModeProbe.cs` |
| `b4ec09ed37c8ad1b7597528a3a8ced42ae7a8613436cdc31a9b1e609a6e85c3c` | `Assets/_Project/Scripts/Editor/ChannelPlayPyramidReferenceMatchedV4Builder.cs` |
| `99daf7abb0262b49335b1af247864ef150544cd273b154d7fed65d5d8d914922` | `Assets/_Project/Scripts/Gameplay/TraitorEscapeMapBindings.cs` |
| `7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38` | `Packages/manifest.json` |
| `d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e` | `Packages/packages-lock.json` |
| `fbf0856b7693639a5388ae693a455baaad354c1d8dc548601de3dc61c4ab12c3` | `ProjectSettings/GraphicsSettings.asset` |
| `bbc1846ac2fa9fdaa62fb1d1425c30ae0a30a98972eb158e8f0bcd9f862f70c4` | `ProjectSettings/QualitySettings.asset` |

The final V6 receipt must reproduce these hashes. A mismatch blocks completion unless a later
explicit decision supersedes this baseline.

## Pre-existing Index Divergences

The package files were already modified in the local worktree before V6 and are bound by the
accepted V5 `build-input-binding.json`. They remain forbidden to stage in the V6 commit. The table
records both the unchanged local build-input hash above and the unchanged Git index hash so staged
verification can distinguish inherited dirty state from V6 drift.

| Index SHA256 | Bound worktree SHA256 | Path |
| --- | --- | --- |
| `e623e41b2bbade3ebaacbb32c768949499e6bedce156a66e5dcb4e115380437b` | `7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38` | `Packages/manifest.json` |
| `d43b65593a5c7eadf0070d8715f456775de999e03e6bad1754540c1c2df45171` | `d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e` | `Packages/packages-lock.json` |
