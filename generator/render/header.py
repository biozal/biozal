"""Section header plate, e.g. 'QUEST LOG'."""
from __future__ import annotations

from generator.pixel import PALETTE as P, rect, svg_doc, text, text_width

W, H = 830, 40


def render_header(title: str) -> str:
    tw = text_width(title, 14)
    x = (W - tw - 40) // 2
    body = [
        rect(0, 19, W, 2, P["border_hi"]),
        rect(x, 2, tw + 40, 36, P["shadow"]),
        rect(x + 2, 4, tw + 36, 32, P["border_hi"]),
        rect(x + 4, 6, tw + 32, 28, P["bg"]),
        text(W // 2, 27, title, 14, P["amber"], anchor="middle"),
    ]
    return svg_doc(W, H, "".join(body))
