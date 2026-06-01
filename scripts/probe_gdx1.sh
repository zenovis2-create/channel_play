#!/usr/bin/env bash
set -u

host="${GDX1_HOST:-gdx1}"
user="${GDX1_USER:-zenovis1}"
target="${user}@${host}"

printf "channel_play gdx1 probe\n"
printf "target: %s\n" "$target"
printf "date: %s\n" "$(date '+%Y-%m-%d %H:%M:%S %Z')"
printf "\n"

printf "tailscale\n"
if command -v tailscale >/dev/null 2>&1; then
  tailscale status --json 2>/dev/null \
    | jq -r '.Peer[] | select((.HostName // "") == "gdx1") | "host=\(.HostName) online=\(.Online) os=\(.OS) ips=\(.TailscaleIPs|join(","))"' 2>/dev/null \
    || tailscale status 2>/dev/null | grep -i gdx || true
else
  printf "miss tailscale command\n"
fi
printf "\n"

printf "ssh\n"
ssh -o BatchMode=yes -o ConnectTimeout=8 "$target" '
  printf "host="; hostname
  printf "user="; whoami
  printf "kernel="; uname -srmo
  printf "arch="; uname -m
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    printf "os=%s\n" "$PRETTY_NAME"
  fi
  printf "mem="
  free -h 2>/dev/null | awk "/Mem:/ {print \$2 \" total, \" \$7 \" available\"}" || true
  printf "disk="
  df -h . | tail -1
  printf "gpu="
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -3 || true
  printf "docker="
  docker --version 2>/dev/null || true
' 2>&1
