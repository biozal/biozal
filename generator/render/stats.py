"""Ability-score block: six D&D-style stats with segmented bars."""
from __future__ import annotations

from generator.config import ABILITIES, Profile, format_modifier
from generator.pixel import PALETTE as P, bar, svg_doc, text, window

W, H = 410, 300
ABILITY_NAMES = {"MOB": "MOBILE", "DAT": "DATA", "NET": "NETWORK",
                 "BAK": "BACKEND", "SYN": "P2P SYNC", "CHA": "ADVOCACY"}


def render_stats(profile: Profile) -> str:
    body = [window(0, 0, W, H, "STATS")]
    for i, ability in enumerate(ABILITIES):
        y = 44 + i * 42
        score = profile.stats[ability]
        body += [
            text(22, y + 12, ability, 12, P["amber"]),
            text(22, y + 26, ABILITY_NAMES[ability], 6, P["muted"]),
            bar(104, y + 2, 190, 14, score / 20),
            text(390, y + 14, f"{score} ({format_modifier(score)})", 9, P["text"], anchor="end"),
        ]
    return svg_doc(W, H, "".join(body))
