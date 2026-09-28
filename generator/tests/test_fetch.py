import json

import pytest

from generator.fetch import (
    fetch_devto, fetch_repo, fetch_youtube, parse_devto, parse_repo, parse_youtube,
)
from generator.models import FeedItem, RepoStats

DEVTO = json.dumps([
    {"title": "Migrating to Swift 6 & <friends>", "url": "https://dev.to/biozal/a",
     "published_at": "2026-06-08T12:00:00Z"},
    {"title": "B", "url": "https://dev.to/biozal/b", "published_at": "2026-04-17T12:00:00Z"},
    {"title": "C", "url": "https://dev.to/biozal/c", "published_at": "2026-03-01T12:00:00Z"},
    {"title": "D", "url": "https://dev.to/biozal/d", "published_at": "2026-02-01T12:00:00Z"},
]).encode()

YOUTUBE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
 <title>Costoda Coding Bits</title>
 <entry><title>Coding SwiftUI with Ditto</title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=abc"/>
  <published>2025-10-01T10:00:00+00:00</published></entry>
 <entry><title> Second </title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=def"/>
  <published>2025-09-01T10:00:00+00:00</published></entry>
</feed>"""

REPO = json.dumps({"description": None, "language": "Swift", "stargazers_count": 6}).encode()


def test_parse_devto_limits_and_trims_dates():
    items = parse_devto(DEVTO)
    assert len(items) == 3
    assert items[0] == FeedItem("Migrating to Swift 6 & <friends>", "https://dev.to/biozal/a", "2026-06-08")


def test_parse_youtube():
    assert parse_youtube(YOUTUBE) == [
        FeedItem("Coding SwiftUI with Ditto", "https://www.youtube.com/watch?v=abc", "2025-10-01"),
        FeedItem("Second", "https://www.youtube.com/watch?v=def", "2025-09-01"),
    ]


def test_parse_youtube_empty_feed():
    assert parse_youtube(b'<feed xmlns="http://www.w3.org/2005/Atom"/>') == []


def test_parse_repo_null_description():
    assert parse_repo(REPO) == RepoStats("", "Swift", 6)


def test_fetchers_build_urls_and_headers():
    calls = []

    def get(url, headers=None):
        calls.append((url, headers))
        return {"dev.to": DEVTO, "youtube": YOUTUBE}.get(
            "dev.to" if "dev.to" in url else "youtube" if "youtube" in url else "", REPO)

    fetch_devto("biozal", get=get)
    fetch_youtube("UCX", get=get)
    fetch_repo("biozal/ttrpg-sfx", token="tok", get=get)
    assert calls[0][0] == "https://dev.to/api/articles?username=biozal&per_page=3"
    assert calls[1][0] == "https://www.youtube.com/feeds/videos.xml?channel_id=UCX"
    assert calls[2][0] == "https://api.github.com/repos/biozal/ttrpg-sfx"
    assert calls[2][1]["Authorization"] == "Bearer tok"


def test_malformed_payload_raises():
    with pytest.raises(Exception):
        parse_devto(b"<html>rate limited</html>")
