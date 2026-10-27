#!/bin/bash
set -euo pipefail
LABEL='local.hermes.file-watcher'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCHER="$SCRIPT_DIR/run.sh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ ! -f "$SCRIPT_DIR/watcher.py" || ! -x "$DIR/.venv/bin/python" ]]; then
  echo "ERROR: First set up $SCRIPT_DIR/watcher.py and $DIR/.venv" >&2
  exit 1
fi
if [[ ! -f "$LAUNCHER" ]]; then
  echo "ERROR: run.sh must be alongside this installer in $SCRIPT_DIR." >&2
  exit 1
fi
if [[ ! -f "$SCRIPT_DIR/profiles.py" || ! -s "$DIR/shared/TEAM.md" || ! -s "$DIR/config.json" ]]; then
  echo "ERROR: Shared team setup missing. Run './bots init' first." >&2
  exit 1
fi
if ! /usr/bin/python3 "$SCRIPT_DIR/profiles.py" --configured all >/dev/null; then
  echo "ERROR: Invalid $DIR/config.json" >&2
  exit 1
fi
mkdir -p "$DIR/logs" "$DIR/fixtures" "$HOME/Library/LaunchAgents"
chmod 700 "$LAUNCHER"

# Write property list with proper escaping (not a hand-edited XML template).
/usr/bin/python3 - "$PLIST" "$DIR" "$LABEL" "$LAUNCHER" <<'PY'
import plistlib, sys
from pathlib import Path
plist, root, label, launcher = sys.argv[1:]
config = {
  'Label': label,
  'ProgramArguments': ['/bin/bash', launcher],
  'RunAtLoad': True,
  'KeepAlive': True,
  'ThrottleInterval': 30,
  'WorkingDirectory': root,
  'StandardOutPath': str(Path(root) / 'logs' / 'watcher-service.log'),
  'StandardErrorPath': str(Path(root) / 'logs' / 'watcher-service-error.log'),
  'ProcessType': 'Background',
}
with open(plist, 'wb') as f:
    plistlib.dump(config, f)
PY
chmod 600 "$PLIST"
DOMAIN="gui/$(id -u)"
# Allow re-running installer to update an existing service.
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl enable "$DOMAIN/$LABEL"
launchctl kickstart -k "$DOMAIN/$LABEL"
echo "Installed $DOMAIN/$LABEL"
echo "Logs: $DIR/logs/watcher-service.log"
echo "Check service: launchctl print $DOMAIN/$LABEL"
echo "Stop: launchctl bootout $DOMAIN/$LABEL"
echo "Resume: launchctl bootstrap $DOMAIN '$PLIST'"
echo 'Hermes Desktop is not launched. Configured handoffs are handled by the watcher.'
