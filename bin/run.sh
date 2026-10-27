#!/bin/bash
# launchd entrypoint for Hermes watcher. No Hermes Desktop required.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCHER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.hermes/hermes-agent/.hermes/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

if ! command -v hermes >/dev/null 2>&1; then
  echo "ERROR: 'hermes' is not on PATH" >&2
  exit 1
fi
if [[ ! -f "$SCRIPT_DIR/watcher.py" || ! -x "$WATCHER_DIR/.venv/bin/python" ]]; then
  echo "ERROR: watcher or virtualenv is missing under $WATCHER_DIR" >&2
  exit 1
fi

# The launchd label prevents duplicate launchd instances. This additionally
# removes an older manually-started Hermes watcher, not unrelated Python jobs.
stop_existing_watchers() {
  local pid attempt still_running
  local pids=''
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && pids="${pids}${pids:+ }${pid}"
  done < <(/usr/bin/python3 - <<'PYSCAN'
import os, re, subprocess
output = subprocess.check_output(["/bin/ps", "-axo", "pid=,command="], text=True)
for row in output.splitlines():
    match = re.match(r"\s*(\d+)\s+(.*)", row)
    if not match:
        continue
    pid, command = int(match[1]), match[2]
    if pid == os.getpid() or " -c " in command:
        continue
    # Require the actual Python watcher script argument, not just a text match
    # to a different program, such as the install script or gateway process.
    if re.search(r"(?:^|/)python(?:3(?:\.\d+)?)?\s+(?:-u\s+)?(?:\S*/)?watcher\.py(?:\s|$)", command):
        print(pid)
PYSCAN
  )
  if [[ -z "$pids" ]]; then
    echo 'No previous Hermes watcher process found.'
    return
  fi
  printf 'Stopping existing Hermes watcher PID(s): %s\n' "$pids"
  for pid in $pids; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  for attempt in {1..20}; do
    still_running=0
    for pid in $pids; do
      if kill -0 "$pid" 2>/dev/null; then
        still_running=1
      fi
    done
    (( still_running == 0 )) && break
    sleep 0.5
  done
  for pid in $pids; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "ERROR: Existing watcher PID $pid did not stop cleanly. Refusing duplicate launch." >&2
      exit 1
    fi
  done
  echo 'Previous watcher stopped.'
}

# Gateway is a separate, launchd-managed Hermes service. `ensure` checks it.
# A healthy gateway does not guarantee model-provider availability.
streak=0
start=$SECONDS
printf '[%s] Checking Hermes gateway readiness (headless)...\n' "$(date)"
while (( SECONDS - start < 120 )); do
  result="$(hermes gateway ensure --json --timeout 10 2>/dev/null || true)"
  if printf '%s' "$result" | /usr/bin/python3 -c 'import json,sys
try:
    data=json.load(sys.stdin)
    sys.exit(0 if data.get("state")=="ready" else 1)
except (ValueError, TypeError):
    sys.exit(1)' ; then
    streak=$((streak + 1))
    echo "Gateway ready check $streak/3"
    if (( streak >= 3 )); then
      break
    fi
  else
    streak=0
    echo 'Gateway not ready; checking again...'
  fi
  sleep 3
done
if (( streak < 3 )); then
  echo 'ERROR: Gateway not stably ready. Watcher not started. launchd will retry.' >&2
  exit 1
fi

stop_existing_watchers
cd "$WATCHER_DIR"
EXPAT_LIB="$(/opt/homebrew/bin/brew --prefix expat 2>/dev/null)/lib" || true
if [[ -d "$EXPAT_LIB" ]]; then
  export DYLD_LIBRARY_PATH="$EXPAT_LIB${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
export PYTHONUNBUFFERED=1
printf '[%s] Hermes ready; starting watcher LIVE (new events plus unseen existing handoffs).\n' "$(date)"

# launchd already captures watcher stdout/stderr; do not duplicate bot logs
# by tailing them into watcher-service.log. Use `./bots logs` interactively.
mkdir -p "$WATCHER_DIR/logs"
exec "$WATCHER_DIR/.venv/bin/python" -u "$SCRIPT_DIR/watcher.py" --live --scan-existing
