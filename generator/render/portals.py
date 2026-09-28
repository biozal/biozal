"""Pixel link buttons for the footer."""
from __future__ import annotations

from generator.config import Portal
from generator.icons import icon
from generator.pixel import PALETTE as P, fit, rect, svg_doc, text

W, H = 160, 44
LABEL_X = 48
ICONS = {"dev.to": ("tome", "#e8e8e8"), "costoda.tech": ("scroll", "#f0a040"),
         "youtube": ("gem", "#ff3b3b"), "linkedin": ("shield", "#2f8fd8"),
         "ditto docs": ("shield", "#4a6cf7")}


def render_portal(portal: Portal) -> str:
    shape, color = ICONS.get(portal.label.lower(), ("scroll", P["amber"]))
    label, size = fit(portal.label.upper(), W - LABEL_X - 8, 8)
    body = [
        rect(2, 0, W - 4, H, P["shadow"]),
        rect(0, 2, W, H - 4, P["shadow"]),
        rect(2, 2, W - 4, H - 4, P["border_hi"]),
        rect(4, 4, W - 8, H - 8, P["panel"]),
        icon(shape, color, 8, 6, 2),
        text(LABEL_X, 26, label, size, P["parchment"]),
    ]
    return svg_doc(W, H, "".join(body))
