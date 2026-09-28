"""4x4 inventory grid of skill items."""
from __future__ import annotations

from generator.config import Profile
from generator.icons import ITEMS, item_icon
from generator.pixel import PALETTE as P, rect, svg_doc, text, window

W, H = 410, 300


def render_inventory(profile: Profile) -> str:
    body = [window(0, 0, W, H, "INVENTORY")]
    for i, item_id in enumerate(profile.inventory):
        x0, y0 = 17 + (i % 4) * 94, 30 + (i // 4) * 64
        label = ITEMS[item_id][0]
        body += [
            rect(x0 + 3, y0 + 3, 88, 58, P["border"]),
            rect(x0 + 4, y0 + 4, 86, 56, P["panel_dark"]),
            item_icon(item_id, x0 + 31, y0 + 9, 2),
            text(x0 + 47, y0 + 54, label, 6, P["parchment"], anchor="middle"),
        ]
    return svg_doc(W, H, "".join(body))
