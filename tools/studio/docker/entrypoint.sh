#!/bin/sh
set -eu

cd /workspace

exec python3 tools/channelctl studio serve "${CHANNEL_PLAY_STUDIO_PORT:-8776}" --host "${CHANNEL_PLAY_STUDIO_HOST:-0.0.0.0}"
