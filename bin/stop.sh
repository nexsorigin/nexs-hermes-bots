#!/bin/bash
# Stop the Nexs Hermes Bots watcher, Hermes Gateway, and available local model services on macOS.
# Does not remove LaunchAgent files, delete logs, or quit Hermes Desktop.
set -u

WATCHER_LABEL="local.hermes.file-watcher"
WATCHER_PLIST="$HOME/Library/LaunchAgents/${WATCHER_LABEL}.plist"
USER_DOMAIN="gui/$(id -u)"

printf '%s\n' 'Stopping Hermes background services...'

# Unload service first, to prevent launchd from restarting the watcher.
if launchctl print "$USER_DOMAIN/$WATCHER_LABEL" >/dev/null 2>&1; then
  echo 'Stopping Nexs Hermes Bots watcher LaunchAgent...'
  if ! launchctl bootout "$USER_DOMAIN/$WATCHER_LABEL"; then
    echo 'WARNING: Could not unload watcher LaunchAgent.' >&2
  fi
else
  echo 'Hermes watcher LaunchAgent is not loaded.'
fi

# Look for manually launched watchers. Limit matches to this user's processes
# whose command line specifically contains the Hermes watcher script.
echo 'Checking for remaining Hermes watcher processes...' 
self_pid=$$
parent_pid=$PPID
pids=''
while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  [[ "$pid" == "$self_pid" || "$pid" == "$parent_pid" ]] && continue
  cmd=$(ps -p "$pid" -o command= 2>/dev/null || true)
  if [[ "$cmd" == *"watcher.py"* && "$cmd" != *"grep "* ]]; then
    pids="${pids}${pids:+ }${pid}"
  fi
done < <(pgrep -u "$(id -u)" -f 'watcher\.py' 2>/dev/null || true)

if [[ -n "$pids" ]]; then
  printf 'Sending SIGTERM to watcher PID(s): %s\n' "$pids"
  for pid in $pids; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  for ((i=0; i<10; i++)); do
    remaining=0
    for pid in $pids; do
      if kill -0 "$pid" 2>/dev/null; then remaining=1; fi
    done
    (( remaining == 0 )) && break
    sleep 1
  done
  for pid in $pids; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "WARNING: Watcher PID $pid has not stopped; not force-killing it." >&2
    fi
  done
else
  echo 'No remaining Hermes watcher processes found.'
fi

# Stop the gateway only after the watcher is stopped, to avoid new dispatches.
echo 'Stopping Hermes Gateway...'
if ! command -v hermes >/dev/null 2>&1; then
  # macOS login shell may have a different PATH; check known installation.
  HERMES_BIN="$HOME/.hermes/hermes-agent/.hermes/bin/hermes"
  if [[ -x "$HERMES_BIN" ]]; then
    "$HERMES_BIN" gateway stop || echo 'WARNING: Hermes Gateway stop failed.' >&2
  elif [[ ! -e "$HOME/.hermes" ]]; then
    echo 'Hermes CLI and home are absent; Gateway is already uninstalled.'
  else
    echo 'ERROR: Hermes home exists but its CLI was not found. Gateway status is unknown.' >&2
    exit 1
  fi
else
  hermes gateway stop || echo 'WARNING: Hermes Gateway stop failed.' >&2
fi

printf '\n%s\n' 'Service status (for verification):'
if launchctl print "$USER_DOMAIN/$WATCHER_LABEL" >/dev/null 2>&1; then
  echo 'Watcher LaunchAgent: still loaded (review errors above)'
else
  echo 'Watcher LaunchAgent: unloaded'
fi
if command -v hermes >/dev/null 2>&1; then
  hermes gateway status || true
fi

# Mirror init's guarded service checks. Missing runtimes, formulae, and models are
# skipped; model-service inspection or shutdown errors never block this routine.
echo 'Stopping available local model services...'
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ -f "$SCRIPT_DIR/model.py" ]]; then
  /usr/bin/python3 "$SCRIPT_DIR/model.py" stop || \
    echo 'WARNING: Local model service cleanup could not be completed; continuing.' >&2
else
  echo 'Model service cleanup skipped: helper is unavailable.'
fi

printf '\n%s\n' 'Stop routine complete. Check the service status above to verify shutdown. Logs and service configurations were preserved.'
