"""Parchment cards for recent dev.to posts and YouTube videos."""
from __future__ import annotations

from generator.icons import icon
from generator.models import FeedItem
from generator.pixel import PALETTE as P, rect, svg_doc, text, wrap

W, H = 410, 100
TEXT_X = 80
SOURCES = {"devto": ("DEV.TO", "tome", "#3b49df"),
           "youtube": ("YOUTUBE", "gem", "#ff3b3b")}


def _frame(source: str) -> list[str]:
    label, shape, color = SOURCES[source]
    return [
        rect(2, 0, W - 4, H, P["ink"]),
        rect(0, 2, W, H - 4, P["ink"]),
        rect(3, 3, W - 6, H - 6, P["parchment_dark"]),
        rect(5, 5, W - 10, H - 10, P["parchment"]),
        icon(shape, color, 16, 26, 3),
        text(TEXT_X, 24, label, 6, P["orange"]),
    ]


def render_scroll(item: FeedItem, source: str) -> str:
    body = _frame(source)
    body.append(text(W - 16, 24, item.published, 6, P["ink"], anchor="end"))
    for i, line in enumerate(wrap(item.title, (W - TEXT_X - 16) // 8, 3)):
        body.append(text(TEXT_X, 44 + i * 14, line, 8, P["ink"]))
    return svg_doc(W, H, "".join(body))


def render_sealed_scroll(source: str) -> str:
    body = _frame(source) + [
        text(TEXT_X, 50, "THE SCROLLS ARE SEALED...", 8, P["ink"]),
        text(TEXT_X, 70, "CLICK TO VISIT THE ARCHIVE", 6, P["orange"]),
    ]
    return svg_doc(W, H, "".join(body))
