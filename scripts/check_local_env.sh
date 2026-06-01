#!/usr/bin/env bash
set -u

failures=0

check_cmd() {
  local name="$1"
  local cmd="$2"

  if command -v "$cmd" >/dev/null 2>&1; then
    printf "ok   %-16s %s\n" "$name" "$(command -v "$cmd")"
  else
    printf "miss %-16s %s\n" "$name" "$cmd"
    failures=$((failures + 1))
  fi
}

check_path() {
  local name="$1"
  local path="$2"

  if [ -e "$path" ]; then
    printf "ok   %-16s %s\n" "$name" "$path"
  else
    printf "miss %-16s %s\n" "$name" "$path"
    failures=$((failures + 1))
  fi
}

printf "channel_play local environment\n"
printf "cwd: %s\n" "$(pwd)"
printf "date: %s\n" "$(date '+%Y-%m-%d %H:%M:%S %Z')"
printf "\n"

printf "system\n"
printf "os: %s %s\n" "$(sw_vers -productName 2>/dev/null || uname -s)" "$(sw_vers -productVersion 2>/dev/null || uname -r)"
printf "arch: %s\n" "$(uname -m)"
printf "cpu: %s\n" "$(sysctl -n machdep.cpu.brand_string 2>/dev/null || printf unknown)"
printf "mem_bytes: %s\n" "$(sysctl -n hw.memsize 2>/dev/null || printf unknown)"
df -h . | awk 'NR==1 || NR==2 {print}'
printf "\n"

printf "required tools\n"
check_cmd "git" git
check_cmd "git-lfs" git-lfs
check_cmd "gh" gh
check_cmd "ffmpeg" ffmpeg
check_cmd "docker" docker
printf "\n"

printf "recommended apps\n"
check_path "Unity Hub" "/Applications/Unity Hub.app"
if find /Applications -maxdepth 6 -name "Unity.app" -print -quit 2>/dev/null | grep -q .; then
  printf "ok   %-16s installed\n" "Unity Editor"
else
  printf "miss %-16s /Applications/**/Unity.app\n" "Unity Editor"
  failures=$((failures + 1))
fi

if find /Applications -maxdepth 3 -name "OBS.app" -print -quit 2>/dev/null | grep -q .; then
  printf "ok   %-16s installed\n" "OBS"
else
  printf "miss %-16s /Applications/OBS.app\n" "OBS"
fi

if find /Applications -maxdepth 3 -name "Blender.app" -print -quit 2>/dev/null | grep -q .; then
  printf "ok   %-16s installed\n" "Blender"
else
  printf "miss %-16s /Applications/Blender.app\n" "Blender"
fi
printf "\n"

printf "git\n"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  printf "ok   repo             %s\n" "$(git rev-parse --show-toplevel)"
else
  printf "miss repo             not initialized\n"
  failures=$((failures + 1))
fi

printf "\n"
if [ "$failures" -eq 0 ]; then
  printf "result: ready\n"
else
  printf "result: needs_setup (%s blocking checks)\n" "$failures"
fi

exit 0
