#!/usr/bin/env bash
set -u

project_root="${CHANNEL_PLAY_ROOT:-/Volumes/AI2/channel_play}"
unity_bin="${UNITY_BIN:-/Applications/Unity/Hub/Editor/6000.0.76f1/Unity.app/Contents/MacOS/Unity}"
log_file="${UNITY_CREATE_LOG:-/tmp/channel_play_unity_create.log}"

printf "channel_play Unity project bootstrap\n"
printf "project_root: %s\n" "$project_root"
printf "unity_bin: %s\n" "$unity_bin"
printf "log_file: %s\n" "$log_file"
printf "\n"

if [ ! -x "$unity_bin" ]; then
  printf "error: Unity binary not executable: %s\n" "$unity_bin"
  exit 2
fi

"$unity_bin" \
  -quit \
  -batchmode \
  -nographics \
  -createProject "$project_root" \
  -logFile "$log_file"

exit_code=$?

printf "\nUnity exit_code=%s\n" "$exit_code"
if [ "$exit_code" -ne 0 ]; then
  printf "last log lines:\n"
  tail -80 "$log_file" 2>/dev/null || true
  exit "$exit_code"
fi

printf "created or opened Unity project successfully\n"
