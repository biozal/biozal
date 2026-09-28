from dataclasses import replace
from datetime import date

from generator.render.banner import render_banner, xp_fraction
from generator.render.header import render_header
from generator.tests.conftest import TODAY
from generator.tests.svgcheck import SVG_NS, assert_valid_svg

def texts(root):
    return [t.text for t in root.iter(f"{SVG_NS}text")]


def test_banner_content(profile):
    svg = render_banner(profile, TODAY)
    root = assert_valid_svg(svg)
    assert root.get("viewBox") == "0 0 830 220"
    all_text = texts(root)
    assert "BIOZAL" in all_text
    assert "Lv.32 Artificer" in all_text
    assert "Developer Advocate @ Ditto" in all_text
    assert not any("PRESS START" in t for t in all_text), "no fake call-to-action: the banner isn't clickable"
    assert "blink" not in svg
    assert "LV.33" in all_text
    assert "<image" not in svg, "portrait lives in the GitHub avatar now"
    for t in root.iter(f"{SVG_NS}text"):
        assert t.get("text-anchor") == "middle"
    assert "@keyframes flick" in svg and "prefers-reduced-motion" in svg


def test_banner_fits_long_title(profile):
    long = replace(profile, title="Principal Staff Senior Developer Advocate and Community Wizard @ Ditto")
    root = assert_valid_svg(render_banner(long, TODAY))
    title = next(t for t in root.iter(f"{SVG_NS}text") if (t.text or "").startswith("Principal"))
    assert len(title.text) * int(title.get("font-size")) <= 830 - 240


def test_xp_fraction():
    assert xp_fraction(date(2026, 1, 1)) == 0.0
    assert 0.73 < xp_fraction(TODAY) < 0.74
    assert xp_fraction(date(2026, 12, 31)) < 1.0


def test_header():
    root = assert_valid_svg(render_header("QUEST LOG"))
    assert root.get("viewBox") == "0 0 830 40"
    assert texts(root) == ["QUEST LOG"]
