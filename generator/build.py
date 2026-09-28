"""Build the profile: profile.yml + live data -> assets/generated/*.svg + README.md."""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

from generator.cache import (
    decode_items, decode_repo, encode_items, encode_repo, load_cache, resolve, save_cache,
)
from generator.config import ConfigError, level, load_profile
from generator.fetch import Getter, fetch_devto, fetch_repo, fetch_youtube, http_get
from generator.icons import ITEMS
from generator.readme import Card, pacman, render_preview, render_readme, row
from generator.render.banner import render_banner
from generator.render.header import render_header
from generator.render.inventory import render_inventory
from generator.render.portals import render_portal
from generator.render.quests import render_quest
from generator.render.scrolls import render_scroll, render_sealed_scroll
from generator.render.stats import render_stats

ROOT = Path(__file__).resolve().parent.parent
GENERATED = "assets/generated"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _pairs(cards: list[Card]) -> list[str]:
    return [row(cards[i:i + 2]) for i in range(0, len(cards), 2)]


def build(root: Path = ROOT, today: date | None = None, get: Getter = http_get,
          token: str | None = None, log=print) -> str:
    today = today or date.today()
    profile = load_profile(root / "profile.yml", today)
    unknown = [i for i in profile.inventory if i not in ITEMS]
    if unknown:
        raise ConfigError(f"profile.yml: unknown inventory items: {', '.join(unknown)} "
                          f"(known: {', '.join(sorted(ITEMS))})")

    out = root / GENERATED
    cache_path = out / "cache.json"
    cache = load_cache(cache_path)
    files: dict[str, str] = {}

    def add(name: str, svg: str) -> str:
        files[name] = svg
        return f"{GENERATED}/{name}"

    def header(title: str) -> str:
        return row([Card(add(f"header-{_slug(title)}.svg", render_header(title)), title.title(), "100%")])

    lvl = level(profile.career_start_year, today)
    blocks = [row([Card(add("banner.svg", render_banner(profile, today)),
                        f"{profile.name}: Lv.{lvl} {profile.char_class}, {profile.title}", "100%")])]

    blocks.append(header("CHARACTER SHEET"))
    stats_alt = "Stats: " + ", ".join(f"{k} {v}" for k, v in profile.stats.items())
    inventory_alt = "Inventory: " + ", ".join(ITEMS[i][0] for i in profile.inventory)
    blocks.append(row([Card(add("stats.svg", render_stats(profile)), stats_alt, "49%"),
                       Card(add("inventory.svg", render_inventory(profile)), inventory_alt, "49%")]))

    blocks.append(header("QUEST LOG"))
    quest_cards = []
    for quest in profile.quests:
        stats = resolve(cache, f"repo:{quest.repo}", lambda q=quest: fetch_repo(q.repo, token, get),
                        encode_repo, decode_repo, log)
        src = add(f"quest-{_slug(quest.repo)}.svg", render_quest(quest, stats))
        quest_cards.append(Card(src, f"{quest.repo}: {quest.blurb or ''}".rstrip(": "), "49%",
                                f"https://github.com/{quest.repo}"))
    blocks += _pairs(quest_cards)

    blocks.append(header("RECENT SCROLLS"))
    feeds = [
        ("devto", lambda: fetch_devto(profile.devto_user, get), f"https://dev.to/{profile.devto_user}"),
        ("youtube", lambda: fetch_youtube(profile.youtube_channel_id, get),
         f"https://www.youtube.com/channel/{profile.youtube_channel_id}"),
    ]
    scroll_cards = []
    for source, fetch, home in feeds:
        items = resolve(cache, source, fetch, encode_items, decode_items, log) or []
        if not items:
            src = add(f"scroll-{source}-1.svg", render_sealed_scroll(source))
            scroll_cards.append(Card(src, f"{source}: visit the archive", "49%", home))
        for n, item in enumerate(items, start=1):
            src = add(f"scroll-{source}-{n}.svg", render_scroll(item, source))
            scroll_cards.append(Card(src, item.title, "49%", item.url or home))
    blocks += _pairs(scroll_cards)

    blocks.append(header("DUNGEON MAP"))
    blocks.append(pacman(profile.github_user))

    blocks.append(header("PORTALS"))
    blocks.append(row([Card(add(f"portal-{_slug(p.label)}.svg", render_portal(p)), p.label, "19%", p.url)
                       for p in profile.portals]))

    readme = render_readme(blocks)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        if old.name not in files:
            old.unlink()
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
    save_cache(cache_path, cache)
    (root / "README.md").write_text(readme, encoding="utf-8")
    return readme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the GitHub profile README.")
    parser.add_argument("--preview", action="store_true", help="also write preview.html")
    args = parser.parse_args(argv)
    try:
        readme = build(ROOT, token=os.environ.get("GITHUB_TOKEN"))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.preview:
        path = ROOT / "preview.html"
        path.write_text(render_preview(readme), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
