#!/bin/bash
# Hermes clipboard bridge — Mac side (run once on the MacBook; safe to re-run).
#
# Why: macOS Terminal.app ignores OSC 52, so a TUI on the VM cannot set the Mac clipboard
# through the terminal. This installs a tiny launchd agent (built-in tools only) that listens on
# 127.0.0.1:47052 ON THE MAC and pipes whatever arrives into pbcopy, then replies "OK".
# Your ssh config forwards the VM's 127.0.0.1:47052 to it, for this VM only.
#
# Undo: launchctl bootout gui/$(id -u)/com.hermes.clipbridge; rm ~/Library/LaunchAgents/com.hermes.clipbridge.plist
#       and delete the "hermes-clipbridge" block at the end of ~/.ssh/config.
set -euo pipefail

VM_IP="${1:?usage: mac-setup.sh <server-ip-or-hostname>}"
PORT=47052
LABEL="com.hermes.clipbridge"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SSHCFG="$HOME/.ssh/config"

[ "$(uname -s)" = "Darwin" ] || { echo "Run this on the Mac, not on the server."; exit 1; }

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# 1) launchd agent: one pbcopy per connection (inetd style), bound to localhost only.
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string><string>-c</string>
    <string>/usr/bin/pbcopy &amp;&amp; printf OK</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>LANG</key><string>en_US.UTF-8</string><key>LC_CTYPE</key><string>UTF-8</string></dict>
  <key>inetdCompatibility</key><dict><key>Wait</key><false/></dict>
  <key>Sockets</key>
  <dict>
    <key>Listener</key>
    <dict>
      <key>SockNodeName</key><string>127.0.0.1</string>
      <key>SockServiceName</key><string>$PORT</string>
      <key>SockType</key><string>stream</string>
      <key>SockFamily</key><string>IPv4</string>
    </dict>
  </dict>
</dict>
</plist>
EOF
plutil -lint "$PLIST" >/dev/null
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "✓ clipboard listener installed (127.0.0.1:$PORT on this Mac)"

# 2) ssh config: forward the VM's 127.0.0.1:47052 back to this Mac, for this VM only.
#    Appended at the END so it also matches an alias whose HostName is the VM IP.
#    ControlMaster: all Terminal windows share one connection, so the forward never conflicts.
touch "$SSHCFG"; chmod 600 "$SSHCFG"
if ! grep -q "hermes-clipbridge" "$SSHCFG"; then
  cp "$SSHCFG" "$SSHCFG.bak-hermes-clipbridge"
  cat >> "$SSHCFG" <<EOF

# >>> hermes-clipbridge >>> (copy from the Hermes TUI on $VM_IP lands in this Mac's clipboard)
Match host $VM_IP
  RemoteForward 127.0.0.1:$PORT 127.0.0.1:$PORT
  ExitOnForwardFailure no
  ControlMaster auto
  ControlPath ~/.ssh/cm-%C
  ControlPersist 8h
  ServerAliveInterval 30
# <<< hermes-clipbridge <<<
EOF
  echo "✓ ~/.ssh/config updated (backup: ~/.ssh/config.bak-hermes-clipbridge)"
else
  echo "✓ ~/.ssh/config already has the hermes-clipbridge block"
fi

# 3) Local self-test (perl ships with macOS): send text, expect OK, read it back with pbpaste.
if command -v perl >/dev/null 2>&1; then
  TOKEN="hermes-bridge-mac-selftest-$$"
  ACK=$(perl -MIO::Socket::INET -e '
    my $s = IO::Socket::INET->new(PeerAddr => "127.0.0.1", PeerPort => '"$PORT"', Timeout => 3) or exit 1;
    print $s $ARGV[0]; shutdown($s, 1); local $/; my $r = <$s>; print $r // "";' "$TOKEN" || true)
  if [ "$ACK" = "OK" ] && [ "$(pbpaste)" = "$TOKEN" ]; then
    echo "✓ self-test passed (listener -> pbcopy works)"
    printf '' | pbcopy
  else
    echo "✗ self-test FAILED (ack='$ACK'). Tell Hermes this exact line."
    exit 1
  fi
fi

echo
echo "Done. Now: close ALL Terminal windows connected to the VM, open a new one, ssh in again, run hermes."
