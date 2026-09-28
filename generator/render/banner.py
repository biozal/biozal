"""Title-card banner: flickering torches, name, level and XP bar. The portrait is the GitHub avatar."""
from __future__ import annotations

import calendar
from datetime import date

from generator.config import Profile, level
from generator.pixel import PALETTE as P, bar, fit, grid_to_svg, rect, svg_doc, text, window

W, H = 830, 220
CX = W // 2
TEXT_MAX_W = W - 240  # clear of the torches
XP_BAR_W = 300
XP_ROW_W = 26 + XP_BAR_W + 56

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
    "@media (prefers-reduced-motion:reduce){.flame,.glow{animation:none}}"
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


def render_banner(profile: Profile, today: date) -> str:
    lvl = level(profile.career_start_year, today)
    name, name_size = fit(profile.name, TEXT_MAX_W, 48)
    title, title_size = fit(profile.title, TEXT_MAX_W, 12)
    subtitle, sub_size = fit(f"Lv.{lvl} {profile.char_class}", TEXT_MAX_W, 14)
    real_name, real_size = fit(profile.real_name, TEXT_MAX_W, 8)
    xp_x = CX - XP_ROW_W // 2
    body = [
        window(0, 0, W, H),
        rect(6, 6, W - 12, H - 12, "url(#brick)"),
        _torch(60, 70),
        _torch(750, 70, "flame2"),
        text(CX + 4, 84, name, name_size, P["shadow"], anchor="middle"),
        text(CX, 80, name, name_size, P["amber"], anchor="middle"),
        text(CX, 118, subtitle, sub_size, P["parchment"], anchor="middle"),
        text(CX, 144, title, title_size, P["text"], anchor="middle"),
        text(CX, 164, real_name, real_size, P["muted"], anchor="middle"),
        text(xp_x + 8, 196, "XP", 8, P["amber"], anchor="middle"),
        bar(xp_x + 26, 186, XP_BAR_W, 12, xp_fraction(today)),
        text(xp_x + 26 + XP_BAR_W + 28, 196, f"LV.{lvl + 1}", 8, P["muted"], anchor="middle"),
    ]
    return svg_doc(W, H, "".join(body), css=CSS, defs=DEFS)
