"""Plain data carried between fetch, cache and render."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    published: str  # YYYY-MM-DD


@dataclass(frozen=True)
class RepoStats:
    description: str
    language: str
    stars: int
