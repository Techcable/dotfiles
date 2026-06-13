#!/usr/bin/env bash
# PostToolUse(Bash) hook. When the agent runs a command against an ix builder
# over ssh, snapshot the jj workspace that command touched on the remote, so
# remote edits land in jj history like the local PreToolUse `jj util snapshot`.
# Hooks run on this Mac, never on the builder, so this reaches over with an
# extra ssh. Never blocks: always exits 0.
# NOTE: superseded by the node-side ~/.config/zsh/local.zsh EXIT-trap once that
# home-manager change is deployed (it uses the real remote $PWD, no parsing).
# Delete this hook then.
set -uo pipefail

builders=(nicholas-compute-1)

payload=$(jq -r '.tool_input.command // empty') || exit 0
[ -n "$payload" ] || exit 0

for host in "${builders[@]}"; do
  # Require an actual ssh to the host, not a mere mention (echo, file content…).
  case $payload in
    *ssh*"$host"*) ;;
    *) continue ;;
  esac

  # Scope cd-detection to the REMOTE payload (everything after the host token),
  # so a local `cd` before the ssh isn't mistaken for the remote workspace.
  remote=${payload#*"$host"}
  # Use the LAST `cd <target>` (where the command ended up); fall back to repo root.
  ws=$(printf '%s\n' "$remote" \
    | grep -oE "cd[[:space:]]+[^[:space:];&|)\"']+" \
    | tail -1 | sed -E 's/^cd[[:space:]]+//')
  [ -n "$ws" ] || ws='~/git/ix'

  # Leave $ws unquoted remotely so the remote shell expands a leading ~.
  ssh "$host" "cd $ws 2>/dev/null && jj util snapshot >/dev/null 2>&1 || true" \
    >/dev/null 2>&1 || true
done
exit 0
