# hermes-tui-minimal: shell wrapper. Source this from ~/.bashrc / ~/.zshrc.
# Re-applies the patches before every launch and around `hermes update`.
# >>> hermes-minimal-ui >>>  (keeps the minimal TUI look across `hermes update`)
hermes() {
  local mu="${HERMES_TUI_MINIMAL:-$HOME/.hermes/tui-minimal}/apply.py" rc
  if [ "$1" = "update" ]; then
    # Update from a clean tree (no autostash / restore prompt / conflicts), then re-apply.
    python3 "$mu" --revert >/dev/null 2>&1
    command hermes "$@"; rc=$?
    python3 "$mu"
    return $rc
  fi
  python3 "$mu" -q 2>&1 | sed 's/^/  /' >&2
  # SSH from macOS Terminal.app doesn't forward TERM_PROGRAM, so the TUI skips its
  # Terminal.app fixes (SGR-dim fading, colour downgrade, redraw). COLORFGBG=15;0 = dark profile.
  if [ -n "$SSH_CONNECTION" ] && [ -z "$TERM_PROGRAM" ] && [ -z "$LC_TERMINAL" ]; then
    TERM_PROGRAM=Apple_Terminal COLORFGBG="${COLORFGBG:-15;0}" command hermes "$@"
  else
    command hermes "$@"
  fi
}
# <<< hermes-minimal-ui <<<
