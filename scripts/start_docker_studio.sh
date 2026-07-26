#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

DETACH=0
if [ "${1:-}" = "--detach" ]; then
  DETACH=1
  shift
fi

HOST_RUNNER_PORT="${CHANNEL_PLAY_HOST_RUNNER_PORT:-8788}"
STUDIO_PORT="${CHANNEL_PLAY_STUDIO_PORT:-8776}"
HOST_RUNNER_LOG="memory/company/secrets/host_runner.log"
HOST_RUNNER_PID="memory/company/secrets/host_runner.pid"
HOST_RUNNER_NAME="${CHANNEL_PLAY_HOST_RUNNER_PM2_NAME:-channel-play-host-runner-$HOST_RUNNER_PORT}"

python3 tools/channelctl host-runner token >/dev/null

if command -v pm2 >/dev/null 2>&1; then
  if pm2 describe "$HOST_RUNNER_NAME" >/dev/null 2>&1; then
    CHANNEL_PLAY_RUNNER_TOKEN_FILE="${CHANNEL_PLAY_RUNNER_TOKEN_FILE:-memory/company/secrets/host_runner.token}" \
      pm2 restart "$HOST_RUNNER_NAME" --update-env >/dev/null
  else
    CHANNEL_PLAY_RUNNER_TOKEN_FILE="${CHANNEL_PLAY_RUNNER_TOKEN_FILE:-memory/company/secrets/host_runner.token}" \
      pm2 start tools/channelctl \
        --name "$HOST_RUNNER_NAME" \
        --cwd "$ROOT_DIR" \
        --interpreter python3 \
        -- host-runner serve "$HOST_RUNNER_PORT" >/dev/null
  fi
  pm2 pid "$HOST_RUNNER_NAME" > "$HOST_RUNNER_PID" || true
  pm2 save >/dev/null || true
else
  if [ -f "$HOST_RUNNER_PID" ]; then
    OLD_PID="$(cat "$HOST_RUNNER_PID" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
      kill "$OLD_PID" >/dev/null 2>&1 || true
      sleep 1
    fi
  fi
  CHANNEL_PLAY_RUNNER_TOKEN_FILE="${CHANNEL_PLAY_RUNNER_TOKEN_FILE:-memory/company/secrets/host_runner.token}" \
    nohup python3 tools/channelctl host-runner serve "$HOST_RUNNER_PORT" > "$HOST_RUNNER_LOG" 2>&1 &
  echo "$!" > "$HOST_RUNNER_PID"
fi

sleep 2
if ! lsof -nP -iTCP:"$HOST_RUNNER_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "host-runner did not start on port $HOST_RUNNER_PORT" >&2
  if command -v pm2 >/dev/null 2>&1; then
    pm2 logs "$HOST_RUNNER_NAME" --nostream --lines 80 >&2 || true
  else
    sed -n '1,80p' "$HOST_RUNNER_LOG" >&2 || true
  fi
  exit 1
fi

if [ "$DETACH" -eq 1 ]; then
  CHANNEL_PLAY_STUDIO_PORT="$STUDIO_PORT" \
  CHANNEL_PLAY_HOST_RUNNER_URL="${CHANNEL_PLAY_HOST_RUNNER_URL:-http://host.docker.internal:$HOST_RUNNER_PORT}" \
  docker compose -f docker-compose.studio.yml up --build -d
else
  CHANNEL_PLAY_STUDIO_PORT="$STUDIO_PORT" \
  CHANNEL_PLAY_HOST_RUNNER_URL="${CHANNEL_PLAY_HOST_RUNNER_URL:-http://host.docker.internal:$HOST_RUNNER_PORT}" \
  docker compose -f docker-compose.studio.yml up --build
fi
