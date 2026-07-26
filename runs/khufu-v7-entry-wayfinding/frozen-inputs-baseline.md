# Khufu V7 Frozen Inputs Baseline

- Captured: `2026-07-11 Asia/Seoul`
- Git HEAD: `c7955d008bdd7fc8b64b79c9a2f23b68eb4c5375`
- Current scene SHA256: `09c8083647f1476e72acd3c0176496e3b6a2742a66e6c5e39ee5fa7df66bb95b`
- Frozen V6 visual signature: `b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530`
- Frozen V6 root metrics: `renderers=11 vertices=520 triangles=404 colliders=0`
- Frozen full-map metrics before V7: `renderers=795 vertices=23776 triangles=16508 colliders=441`

## Forbidden Inputs

| SHA256 | Path |
| --- | --- |
| `0a9f7a1f071db40fbab05e955e41acfbfa98c6b22aa7ee9d059f454392184faf` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs` |
| `405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs` |
| `c06e70f287b97cfdeaf8d8871f2c1387cbf1481c6f03db2a9c0f29d010051885` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5PlayModeProbe.cs` |
| `ffa6fa51a20074760181db6c87319f2aad5afca443e37f80da657b17759c75f2` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs` |
| `6ab23d70ce11c8c8e69352937150599352a821db55426e150935e0fec2a3cf1c` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs` |
| `6c376fe033861dc16b9bc1b9edfd94ec977954897fd67b5a137e1a5b4f9d609e` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceScreenshotExporter.cs` |
| `90d55489833a6a24ae493282d0b85b41a3fa5fca60667013f229a6eb84464df3` | `Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6PlayModeRegressionRunner.cs` |
| `c8da3f34b0f65c4d14ead6f60e8b928063bd0b41c9e7a429bc8ef2a56ec9cd72` | `Assets/_Project/Materials/KhufuV6/V6_Scan_Inlay.mat` |
| `99daf7abb0262b49335b1af247864ef150544cd273b154d7fed65d5d8d914922` | `Assets/_Project/Scripts/Gameplay/TraitorEscapeMapBindings.cs` |
| `ac076ff0e37595224fef7e61cb4907301e4203a74c9c676cb5add78e9d0ba9e2` | `Assets/_Project/Scripts/Gameplay/TraitorEscapeMvpSession.cs` |
| `7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38` | `Packages/manifest.json` |
| `d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e` | `Packages/packages-lock.json` |
| `fbf0856b7693639a5388ae693a455baaad354c1d8dc548601de3dc61c4ab12c3` | `ProjectSettings/GraphicsSettings.asset` |
| `bbc1846ac2fa9fdaa62fb1d1425c30ae0a30a98972eb158e8f0bcd9f862f70c4` | `ProjectSettings/QualitySettings.asset` |

## Intentional Shared-Code Inputs

Only the three files below may change outside new V7-owned files. Their baseline hashes make the
shared delta auditable.

| Baseline SHA256 | Path | Allowed delta |
| --- | --- | --- |
| `a4e2122aad57587ad6c649b7740026bcc6cb55cbb7dfd88b311c881233a1ccb5` | `Assets/_Project/Scripts/Player/ChannelFollowCamera.cs` | execution order plus V7-configurable offset and look-ahead APIs |
| `9d6aa25ffa77ee2fb040fa9eb14bf0c353c1743b65a7dd6a34dcddada36c5e2a` | `Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs` | execution order, two exact pylon candidates, diagnostics, and restorable pylon renderer disabling |
| `0c3bda152cd436c54e1de2e3b2748246bdebb65fcef842f040e5600a74da454a` | `Assets/_Project/Scripts/Editor/ChannelPlayCameraCutawayValidator.cs` | exact-pylon disable/restore and unrelated-pylon regression |

## Pre-existing Index Divergences

The package files remain local build inputs inherited from V5/V6 and must not be staged by V7.

| Index SHA256 | Bound worktree SHA256 | Path |
| --- | --- | --- |
| `e623e41b2bbade3ebaacbb32c768949499e6bedce156a66e5dcb4e115380437b` | `7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38` | `Packages/manifest.json` |
| `d43b65593a5c7eadf0070d8715f456775de999e03e6bad1754540c1c2df45171` | `d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e` | `Packages/packages-lock.json` |
