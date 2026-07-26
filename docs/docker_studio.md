# Channel Play Docker Studio

Date: 2026-06-03

## Recommended Operating Model

Channel Play Studio can run in Docker, but the container is only the control plane:

- Studio container: web UI, state API, job ledger viewer, artifact preview
- Host runner: local execution bridge for `tools/channelctl` commands
- gdx1 workers: long-running or remote headless work
- Mac Studio host: Unity, Blender, Codex App-style visual review, local credentials

Do not put every capability inside the Studio container. Unity Editor, Blender GUI, screen capture, and desktop agent tools need host access and should run through the host runner or a dedicated worker.

## Security Rules

- Do not mount `/var/run/docker.sock` into the Studio container.
- Do not run the Studio container as a privileged container.
- Keep the bind mount scoped to this repository.
- Publish the Studio port on host loopback only; do not expose the admin console to the LAN.
- Use the host-runner token secret file instead of passing the token through the browser.
- Keep `memory/company/secrets/` out of Git.
- Treat a Docker/agent control plane as an admin console.

## Files

- `docker-compose.studio.yml`
- `docker/studio/Dockerfile`
- `tools/studio/docker/entrypoint.sh`
- `tools/studio/host_runner.py`
- `tools/studio/docker_runtime.py`
- `scripts/start_docker_studio.sh`

## Start

```bash
scripts/start_docker_studio.sh
```

For background operation:

```bash
CHANNEL_PLAY_STUDIO_PORT=8778 CHANNEL_PLAY_HOST_RUNNER_PORT=8789 scripts/start_docker_studio.sh --detach
```

Then open:

```text
http://127.0.0.1:8776/#runtime
```

Docker Compose binds this port to `127.0.0.1` on the host. Use an authenticated
reverse proxy or tunnel for deliberate remote access; do not widen the Compose
binding directly.

If `CHANNEL_PLAY_STUDIO_PORT=8778` is used, open:

```text
http://127.0.0.1:8778/#runtime
```

The script creates `memory/company/secrets/host_runner.token`, starts `tools/channelctl host-runner serve <port>` with `pm2` when available, verifies the runner port, and then starts Docker Compose. If `pm2` is not installed, it falls back to `nohup`.

## Manual Start

```bash
python3 tools/channelctl host-runner token
python3 tools/channelctl host-runner serve 8788
docker compose -f docker-compose.studio.yml up --build
```

## Expected Runtime State

In the Studio UI:

- `Studio`: Docker container
- `Host Runner`: connected
- `Token`: configured
- `Docker Socket`: blocked

If `Host Runner` is blocked, UI state and previews still work, but command buttons cannot execute real host work until the runner is reachable.
