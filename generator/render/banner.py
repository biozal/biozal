"""Title-screen banner: portrait, flickering torches, name, level and a blinking PRESS START."""
from __future__ import annotations

import calendar
from datetime import date

from generator.config import Profile, level
from generator.pixel import PALETTE as P, bar, data_uri, fit, grid_to_svg, rect, svg_doc, text, window

W, H = 830, 300
TEXT_X = 320
TEXT_MAX_W = W - 340

FLAME = [
    "..y..",
    ".yy..",
    ".ywy.",
    "yywyo",
    "ywwyo",
    "oyyyo",
    ".ooo.",
]
FLAME_COLORS = {"y": "#ffd060", "w": "#fff4c0", "o": "#e8641e"}

CSS = (
    "@keyframes flick{0%,100%{opacity:1;transform:scaleY(1)}"
    "40%{opacity:.8;transform:scaleY(.88)}70%{opacity:.95;transform:scaleY(1.06)}}"
    ".flame{animation:flick .9s steps(3) infinite;transform-box:fill-box;transform-origin:50% 100%}"
    ".flame2{animation-delay:-.45s}"
    "@keyframes glow{0%,100%{opacity:.55}50%{opacity:.35}}"
    ".glow{animation:glow 1.8s ease-in-out infinite}"
    "@keyframes blink{50%{opacity:0}}"
    ".blink{animation:blink 1.2s steps(1) infinite}"
    ".portrait{image-rendering:pixelated}"
    "@media (prefers-reduced-motion:reduce){.flame,.glow,.blink{animation:none}}"
)

DEFS = (
    '<pattern id="brick" width="32" height="16" patternUnits="userSpaceOnUse">'
    f'<rect width="32" height="16" fill="{P["panel"]}"/>'
    f'<rect x="0" y="0" width="31" height="7" fill="{P["brick"]}"/>'
    f'<rect x="-16" y="8" width="31" height="7" fill="{P["brick"]}"/>'
    f'<rect x="16" y="8" width="31" height="7" fill="{P["brick"]}"/>'
    "</pattern>"
    '<radialGradient id="torchglow">'
    f'<stop offset="0" stop-color="{P["amber"]}" stop-opacity=".6"/>'
    f'<stop offset="1" stop-color="{P["amber"]}" stop-opacity="0"/>'
    "</radialGradient>"
)


def xp_fraction(today: date) -> float:
    """Fraction of the current year elapsed: XP toward the next level."""
    days = 366 if calendar.isleap(today.year) else 365
    return (today.timetuple().tm_yday - 1) / days


def _torch(x: int, y: int, extra_cls: str = "") -> str:
    glow = f'<circle class="glow" cx="{x + 10}" cy="{y + 14}" r="34" fill="url(#torchglow)"/>'
    handle = rect(x + 6, y + 28, 8, 26, P["border"]) + rect(x + 4, y + 26, 12, 4, "#8a5a3a")
    flame = f'<g class="{("flame " + extra_cls).strip()}">'
    return glow + handle + flame + grid_to_svg(FLAME, FLAME_COLORS, x, y, 4) + "</g>"


def render_banner(profile: Profile, portrait_png: bytes, today: date) -> str:
    lvl = level(profile.career_start_year, today)
    name, name_size = fit(profile.name, TEXT_MAX_W, 40)
    title, title_size = fit(profile.title, TEXT_MAX_W, 12)
    subtitle, sub_size = fit(f"Lv.{lvl} {profile.char_class}", TEXT_MAX_W, 14)
    body = [
        window(0, 0, W, H),
        rect(6, 6, W - 12, H - 12, "url(#brick)"),
        _torch(284, 20),
        _torch(790, 20, "flame2"),
        rect(24, 24, 252, 252, P["shadow"]),
        rect(26, 26, 248, 248, P["border_hi"]),
        f'<image class="portrait" x="30" y="30" width="240" height="240" href="{data_uri(portrait_png)}"/>',
        text(TEXT_X + 4, 104, name, name_size, P["shadow"]),
        text(TEXT_X, 100, name, name_size, P["amber"]),
        text(TEXT_X, 140, subtitle, sub_size, P["parchment"]),
        text(TEXT_X, 168, title, title_size, P["text"]),
        text(TEXT_X, 190, profile.real_name, 8, P["muted"]),
        text(TEXT_X, 222, "XP", 8, P["amber"]),
        bar(TEXT_X + 26, 212, 260, 12, xp_fraction(today)),
        text(TEXT_X + 294, 222, f"LV.{lvl + 1}", 8, P["muted"]),
        text(TEXT_X, 266, "> PRESS START", 12, P["accent"], cls="t blink"),
    ]
    return svg_doc(W, H, "".join(body), css=CSS, defs=DEFS)
