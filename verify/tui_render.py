#!/usr/bin/env python3
"""Render raw pty bytes through pyte; print text screen and write an HTML with colors."""
import html, sys
import pyte

raw_paths = sys.argv[1:]
screen = pyte.Screen(120, 40)
stream = pyte.ByteStream(screen)
for p in raw_paths:
    stream.feed(open(p, "rb").read())

# macOS Terminal.app standard ANSI palette (Basic/Pro profiles)
NAMED = {"black": "000000", "red": "990000", "green": "00a600", "brown": "999900", "yellow": "999900",
         "blue": "0000b2", "magenta": "b200b2", "cyan": "00a6b2", "white": "bfbfbf",
         "brightblack": "666666", "brightred": "e50000", "brightgreen": "00d900", "brightbrown": "e5e500",
         "brightblue": "0000ff", "brightmagenta": "e500e5", "brightcyan": "00e5e5", "brightwhite": "e5e5e5", "default": None}


def col(c, fallback):
    if c in NAMED:
        v = NAMED[c]
        return "#" + v if v else fallback
    if len(c) == 6:
        return "#" + c
    return fallback


rows = []
for y in range(screen.lines):
    line = screen.buffer[y]
    rows.append("".join(line[x].data for x in range(screen.columns)).rstrip())
print("\n".join(rows))

BG, FG = "#000000", "#f2f2f2"  # Terminal.app Pro
out = [f'<html><body style="background:{BG};margin:0"><pre style="font:14px/1.25 DejaVu Sans Mono,monospace;color:{FG};padding:8px">']
for y in range(screen.lines):
    line = screen.buffer[y]
    for x in range(screen.columns):
        ch = line[x]
        fg, bg = col(ch.fg, FG), col(ch.bg, "transparent")
        if ch.reverse:
            fg, bg = (bg if bg != "transparent" else BG), fg
        style = f"color:{fg};background:{bg}" + (";font-weight:bold" if ch.bold else "")
        out.append(f'<span style="{style}">{html.escape(ch.data or " ")}</span>')
    out.append("\n")
out.append("</pre></body></html>")
open(raw_paths[-1] + ".html", "w").write("".join(out))

try:
    from PIL import Image, ImageDraw, ImageFont
    CW, CH = 10, 20
    img = Image.new("RGB", (screen.columns * CW, screen.lines * CH), BG)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", 15)
    bold = ImageFont.truetype("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", 15)
    for y in range(screen.lines):
        line = screen.buffer[y]
        for x in range(screen.columns):
            ch = line[x]
            fg, bg = col(ch.fg, FG), col(ch.bg, None)
            if ch.reverse:
                fg, bg = (bg or BG), fg
            if bg:
                d.rectangle([x * CW, y * CH, x * CW + CW - 1, y * CH + CH - 1], fill=bg)
            if ch.data and ch.data != " ":
                d.text((x * CW, y * CH + 1), ch.data, fill=fg, font=bold if ch.bold else font)
    img.save(raw_paths[-1] + ".png")
except ImportError:
    pass
