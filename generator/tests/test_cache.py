from generator.cache import (
    decode_items, decode_repo, encode_items, encode_repo, load_cache, resolve, save_cache,
)
from generator.models import FeedItem, RepoStats

ITEMS = [FeedItem("T", "https://x", "2026-01-01")]


def boom():
    raise OSError("network down")


def test_success_updates_cache():
    cache, logs = {}, []
    assert resolve(cache, "devto", lambda: ITEMS, encode_items, decode_items, logs.append) == ITEMS
    assert cache["devto"] == [{"title": "T", "url": "https://x", "published": "2026-01-01"}]
    assert logs == []


def test_failure_uses_cache():
    cache, logs = {"devto": encode_items(ITEMS)}, []
    assert resolve(cache, "devto", boom, encode_items, decode_items, logs.append) == ITEMS
    assert "network down" in logs[0] and "cached" in logs[0]


def test_failure_without_cache_returns_none():
    logs = []
    assert resolve({}, "devto", boom, encode_items, decode_items, logs.append) is None
    assert "no cached value" in logs[0]


def test_corrupt_cache_entry_returns_none():
    logs = []
    cache = {"repo:x/y": {"stars": "lots", "unexpected": 1}}
    assert resolve(cache, "repo:x/y", boom, encode_repo, decode_repo, logs.append) is None
    assert "unreadable" in logs[-1]


def test_load_and_save_roundtrip(tmp_path):
    path = tmp_path / "cache.json"
    assert load_cache(path) == {}
    save_cache(path, {"repo:a/b": encode_repo(RepoStats("d", "Go", 3))})
    assert decode_repo(load_cache(path)["repo:a/b"]) == RepoStats("d", "Go", 3)
    path.write_text("{not json")
    assert load_cache(path) == {}
