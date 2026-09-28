"""Shared pixel-art SVG building blocks. Pure string builders; the font file is the only thing read."""
from __future__ import annotations

import base64
import html
import io
import re
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"

# Warm torchlit-dungeon palette sampled from the portrait, plus the Cartyx blue accent.
PALETTE = {
    "bg": "#120b16",
    "panel": "#1d1220",
    "panel_dark": "#150d18",
    "brick": "#2a1a24",
    "border": "#5a3a2a",
    "border_hi": "#c8792e",
    "shadow": "#07040a",
    "outline": "#1a0f14",
    "amber": "#f0a040",
    "orange": "#d8642a",
    "parchment": "#f1dfb8",
    "parchment_dark": "#c9a877",
    "ink": "#2a1a12",
    "text": "#f1dfb8",
    "muted": "#a08870",
    "accent": "#85adff",
}

_TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)


def esc(s: str) -> str:
    return escape(s, {'"': "&quot;"})


def rect(x, y, w, h, fill: str, extra: str = "") -> str:
    tail = f" {extra}" if extra else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{tail}/>'


def text(x, y, s: str, size: int = 8, fill: str = PALETTE["text"], anchor: str = "start",
         cls: str = "t") -> str:
    return (f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def text_width(s: str, size: int) -> int:
    """Press Start 2P is monospaced with a 1em advance."""
    return len(s) * size


def fit(s: str, max_width: int, max_size: int, min_size: int = 6) -> tuple[str, int]:
    """Shrink the font to fit; below min_size, truncate with '...'."""
    size = max(min_size, min(max_size, max_width // max(1, len(s))))
    max_chars = max_width // size
    if len(s) > max_chars:
        s = s[: max_chars - 3].rstrip() + "..."
    return s, size


def wrap(s: str, max_chars: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in s.split():
        while len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:max_chars])
            word = word[max_chars:]
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        lines = lines[: max_lines - 1] + [last[: max_chars - 3].rstrip() + "..."]
    return lines


def window(x, y, w, h, title: str | None = None) -> str:
    """Dark game window with a notched pixel border and an optional title tab."""
    p = PALETTE
    parts = [
        rect(x + 2, y, w - 4, h, p["shadow"]),
        rect(x, y + 2, w, h - 4, p["shadow"]),
        rect(x + 2, y + 2, w - 4, h - 4, p["border_hi"]),
        rect(x + 4, y + 4, w - 8, h - 8, p["border"]),
        rect(x + 6, y + 6, w - 12, h - 12, p["panel"]),
    ]
    if title:
        parts.append(rect(x + 14, y, text_width(title, 8) + 12, 14, p["border_hi"]))
        parts.append(text(x + 20, y + 11, title, 8, p["ink"]))
    return "".join(parts)


def grid_to_svg(rows: list[str], colors: dict[str, str], x, y, scale=1) -> str:
    """Draw a character grid; '.' is transparent and horizontal runs merge into one rect."""
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == ".":
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == ch:
                c += 1
            out.append(rect(x + start * scale, y + r * scale, (c - start) * scale, scale, colors[ch]))
    return "".join(out)


def bar(x, y, w, h, frac: float, fill: str = PALETTE["amber"]) -> str:
    """Segmented stat bar: 6-unit blocks with 2-unit gaps."""
    frac = max(0.0, min(1.0, frac))
    parts = [rect(x, y, w, h, PALETTE["shadow"]), rect(x + 1, y + 1, w - 2, h - 2, PALETTE["panel_dark"])]
    segments = (w - 4) // 8
    for i in range(round(segments * frac)):
        parts.append(rect(x + 2 + i * 8, y + 2, 6, h - 4, fill))
    return "".join(parts)


def shade(hex_color: str, amount: float) -> str:
    """amount > 0 mixes toward white, amount < 0 toward black."""
    target = 255 if amount > 0 else 0
    a = abs(amount)
    channels = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(v + (target - v) * a):02x}" for v in channels)


def data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def used_chars(body: str) -> str:
    chars: set[str] = set()
    for inner in _TEXT_RE.findall(body):
        chars.update(html.unescape(inner))
    return "".join(sorted(chars))


@lru_cache(maxsize=1)
def _font_bytes() -> bytes:
    return FONT_PATH.read_bytes()


@lru_cache(maxsize=256)
def font_face(chars: str) -> str:
    """@font-face rule embedding Press Start 2P subset to `chars`; missing glyphs fall back to monospace."""
    font = TTFont(io.BytesIO(_font_bytes()), recalcTimestamp=False)  # stable bytes across builds
    subsetter = subset.Subsetter(subset.Options())
    subsetter.populate(text=chars)
    subsetter.subset(font)
    out = io.BytesIO()
    font.save(out)
    data = base64.b64encode(out.getvalue()).decode("ascii")
    return f"@font-face{{font-family:'PS2P';src:url(data:font/ttf;base64,{data}) format('truetype');}}"


def svg_doc(width: int, height: int, body: str, css: str = "", defs: str = "") -> str:
    chars = used_chars(body)
    font_css = font_face(chars) if chars else ""
    style = f"{font_css}.t{{font-family:'PS2P',monospace;}}{css}"
    defs_block = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
            f"<style>{style}</style>{defs_block}{body}</svg>")
