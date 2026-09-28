"""Last-known-good values for live data, so a flaky feed never blanks the profile."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, TypeVar

from generator.models import FeedItem, RepoStats

T = TypeVar("T")


def load_cache(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):  # missing, unreadable, non-UTF-8 or invalid JSON
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(path: Path, cache: dict) -> None:
    Path(path).write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve(cache: dict, key: str, fetch: Callable[[], T], encode: Callable[[T], object],
            decode: Callable[[object], T], log: Callable[[str], None] = print) -> T | None:
    try:
        value = fetch()
    except Exception as exc:  # any failure (network, HTTP, parse) falls back to the cache
        if key not in cache:
            log(f"warning: {key}: {exc}; no cached value")
            return None
        log(f"warning: {key}: {exc}; using cached value")
        try:
            return decode(cache[key])
        except (TypeError, ValueError, KeyError) as bad:
            log(f"warning: {key}: cached value unreadable ({bad})")
            return None
    cache[key] = encode(value)
    return value


def encode_items(items: list[FeedItem]) -> list[dict]:
    return [asdict(i) for i in items]


def decode_items(raw: object) -> list[FeedItem]:
    return [FeedItem(**r) for r in raw]


def encode_repo(stats: RepoStats) -> dict:
    return asdict(stats)


def decode_repo(raw: object) -> RepoStats:
    return RepoStats(**raw)
