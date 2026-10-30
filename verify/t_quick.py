"""Fast copy regression check (no model call): transcript drag + prompt-box drag -> OSC 52 payloads."""
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from harness import TUI

t = TUI()
ok_boot = t.wait_for(r"auto|claude|│", 240)
t.pump(6)
res = {}

# transcript: run a local slash command so there is text to select
t.send("/help", 0.5); t.send(b"\r", 4)
L = t.text()
row = next((i for i, l in enumerate(L) if len(l.strip()) > 25 and "/" in l), None)
if row is None:
    t.dump("no transcript text"); t.kill(); sys.exit(2)
line = L[row]
x0 = len(line) - len(line.lstrip())
x1 = min(len(line), x0 + 20)
expect = line[x0:x1]
t.set_mark(); t.drag(x0 + 1, row + 1, x1, row + 1); t.pump(1.5)
got = t.osc52_since_mark()
notice = [l.strip() for l in t.text() if "copied" in l]
res["transcript drag"] = bool(got) and got[-1].strip() == expect.strip()
print("transcript expect", repr(expect), "got", got, "notice", notice)
t.send(b"\x1b", 0.4); t.pump(3)

# prompt box
t.send("hello world copy test", 0.8)
L = t.text()
py = max(i for i, l in enumerate(L) if "hello world copy test" in l)
px = L[py].find("hello world")
t.set_mark(); t.drag(px + 1, py + 1, px + len("hello world") + 1, py + 1); t.pump(1.5)
got = t.osc52_since_mark()
res["prompt drag"] = bool(got) and got[-1] == "hello world"
print("prompt got", got, "notice", [l.strip() for l in t.text() if "copied" in l])
t.dump("final")
print("RESULTS", res)
t.kill()
