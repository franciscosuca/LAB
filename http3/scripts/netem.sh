#!/usr/bin/env bash
# Manually apply/remove tc netem loss+delay on an interface (default: lo).
# `httpbench bench --loss/--delay` already does this automatically for the
# duration of a benchmark run - use this script instead when you want the
# impairment to persist across multiple manual runs, curl, or a browser.
#
# Linux only. Requires NET_ADMIN (root/sudo, or --cap-add=NET_ADMIN in a
# container).
#
# Usage:
#   sudo scripts/netem.sh add [interface] [loss_pct] [delay_ms]
#   sudo scripts/netem.sh del [interface]
#
# Examples:
#   sudo scripts/netem.sh add lo 3 40      # 3% loss, +40ms delay on loopback
#   sudo scripts/netem.sh del lo
set -euo pipefail

action="${1:-}"
iface="${2:-lo}"
loss="${3:-0}"
delay="${4:-0}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "error: tc netem is Linux-only. Run this inside a Linux VM/container." >&2
  exit 1
fi

case "$action" in
  add)
    args=(netem)
    [[ "$delay" != "0" ]] && args+=(delay "${delay}ms")
    [[ "$loss" != "0" ]] && args+=(loss "${loss}%")
    if [[ ${#args[@]} -eq 1 ]]; then
      echo "error: pass a nonzero loss and/or delay" >&2
      exit 1
    fi
    tc qdisc add dev "$iface" root "${args[@]}"
    echo "Applied to $iface: ${args[*]}"
    ;;
  del)
    tc qdisc del dev "$iface" root
    echo "Removed impairment from $iface"
    ;;
  *)
    echo "usage: $0 {add|del} [interface] [loss_pct] [delay_ms]" >&2
    exit 1
    ;;
esac
