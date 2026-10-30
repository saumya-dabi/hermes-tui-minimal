# Hermes clipboard bridge (Mac Terminal.app over SSH)

**Problem.** macOS Terminal.app ignores OSC 52, the escape sequence a remote TUI uses to set the
local clipboard. Proven live on 30 Oct 2026: the TUI emitted a correct OSC 52 sequence, but
Chrome still pasted the old clipboard. Any fix on the VM side alone cannot work.

**Fix.** Every copy in the Hermes TUI also goes over the SSH connection:

```
TUI copy ──> VM 127.0.0.1:47052 ──(ssh RemoteForward)──> Mac 127.0.0.1:47052
         ──> launchd agent com.hermes.clipbridge ──> pbcopy ──> replies "OK"
```

The TUI shows `✓ copied N chars` only after the Mac sends back "OK". If the link is down, it
shows `✗ NOT copied: Mac clipboard link is down · reconnect SSH` instead. OSC 52 is still sent
too, so terminals that support it (iTerm2, Ghostty) keep working.

## Pieces
| Where | What |
|---|---|
| Mac | `~/Library/LaunchAgents/com.hermes.clipbridge.plist` (built-in launchd + pbcopy, localhost only) |
| Mac | the `hermes-clipbridge` block at the end of `~/.ssh/config`: RemoteForward 47052 plus ControlMaster, so every window shares one connection |
| VM | apply.py patch #24 (`clipBridge.helpers.ts`), in hermes-ink `termio/osc.ts` setClipboard (drag copy) and `src/lib/osc52.ts` (prompt box, link click, /copy) |
| VM | `clipbridge/hermes-clip (copy to ~/.local/bin)`: `echo hi \| hermes-clip`, or `hermes-clip --status` (exit 0 only when the Mac acks) |
| VM | the `hermes()` wrapper in `~/.bashrc` warns at launch if 47052 isn't listening |

## Setup on the Mac (once)
```
ssh <your usual target> 'cat ~/hermes-tui-minimal/clipbridge/mac-setup.sh' | bash -s <server-ip>
```
Then close every Terminal window connected to the VM, open a new one, and ssh in again.

## Checks
- VM: `ss -ltn 'sport = :47052'` should show a listener while you're connected.
- VM: `hermes-clip --status` should print "bridge OK", and ⌘V on the Mac then pastes the probe text.
- VM-only regression test, no Mac needed: start `fake_mac.py OUT 47999`, then run
  `HERMES_CLIP_BRIDGE_PORT=47999 python3 verify/t_quick.py`. The notices
  should say ✓ and OUT should hold the copied text. Point it at an unused port instead and the
  notices should say ✗ NOT copied.

## Turn off
`HERMES_CLIP_BRIDGE=0` in the environment turns off the bridge (OSC 52 only).
