"""Live data sources. Each fetcher raises on failure; build.py decides what to fall back to."""
from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from typing import Callable
from urllib.parse import quote

from generator.models import FeedItem, RepoStats

Getter = Callable[..., bytes]
USER_AGENT = "biozal-profile-generator (+https://github.com/biozal/biozal)"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def http_get(url: str, headers: dict | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_devto(payload: bytes, limit: int = 3) -> list[FeedItem]:
    return [FeedItem(a["title"], a["url"], a["published_at"][:10]) for a in json.loads(payload)[:limit]]


def parse_youtube(payload: bytes, limit: int = 3) -> list[FeedItem]:
    items = []
    for entry in ET.fromstring(payload).findall("a:entry", ATOM)[:limit]:
        link = entry.find("a:link", ATOM)
        items.append(FeedItem(
            title=(entry.findtext("a:title", "", ATOM) or "").strip(),
            url=link.get("href", "") if link is not None else "",
            published=(entry.findtext("a:published", "", ATOM) or "")[:10],
        ))
    return items


def parse_repo(payload: bytes) -> RepoStats:
    data = json.loads(payload)
    return RepoStats(data.get("description") or "", data.get("language") or "",
                     int(data.get("stargazers_count") or 0))


def fetch_devto(user: str, get: Getter = http_get) -> list[FeedItem]:
    return parse_devto(get(f"https://dev.to/api/articles?username={quote(user)}&per_page=3"))


def fetch_youtube(channel_id: str, get: Getter = http_get) -> list[FeedItem]:
    return parse_youtube(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={quote(channel_id)}"))


def fetch_repo(full_name: str, token: str | None = None, get: Getter = http_get) -> RepoStats:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return parse_repo(get(f"https://api.github.com/repos/{full_name}", headers))
