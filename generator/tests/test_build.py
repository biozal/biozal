import json
import re
import shutil
from datetime import date

import pytest

from generator.build import build, main
from generator.config import ConfigError
from generator.tests.conftest import ROOT
from generator.tests.svgcheck import assert_valid_svg

TODAY = date(2026, 9, 27)
DEVTO = json.dumps([{"title": "Swift 6 & friends", "url": "https://dev.to/biozal/s6",
                     "published_at": "2026-06-08T00:00:00Z"}]).encode()
YOUTUBE = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Coding SwiftUI with Ditto</title>
<link href="https://www.youtube.com/watch?v=abc"/><published>2025-10-01T00:00:00Z</published></entry></feed>"""
REPO = json.dumps({"description": "desc", "language": "Swift", "stargazers_count": 6}).encode()


def good_get(url, headers=None):
    if "dev.to" in url:
        return DEVTO
    if "youtube.com" in url:
        return YOUTUBE
    return REPO


def bad_get(url, headers=None):
    raise OSError("offline")


@pytest.fixture
def root(tmp_path):
    shutil.copy(ROOT / "profile.yml", tmp_path / "profile.yml")
    return tmp_path


def run(root, get=good_get):
    return build(root, TODAY, get, None, log=lambda m: None)


def test_build_writes_readme_and_valid_svgs(root):
    readme = run(root)
    assert (root / "README.md").read_text() == readme
    srcs = re.findall(r'src="(assets/generated/[^"?]+)\?v=[0-9a-f]{10}"', readme)
    assert len(srcs) == len(set(srcs)) == 1 + 5 + 2 + 6 + 2 + 5
    for src in srcs:
        assert_valid_svg((root / src).read_text())
    for url in ["https://github.com/biozal/ditto-edge-studio", "https://dev.to/biozal/s6",
                "https://www.youtube.com/watch?v=abc", "https://docs.ditto.live",
                "https://www.linkedin.com/in/aaron-labeau-b444747/"]:
        assert f'href="{url}"' in readme
    assert "pacman-contribution-graph-dark.svg" in readme
    assert "Swift 6 &amp; friends" in (root / "assets/generated/scroll-devto-1.svg").read_text()


def test_offline_first_build_uses_sealed_scrolls(root):
    readme = run(root, bad_get)
    assert "THE SCROLLS ARE SEALED" in (root / "assets/generated/scroll-devto-1.svg").read_text()
    assert 'href="https://dev.to/biozal"' in readme
    assert 'href="https://www.youtube.com/channel/UCXgF-JqwBRGSawXajr6plGg"' in readme


def test_offline_rebuild_keeps_cached_content(root):
    run(root)
    run(root, bad_get)
    assert "Swift 6" in (root / "assets/generated/scroll-devto-1.svg").read_text()
    assert ">6</text>" in (root / "assets/generated/quest-biozal-ditto-edge-studio.svg").read_text()


def test_empty_feed_renders_sealed_scroll(root):
    def get(url, headers=None):
        return b"[]" if "dev.to" in url else good_get(url, headers)
    run(root, get)
    assert "SEALED" in (root / "assets/generated/scroll-devto-1.svg").read_text()


def test_stale_svgs_are_removed(root):
    run(root)
    stale = root / "assets/generated/quest-old-thing.svg"
    stale.write_text("<svg/>")
    run(root)
    assert not stale.exists()


def test_invalid_profile_writes_nothing(root):
    (root / "profile.yml").write_text("name: BIOZAL\n")
    with pytest.raises(ConfigError):
        run(root)
    assert not (root / "README.md").exists()
    assert not (root / "assets/generated").exists()


def test_unknown_inventory_item(root):
    text = (root / "profile.yml").read_text().replace("iot, ditto", "iot, cobol")
    (root / "profile.yml").write_text(text)
    with pytest.raises(ConfigError, match="cobol"):
        run(root)


def test_main_reports_config_errors(monkeypatch, capsys, root):
    (root / "profile.yml").write_text("name: BIOZAL\n")
    monkeypatch.setattr("generator.build.ROOT", root)
    assert main([]) == 1
    assert "error:" in capsys.readouterr().err


def test_image_links_change_when_content_changes(root):
    """Browsers cache images for minutes; a content-hash query makes updates show immediately."""
    before = re.search(r'src="assets/generated/banner.svg\?v=([0-9a-f]+)"', run(root)).group(1)
    same = re.search(r'src="assets/generated/banner.svg\?v=([0-9a-f]+)"', run(root)).group(1)
    (root / "profile.yml").write_text((root / "profile.yml").read_text().replace("name: BIOZAL", "name: BIOZAL2"))
    after = re.search(r'src="assets/generated/banner.svg\?v=([0-9a-f]+)"', run(root)).group(1)
    assert before == same != after
