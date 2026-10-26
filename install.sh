#!/usr/bin/env bash
# hermes-tui-minimal installer: skins + shell wrapper + config keys + apply.py
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ROOT="${HERMES_AGENT_ROOT:-$HERMES_HOME/hermes-agent}"

if [ ! -d "$ROOT/ui-tui/src" ]; then
  echo "hermes-tui-minimal: no Hermes source checkout at $ROOT (set HERMES_AGENT_ROOT)" >&2
  exit 1
fi
command -v hermes >/dev/null || { echo "hermes-tui-minimal: 'hermes' not on PATH" >&2; exit 1; }

mkdir -p "$HERMES_HOME/skins"
cp "$HERE"/skins/*.yaml "$HERMES_HOME/skins/"
echo "skins -> $HERMES_HOME/skins/"

# shell wrapper (bash or zsh), once
RC="$HOME/.bashrc"; [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = zsh ] && RC="$HOME/.zshrc"
if ! grep -q "hermes-minimal-ui" "$RC" 2>/dev/null; then
  { echo; echo "export HERMES_TUI_MINIMAL=\"$HERE\""; cat "$HERE/shell/hermes-wrapper.sh"; } >> "$RC"
  echo "wrapper -> $RC"
else
  echo "wrapper already in $RC"
fi

set_key() { hermes config set "$@" >/dev/null 2>&1 || hermes config set "$@" --force >/dev/null 2>&1 || echo "  (could not set $1 — set it in config.yaml)"; }
set_key display.interface tui
set_key display.skin quiet-ansi
set_key display.tui_statusbar bottom
set_key display.tui_native false
set_key display.tui_compact true
set_key display.mouse_tracking all
set_key display.resume_display minimal
set_key display.status_bar.fields '["model","context_detail","git_branch"]'
set_key display.turn_summary false
set_key display.turn_completion_explainer false
set_key display.credits_notices false
set_key display.details_mode collapsed
echo "config keys set"

python3 "$HERE/apply.py"
echo "done — open a new shell and run: hermes   (first launch rebuilds the TUI, ~1 min)"
