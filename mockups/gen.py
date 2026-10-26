#!/usr/bin/env python3
"""Render three markdown-style mockups for the Hermes TUI reply area as PNGs.

Palette = macOS Terminal.app (Pro-ish, black bg) so the images match a dark Terminal.app profile.
Usage: python3 gen.py OUTDIR
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLS, CW, CH = 100, 9, 19
BG, FG = "#000000", "#f2f2f2"
C = {
    "cyan": "#00a6b2", "white": "#bfbfbf", "whiteB": "#e5e5e5", "dim": "#666666",
    "green": "#00a600", "yellow": "#999900", "magentaB": "#e500e5", "redB": "#e50000",
    "g235": "#262626", "g236": "#303030", "g237": "#3a3a3a", "g238": "#444444", "black": "#000000",
}

FONT_DIR = "/usr/share/fonts"
F_REG = ImageFont.truetype(f"{FONT_DIR}/adobe-source-code-pro/SourceCodePro-Regular.otf", 15)
F_BOLD = ImageFont.truetype(f"{FONT_DIR}/adobe-source-code-pro/SourceCodePro-Bold.otf", 15)
F_IT = ImageFont.truetype(f"{FONT_DIR}/adobe-source-code-pro/SourceCodePro-It.otf", 15)
F_SYM = ImageFont.truetype(f"{FONT_DIR}/dejavu-sans-fonts/DejaVuSans.ttf", 14)
F_SYMB = ImageFont.truetype(f"{FONT_DIR}/dejavu-sans-fonts/DejaVuSans-Bold.ttf", 14)


def is_sym(ch):
    o = ord(ch)
    return 0x2500 <= o <= 0x25FF or ch in "₹Δ✓✗›⎇§◆•◦▪▸▍▌▐█▏▕☐☑–—…"


class Screen:
    def __init__(self):
        self.rows = []  # list of list of cells (ch, fg, bg, bold, italic, underline)

    def line(self, segs=None, bg=None):
        """segs: list of (text, style dict). Pads to COLS with bg."""
        row = []
        for text, st in (segs or []):
            for ch in text:
                row.append((ch, st.get("fg"), st.get("bg", bg), st.get("b", False), st.get("i", False), st.get("u", False)))
        while len(row) < COLS:
            row.append((" ", None, bg, False, False, False))
        self.rows.append(row[:COLS])

    def blank(self):
        self.line()

    def render(self, title, path):
        H = len(self.rows)
        img = Image.new("RGB", (COLS * CW + 24, H * CH + 52), "#1b1b1b")
        d = ImageDraw.Draw(img)
        d.text((12, 8), title, fill="#dddddd", font=F_BOLD)
        ox, oy = 12, 36
        d.rectangle([ox, oy, ox + COLS * CW, oy + H * CH], fill=BG)
        for y, row in enumerate(self.rows):
            for x, (ch, fg, bg, b, i, u) in enumerate(row):
                px, py = ox + x * CW, oy + y * CH
                if bg:
                    d.rectangle([px, py, px + CW - 1, py + CH - 1], fill=bg)
                if ch and ch != " ":
                    f = (F_SYMB if b else F_SYM) if is_sym(ch) else (F_BOLD if b else F_IT if i else F_REG)
                    d.text((px, py + 1), ch, fill=fg or FG, font=f)
                if u:
                    d.line([px, py + CH - 3, px + CW - 1, py + CH - 3], fill=fg or FG)
        img.save(path)


# ---------- shared chrome ----------
def chrome_top(s):
    s.line([("› ", {"fg": C["dim"]}), ("explain the quote engine fix and what changed", {"fg": C["whiteB"]})])
    s.blank()
    s.line([("  ✓ ", {"fg": C["green"]}), ("terminal ", {"fg": C["white"]}), ("pytest -q engine/  ", {"fg": C["dim"]}), ("24 passed · 3.1s", {"fg": C["dim"]})])
    s.line([("  ✓ ", {"fg": C["green"]}), ("read_file ", {"fg": C["white"]}), ("engine/rate_card.py", {"fg": C["dim"]})])
    s.blank()


def chrome_bottom(s):
    s.blank()
    s.line([("─" * COLS, {"fg": C["dim"]})])
    s.line([("› ", {"fg": C["whiteB"]})])
    s.line([("─" * COLS, {"fg": C["dim"]})])
    s.line([("  auto best ", {"fg": C["white"]}), ("│ ", {"fg": C["dim"]}), ("17.5k/500k ", {"fg": C["white"]}), ("│ ", {"fg": C["dim"]}), ("⎇ main", {"fg": C["cyan"]})])


CODE = [
    [("def ", "magentaB"), ("quote", None), ("(card: RateCard, pax: int) -> int:", None)],
    [("    base = card.fixed + card.per_pax * pax", None)],
    [("    ", None), ("return ", "magentaB"), ("round(base * (", None), ("1", "yellow"), (" + card.margin))", None)],
]


def code_segs(line, bg=None, fg_default=None):
    return [(t, {"fg": C[c] if c else fg_default, "bg": bg}) for t, c in line]


def para(s, text, indent=0, fg=None):
    s.line([(" " * indent + text, {"fg": fg})])


def inline_code_segs(parts, bg=C["g237"], fg=C["whiteB"], base=None):
    """parts: list of (text, is_code)."""
    return [(t, {"fg": fg if code else base, "bg": bg if code else None}) for t, code in parts]


# ---------- Option A: Editorial ----------
def option_a(out):
    s = Screen()
    chrome_top(s)
    # H1
    s.line([("Quote engine: per-pax pricing fix", {"fg": C["whiteB"], "b": True})])
    s.line([("─" * COLS, {"fg": C["dim"]})])
    s.blank()
    para(s, "The rate card stored one price and multiplied it by heads. Groups were over-quoted and")
    para(s, "couples on group-calibrated products were under-quoted.")
    s.blank()
    # H2
    s.line([("What changed", {"fg": C["cyan"], "b": True})])
    s.blank()
    s.line([("• ", {"fg": C["cyan"]})] + inline_code_segs([("engine/rate_card.py", True), (" now stores a recipe (base + per-pax + fixed) instead of a price", False)]))
    s.line([("• ", {"fg": C["cyan"]}), ("Supplier sync holds suspicious changes (>15 % delta) in an OPS queue", {})])
    s.line([("  ◦ ", {"fg": C["dim"]}), ("ranked by ₹ exposure, oldest first", {"fg": C["white"]})])
    s.line([("• ", {"fg": C["cyan"]}), ("24 engine tests pass, 3 new for multi-pax", {})])
    s.blank()
    # H3
    s.line([("Example", {"fg": C["whiteB"], "b": True})])
    s.blank()
    bg = C["g235"]
    w = 60
    s.line([("  ", {}), ("▏", {"fg": C["dim"], "bg": bg}), (" " * (w - 8), {"bg": bg}), ("python ", {"fg": C["dim"], "bg": bg, "i": True})])
    for ln in CODE:
        segs = [("  ", {}), ("▏ ", {"fg": C["dim"], "bg": bg})] + code_segs(ln, bg=bg)
        n = sum(len(t) for t, _ in segs)
        segs.append((" " * (w + 2 - n), {"bg": bg}))
        s.line(segs)
    s.line([("  ", {}), ("▏", {"fg": C["dim"], "bg": bg}), (" " * (w - 1), {"bg": bg})])
    s.blank()
    s.line([("Rollout", {"fg": C["cyan"], "b": True})])
    s.blank()
    s.line([("1. ", {"fg": C["cyan"], "b": True})] + inline_code_segs([("Deploy behind ", False), ("QUOTE_V2", True), (" flag", False)]))
    s.line([("2. ", {"fg": C["cyan"], "b": True}), ("Shadow-price for a week, compare with v1", {})])
    s.line([("3. ", {"fg": C["cyan"], "b": True}), ("Flip for Bali and Vietnam first", {})])
    s.blank()
    s.line([("  Segment       ", {"fg": C["whiteB"], "b": True}), ("│ ", {"fg": C["dim"]}), ("v1 quote   ", {"fg": C["whiteB"], "b": True}), ("│ ", {"fg": C["dim"]}), ("v2 quote   ", {"fg": C["whiteB"], "b": True}), ("│ ", {"fg": C["dim"]}), ("Δ", {"fg": C["whiteB"], "b": True})])
    s.line([("  ──────────────┼────────────┼────────────┼──────", {"fg": C["dim"]})])
    s.line([("  Couple        ", {}), ("│ ", {"fg": C["dim"]}), ("₹1,48,000  ", {}), ("│ ", {"fg": C["dim"]}), ("₹1,52,400  ", {}), ("│ ", {"fg": C["dim"]}), ("+3%", {"fg": C["green"]})])
    s.line([("  Family of 4   ", {}), ("│ ", {"fg": C["dim"]}), ("₹2,96,000  ", {}), ("│ ", {"fg": C["dim"]}), ("₹2,61,800  ", {}), ("│ ", {"fg": C["dim"]}), ("−12%", {"fg": C["redB"]})])
    s.blank()
    s.line([("▌ ", {"fg": C["cyan"]}), ("1% of GBV is ₹17L a month. The v2 engine closes most of it.", {"fg": C["white"], "i": True})])
    s.blank()
    s.line([("─" * 40, {"fg": C["dim"]})])
    s.blank()
    s.line([("Verified:", {"b": True}), (" tests pass, deployed to preview. ", {}), ("Left:", {"b": True}), (" prod flag flip.", {})])
    chrome_bottom(s)
    s.render("Option A — Editorial  (typographic hierarchy, shaded code, light rules)", out / "option_A_editorial.png")


# ---------- Option B: Panels ----------
def option_b(out):
    s = Screen()
    chrome_top(s)
    t = " Quote engine: per-pax pricing fix "
    s.line([(t, {"fg": C["black"], "bg": C["whiteB"], "b": True})])
    s.blank()
    para(s, "The rate card stored one price and multiplied it by heads. Groups were over-quoted and")
    para(s, "couples on group-calibrated products were under-quoted.")
    s.blank()
    h = "What changed"
    s.line([("━━ ", {"fg": C["cyan"]}), (h + " ", {"fg": C["whiteB"], "b": True}), ("━" * (COLS - len(h) - 4), {"fg": C["cyan"]})])
    s.blank()
    s.line([("  ▪ ", {"fg": C["white"]})] + inline_code_segs([("engine/rate_card.py", True), (" now stores a recipe (base + per-pax + fixed) instead of a price", False)]))
    s.line([("  ▪ ", {"fg": C["white"]}), ("Supplier sync holds suspicious changes (>15 % delta) in an OPS queue", {})])
    s.line([("    ▫ ", {"fg": C["dim"]}), ("ranked by ₹ exposure, oldest first", {"fg": C["white"]})])
    s.line([("  ▪ ", {"fg": C["white"]}), ("24 engine tests pass, 3 new for multi-pax", {})])
    s.blank()
    s.line([("  ▸ ", {"fg": C["cyan"]}), ("Example", {"fg": C["whiteB"], "b": True})])
    s.blank()
    w = 60
    s.line([("  ╭─ ", {"fg": C["dim"]}), ("python", {"fg": C["white"]}), (" " + "─" * (w - 10) + "╮", {"fg": C["dim"]})])
    for ln in CODE:
        segs = [("  │ ", {"fg": C["dim"]})] + code_segs(ln)
        n = sum(len(t) for t, _ in segs)
        segs.append((" " * (w + 2 - n) + "│", {"fg": C["dim"]}))
        s.line(segs)
    s.line([("  ╰" + "─" * (w - 1) + "╯", {"fg": C["dim"]})])
    s.blank()
    h = "Rollout"
    s.line([("━━ ", {"fg": C["cyan"]}), (h + " ", {"fg": C["whiteB"], "b": True}), ("━" * (COLS - len(h) - 4), {"fg": C["cyan"]})])
    s.blank()
    s.line([("  1) ", {"fg": C["cyan"]})] + inline_code_segs([("Deploy behind ", False), ("QUOTE_V2", True), (" flag", False)]))
    s.line([("  2) ", {"fg": C["cyan"]}), ("Shadow-price for a week, compare with v1", {})])
    s.line([("  3) ", {"fg": C["cyan"]}), ("Flip for Bali and Vietnam first", {})])
    s.blank()
    s.line([("  ┌──────────────┬────────────┬────────────┬──────┐", {"fg": C["dim"]})])
    s.line([("  │ ", {"fg": C["dim"]}), ("Segment      ", {"fg": C["whiteB"], "b": True}), (" │ ", {"fg": C["dim"]}), ("v1 quote  ", {"fg": C["whiteB"], "b": True}), (" │ ", {"fg": C["dim"]}), ("v2 quote  ", {"fg": C["whiteB"], "b": True}), (" │ ", {"fg": C["dim"]}), ("Δ   ", {"fg": C["whiteB"], "b": True}), (" │", {"fg": C["dim"]})])
    s.line([("  ├──────────────┼────────────┼────────────┼──────┤", {"fg": C["dim"]})])
    s.line([("  │ ", {"fg": C["dim"]}), ("Couple       ", {}), (" │ ", {"fg": C["dim"]}), ("₹1,48,000 ", {}), (" │ ", {"fg": C["dim"]}), ("₹1,52,400 ", {}), (" │ ", {"fg": C["dim"]}), ("+3% ", {"fg": C["green"]}), (" │", {"fg": C["dim"]})])
    s.line([("  │ ", {"fg": C["dim"]}), ("Family of 4  ", {}), (" │ ", {"fg": C["dim"]}), ("₹2,96,000 ", {}), (" │ ", {"fg": C["dim"]}), ("₹2,61,800 ", {}), (" │ ", {"fg": C["dim"]}), ("−12%", {"fg": C["redB"]}), (" │", {"fg": C["dim"]})])
    s.line([("  └──────────────┴────────────┴────────────┴──────┘", {"fg": C["dim"]})])
    s.blank()
    s.line([("  ┃ ", {"fg": C["yellow"]}), ("1% of GBV is ₹17L a month. The v2 engine closes most of it.", {"fg": C["white"]})])
    s.blank()
    s.line([("  " + "─" * 46 + " ◆ " + "─" * 46, {"fg": C["dim"]})])
    s.blank()
    s.line([("Verified:", {"b": True}), (" tests pass, deployed to preview. ", {}), ("Left:", {"b": True}), (" prod flag flip.", {})])
    chrome_bottom(s)
    s.render("Option B — Panels  (title band, section rules, boxed code and tables)", out / "option_B_panels.png")


# ---------- Option C: Outline ----------
def option_c(out):
    s = Screen()
    chrome_top(s)
    s.line([("Quote engine: per-pax pricing fix", {"fg": C["whiteB"], "b": True})])
    s.blank()
    para(s, "The rate card stored one price and multiplied it by heads. Groups were over-quoted and")
    para(s, "couples on group-calibrated products were under-quoted.")
    s.blank()
    s.line([("What changed", {"fg": C["cyan"], "b": True})])
    s.line([("  – ", {"fg": C["dim"]})] + inline_code_segs([("engine/rate_card.py", True), (" now stores a recipe (base + per-pax + fixed) instead of a price", False)], bg=None, fg=C["cyan"]))
    s.line([("  – ", {"fg": C["dim"]}), ("Supplier sync holds suspicious changes (>15 % delta) in an OPS queue", {})])
    s.line([("    · ", {"fg": C["dim"]}), ("ranked by ₹ exposure, oldest first", {"fg": C["white"]})])
    s.line([("  – ", {"fg": C["dim"]}), ("24 engine tests pass, 3 new for multi-pax", {})])
    s.blank()
    s.line([("  Example", {"fg": C["whiteB"], "b": True})])
    s.line([("    │ ", {"fg": C["cyan"]}), ("python", {"fg": C["dim"], "i": True})])
    for ln in CODE:
        s.line([("    │ ", {"fg": C["cyan"]})] + code_segs(ln))
    s.blank()
    s.line([("Rollout", {"fg": C["cyan"], "b": True})])
    s.line([("  1  ", {"fg": C["white"]})] + inline_code_segs([("Deploy behind ", False), ("QUOTE_V2", True), (" flag", False)], bg=None, fg=C["cyan"]))
    s.line([("  2  ", {"fg": C["white"]}), ("Shadow-price for a week, compare with v1", {})])
    s.line([("  3  ", {"fg": C["white"]}), ("Flip for Bali and Vietnam first", {})])
    s.blank()
    s.line([("  Segment      ", {"fg": C["whiteB"], "b": True, "u": True}), ("   ", {}), ("v1 quote  ", {"fg": C["whiteB"], "b": True, "u": True}), ("   ", {}), ("v2 quote  ", {"fg": C["whiteB"], "b": True, "u": True}), ("   ", {}), ("Δ   ", {"fg": C["whiteB"], "b": True, "u": True})])
    s.line([("  Couple          ₹1,48,000     ₹1,52,400     ", {}), ("+3%", {"fg": C["green"]})])
    s.line([("  Family of 4     ₹2,96,000     ₹2,61,800     ", {}), ("−12%", {"fg": C["redB"]})])
    s.blank()
    s.line([("  │ ", {"fg": C["dim"]}), ("1% of GBV is ₹17L a month. The v2 engine closes most of it.", {"fg": C["white"], "i": True})])
    s.blank()
    s.line([("  · · ·", {"fg": C["dim"]})])
    s.blank()
    s.line([("Verified:", {"b": True}), (" tests pass, deployed to preview. ", {}), ("Left:", {"b": True}), (" prod flag flip.", {})])
    chrome_bottom(s)
    s.render("Option C — Outline  (no boxes or fills; hierarchy by colour, weight and indent)", out / "option_C_outline.png")


# ---------- Current (as rendered today) ----------
def current(out):
    s = Screen()
    chrome_top(s)
    s.line([("Quote engine: per-pax pricing fix", {"fg": C["cyan"], "b": True})])
    s.blank()
    para(s, "The rate card stored one price and multiplied it by heads. Groups were over-quoted and")
    para(s, "couples on group-calibrated products were under-quoted.")
    s.blank()
    s.line([("What changed", {"fg": C["cyan"], "b": True})])
    s.blank()
    s.line([("• ", {"fg": C["dim"]})] + inline_code_segs([("engine/rate_card.py", True), (" now stores a recipe (base + per-pax + fixed) instead of a price", False)], bg=None, fg=C["cyan"]))
    s.line([("• ", {"fg": C["dim"]}), ("Supplier sync holds suspicious changes (>15 % delta) in an OPS queue", {})])
    s.line([("  • ", {"fg": C["dim"]}), ("ranked by ₹ exposure, oldest first", {})])
    s.line([("• ", {"fg": C["dim"]}), ("24 engine tests pass, 3 new for multi-pax", {})])
    s.blank()
    s.line([("Example", {"fg": C["cyan"], "b": True})])
    s.blank()
    s.line([("  ─ python", {"fg": C["dim"]})])
    for ln in CODE:
        s.line([("  ", {})] + code_segs(ln))
    s.blank()
    s.line([("Rollout", {"fg": C["cyan"], "b": True})])
    s.blank()
    s.line([("1. ", {"fg": C["dim"]})] + inline_code_segs([("Deploy behind ", False), ("QUOTE_V2", True), (" flag", False)], bg=None, fg=C["cyan"]))
    s.line([("2. ", {"fg": C["dim"]}), ("Shadow-price for a week, compare with v1", {})])
    s.line([("3. ", {"fg": C["dim"]}), ("Flip for Bali and Vietnam first", {})])
    s.blank()
    s.line([("  Segment      ", {"fg": C["cyan"], "b": True}), ("  v1 quote  ", {"fg": C["cyan"], "b": True}), ("  v2 quote  ", {"fg": C["cyan"], "b": True}), ("  Δ", {"fg": C["cyan"], "b": True})])
    s.line([("  Couple         ₹1,48,000   ₹1,52,400   +3%", {})])
    s.line([("  Family of 4    ₹2,96,000   ₹2,61,800   −12%", {})])
    s.blank()
    s.line([("│ 1% of GBV is ₹17L a month. The v2 engine closes most of it.", {"fg": C["dim"]})])
    s.blank()
    s.line([("─" * 36, {"fg": C["dim"]})])
    s.blank()
    s.line([("Verified:", {"b": True}), (" tests pass, deployed to preview. ", {}), ("Left:", {"b": True}), (" prod flag flip.", {})])
    chrome_bottom(s)
    s.render("Current  (today: every heading looks the same, code has no frame, flat lists)", out / "option_0_current.png")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    current(out)
    option_a(out)
    option_b(out)
    option_c(out)
    for p in sorted(out.glob("option_*.png")):
        print(p)
