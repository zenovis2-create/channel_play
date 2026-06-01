# channel_play Setup Status

Updated: 2026-06-01 13:18 KST

## Completed

- Git repository initialized on `main`
- Git LFS installed with local hooks
- Unity Hub installed
- Unity Editor `6000.0.76f1` arm64 installed
- Unity license activated
- Unity project created in `/Volumes/AI2/channel_play`
- OBS installed
- Blender installed
- Unity `_Project` folder structure created
- GitHub remote connected: `https://github.com/zenovis2-create/channel_play`
- Local `main` pushed to `origin/main`
- Initial Unity scenes created:
  - `Boot`
  - `MainMenu`
  - `Lobby`
  - `School_MVP`
  - `OperatorView`
  - `OverlayTest`
- Initial blockout materials created
- Build Settings scene list configured
- First playable slice created in `School_MVP`
- `MVP_Player` prefab created
- `ChannelPlayerController` added
- `ChannelFollowCamera` added
- `.gitignore` added for Unity/macOS/context-mode generated files
- `.gitattributes` added for Unity asset LFS tracking
- Environment scripts added:
  - `scripts/check_local_env.sh`
  - `scripts/probe_gdx1.sh`
  - `scripts/create_unity_project.sh`
- Implementation plan added:
  - `docs/implementation_plan.md`

## Current Blocker

gdx1 is visible on Tailscale, but SSH authentication is not configured from this Mac.

Observed:

```text
zenovis1@gdx1: Permission denied (publickey,password).
```

## Next Action

1. Register this Mac Studio SSH public key on gdx1, or enable Tailscale SSH.
2. Open `School_MVP` in Unity and verify movement with WASD/arrow keys, Shift, Space.
3. Add Unity Netcode packages after confirming package versions.
4. Start point/shop/item core loop.

## gdx1 Status

gdx1 is visible on Tailscale, but SSH authentication is not configured from this Mac.

```text
zenovis1@gdx1: Permission denied (publickey,password).
```
