from generator.config import Portal, Quest
from generator.models import FeedItem, RepoStats
from generator.render.inventory import render_inventory
from generator.render.portals import render_portal
from generator.render.quests import render_quest
from generator.render.scrolls import render_scroll, render_sealed_scroll
from generator.render.stats import render_stats
from generator.tests.svgcheck import SVG_NS, assert_valid_svg


def texts(svg):
    return [t.text for t in assert_valid_svg(svg).iter(f"{SVG_NS}text")]


def max_text_extent(svg):
    """Rightmost x reached by any start-anchored text: x + chars * font-size."""
    root = assert_valid_svg(svg)
    return max(float(t.get("x")) + len(t.text) * float(t.get("font-size"))
               for t in root.iter(f"{SVG_NS}text") if t.get("text-anchor") == "start")


def test_stats(profile):
    t = texts(render_stats(profile))
    for ability, line in [("MOB", "20 (+5)"), ("DAT", "19 (+4)"), ("CHA", "16 (+3)")]:
        assert ability in t and line in t
    assert "P2P SYNC" in t


def test_inventory_labels(profile):
    t = texts(render_inventory(profile))
    assert "SWIFT" in t and "REACT NATIVE" in t and "DITTO" in t
    assert len([x for x in t if x != "INVENTORY"]) == 16


def test_quest_uses_blurb_then_description():
    q = Quest("biozal/ttrpg-sfx", "side", "Local AI sound effects")
    t = texts(render_quest(q, RepoStats("repo description", "Shell", 2)))
    assert "SIDE QUEST" in t and "ttrpg-sfx" in t and "Local AI sound effects" in t
    assert "SHELL" in t and "2" in t
    t2 = texts(render_quest(Quest("a/b", "guild"), RepoStats("From GitHub", "", 0)))
    assert "GUILD QUEST" in t2 and "From GitHub" in t2


def test_quest_without_stats_has_no_star_count():
    t = texts(render_quest(Quest("a/b", "guild", "blurb"), None))
    assert t == ["GUILD QUEST", "b", "blurb"]


def test_quest_long_text_stays_inside_card():
    q = Quest("owner/" + "a-very-long-repository-name" * 3, "side", "word " * 60)
    svg = render_quest(q, RepoStats("", "TypeScript", 12345))
    assert max_text_extent(svg) <= 410 - 14


def test_scroll_escapes_and_wraps():
    item = FeedItem("Tips & <Tricks> for \"Swift 6\" 🚀 " + "long " * 30, "https://x", "2026-06-08")
    svg = render_scroll(item, "devto")
    assert "&amp;" in svg and "&lt;Tricks&gt;" in svg
    assert "DEV.TO" in texts(svg) and "2026-06-08" in texts(svg)
    assert max_text_extent(svg) <= 410 - 14


def test_sealed_scroll():
    t = texts(render_sealed_scroll("youtube"))
    assert "YOUTUBE" in t and "THE SCROLLS ARE SEALED..." in t


def test_portal():
    t = texts(render_portal(Portal("Ditto Docs", "https://docs.ditto.live")))
    assert t == ["DITTO DOCS"]
    assert max_text_extent(render_portal(Portal("A much longer portal label", "https://x"))) <= 160 - 6
