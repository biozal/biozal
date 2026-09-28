"""Quest cards: one per featured repo."""
from __future__ import annotations

from generator.config import Quest
from generator.icons import icon, star
from generator.models import RepoStats
from generator.pixel import PALETTE as P, fit, svg_doc, text, text_width, window, wrap

W, H = 410, 120
TEXT_X = 84
TEXT_W = W - TEXT_X - 16
KIND_STYLE = {"guild": ("GUILD QUEST", "shield", "#4a6cf7"),
              "side": ("SIDE QUEST", "potion", "#d8642a")}


def render_quest(quest: Quest, stats: RepoStats | None) -> str:
    label, shape, color = KIND_STYLE[quest.kind]
    blurb = quest.blurb or (stats.description if stats else "")
    name, name_size = fit(quest.name, TEXT_W, 10)
    body = [window(0, 0, W, H, label), icon(shape, color, 20, 34, 3),
            text(TEXT_X, 46, name, name_size, P["amber"])]
    for i, line in enumerate(wrap(blurb, TEXT_W // 7, 2)):
        body.append(text(TEXT_X, 66 + i * 12, line, 7, P["text"]))
    if stats:
        if stats.language:
            body.append(text(TEXT_X, 104, stats.language.upper(), 6, P["muted"]))
        count = str(stats.stars)
        count_x = W - 16 - text_width(count, 8)
        body += [star(count_x - 18, 91, 2), text(count_x, 104, count, 8, P["amber"])]
    return svg_doc(W, H, "".join(body))
