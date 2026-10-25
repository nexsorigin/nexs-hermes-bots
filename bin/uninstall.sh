#!/bin/bash
# Fully uninstall Hermes and its user LaunchAgents while preserving this Git checkout.
set -euo pipefail

# Keep core macOS tools available even if the Hermes uninstaller changes shell
# startup files or removes a package-managed bin directory during this process.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin${PATH:+:$PATH}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_DOMAIN="gui/$(id -u)"
WATCHER_LABEL='local.hermes.file-watcher'
WATCHER_PLIST="$HOME/Library/LaunchAgents/$WATCHER_LABEL.plist"

if [[ ! -t 0 ]]; then
  echo 'ERROR: Full Hermes uninstall requires an interactive Terminal.' >&2
  exit 1
fi

cat <<'WARNING'
WARNING: This permanently uninstalls Hermes from this user account, including:
  - Hermes Agent and Hermes Desktop (when owned by the Hermes installer)
  - all Hermes profiles, sessions, chats, credentials, secrets, and configuration
  - downloaded Hermes tools, plugins, caches, logs, and other ~/.hermes data
  - Hermes gateway LaunchAgents and the Nex Hermes watcher LaunchAgent

The nexs-hermes-bots Git checkout, its fixtures, logs, and history are preserved.
WARNING
printf 'Continue with the full Hermes uninstall? [y/N] '
IFS= read -r confirmation || confirmation=''
case "$confirmation" in
  [Yy]|[Yy][Ee][Ss]) ;;
  *)
    echo 'Cancelled. Nothing was removed.'
    exit 0 ;;
esac

HERMES_BIN=''
if command -v hermes >/dev/null 2>&1; then
  HERMES_BIN="$(command -v hermes)"
elif [[ -x "$HOME/.hermes/hermes-agent/.hermes/bin/hermes" ]]; then
  HERMES_BIN="$HOME/.hermes/hermes-agent/.hermes/bin/hermes"
fi

echo 'Stopping Hermes services and watcher processes...'
if [[ -f "$SCRIPT_DIR/stop.sh" ]]; then
  if ! /bin/bash "$SCRIPT_DIR/stop.sh"; then
    echo 'WARNING: The normal stop routine reported an error; continuing with LaunchAgent cleanup.' >&2
  fi
fi

unload_and_remove_plist() {
  local plist="$1" label=''
  [[ -f "$plist" || -L "$plist" ]] || return 0
  if [[ -f "$plist" ]]; then
    label=$(/usr/libexec/PlistBuddy -c 'Print :Label' "$plist" 2>/dev/null || true)
  fi
  if [[ -z "$label" ]]; then
    label="$(basename "$plist" .plist)"
  fi
  launchctl bootout "$USER_DOMAIN/$label" 2>/dev/null || true
  rm -f -- "$plist"
  echo "Removed LaunchAgent: $label"
}

# Remove the project watcher first so it cannot restart while Hermes is removed.
unload_and_remove_plist "$WATCHER_PLIST"

if [[ -n "$HERMES_BIN" && -x "$HERMES_BIN" ]]; then
  echo 'Running the official Hermes full uninstall...'
  "$HERMES_BIN" uninstall --full --yes
elif [[ ! -e "$HOME/.hermes" && ! -e "$HOME/.local/bin/hermes" && \
        ! -L "$HOME/.local/bin/hermes" && ! -e '/Applications/Hermes.app' && \
        ! -e "$HOME/Applications/Hermes.app" ]]; then
  echo 'Hermes CLI and primary installation paths are already absent; continuing residual cleanup.'
else
  echo 'ERROR: Hermes CLI was not found; refusing to guess at installation-owned files.' >&2
  echo 'The Nex Hermes watcher LaunchAgent was removed, but Hermes itself was not uninstalled.' >&2
  exit 1
fi

# The official uninstaller owns application/data removal. Clean up any residual
# user LaunchAgent definitions so no Hermes service can be relaunched.
shopt -s nullglob
for plist in \
  "$HOME/Library/LaunchAgents"/ai.hermes*.plist \
  "$HOME/Library/LaunchAgents"/io.nousresearch.hermes*.plist \
  "$HOME/Library/LaunchAgents"/com.nousresearch.hermes*.plist
do
  unload_and_remove_plist "$plist"
done
shopt -u nullglob

remaining=0
for path in \
  "$HOME/.hermes" \
  "$HOME/.local/bin/hermes" \
  '/Applications/Hermes.app' \
  "$HOME/Applications/Hermes.app"
do
  if [[ -e "$path" || -L "$path" ]]; then
    if (( remaining == 0 )); then
      echo 'ERROR: Hermes full uninstall returned, but these installation paths remain:' >&2
    fi
    printf '  %s\n' "$path" >&2
    remaining=1
  fi
done

if (( remaining != 0 )); then
  echo 'Review the official uninstaller output above. No unverified paths were deleted.' >&2
  exit 1
fi

echo 'Hermes, its user data, and Hermes-related LaunchAgents were removed.'
echo "Preserved project checkout: $PROJECT_ROOT"
