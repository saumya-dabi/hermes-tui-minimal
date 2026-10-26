#!/usr/bin/env python3
"""Drive the Hermes TUI in a pty and dump raw output snapshots.

usage: [APPLETERM=1] [HERMES_BIN=/path/to/hermes] tui_drive.py OUTPREFIX step1 step2 ...
  step = "wait:N" | "send:TEXT" (\\r = Enter, \\x1b = Esc) | "snap:NAME"
"""
import fcntl, os, pty, select, struct, sys, termios, time

out = sys.argv[1]
steps = sys.argv[2:]
pid, fd = pty.fork()
if pid == 0:
    os.environ["TERM"] = "xterm-256color"
    if os.environ.get("APPLETERM"):  # emulate macOS Terminal.app over SSH
        os.environ.pop("COLORTERM", None); os.environ["TERM_PROGRAM"] = "Apple_Terminal"; os.environ["COLORFGBG"] = "15;0"
    else:
        os.environ["COLORTERM"] = "truecolor"
    os.execvp(os.environ.get("HERMES_BIN", "hermes"), ["hermes"])
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
buf = bytearray()


def pump(sec):
    end = time.time() + sec
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return
            if not data:
                return
            buf.extend(data)
            # answer cursor-position / device-attr queries so Ink doesn't stall
            if b"\x1b[6n" in data:
                os.write(fd, b"\x1b[1;1R")
            if b"\x1b[c" in data:
                os.write(fd, b"\x1b[?62;c")


for s in steps:
    kind, _, arg = s.partition(":")
    if kind == "wait":
        pump(float(arg))
    elif kind == "send":
        os.write(fd, arg.encode().decode("unicode_escape").encode())
        pump(0.3)
    elif kind == "snap":
        open(f"{out}.{arg}.raw", "wb").write(bytes(buf))
        buf.clear()
os.kill(pid, 9)
