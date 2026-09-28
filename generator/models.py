"""Plain data carried between fetch, cache and render."""
from __future__ import annotations

from dataclasses import dataclass, fields


def _check_types(obj) -> None:
    """Reject wrong-typed values (e.g. a null title from a feed or a hand-edited cache)."""
    for f in fields(obj):
        value = getattr(obj, f.name)
        expected = {"str": str, "int": int}[f.type]
        if not isinstance(value, expected) or isinstance(value, bool):
            raise ValueError(f"{type(obj).__name__}.{f.name} must be {f.type}, got {value!r}")


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    published: str  # YYYY-MM-DD

    def __post_init__(self) -> None:
        _check_types(self)


@dataclass(frozen=True)
class RepoStats:
    description: str
    language: str
    stars: int

    def __post_init__(self) -> None:
        _check_types(self)
