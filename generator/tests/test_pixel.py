import pytest

from generator.pixel import (
    PALETTE, bar, data_uri, esc, fit, font_face, grid_to_svg, shade, svg_doc,
    text, used_chars, window, wrap,
)
from generator.tests.svgcheck import assert_valid_svg


def test_esc_handles_markup_and_quotes():
    assert esc('a & <b> "c"') == "a &amp; &lt;b&gt; &quot;c&quot;"


def test_text_escapes_and_sets_class():
    t = text(1, 2, "R&D", 8, "#fff", cls="t blink")
    assert 'class="t blink"' in t and "R&amp;D" in t


@pytest.mark.parametrize("s,chars,lines,expected", [
    ("short", 10, 2, ["short"]),
    ("one two three four", 9, 2, ["one two", "three..."]),
    ("one two three", 9, 3, ["one two", "three"]),
    ("abcdefghijklmnop", 5, 4, ["abcde", "fghij", "klmno", "p"]),
    ("abcdefghijklmnop", 5, 2, ["abcde", "fg..."]),
    ("", 5, 2, []),
])
def test_wrap(s, chars, lines, expected):
    out = wrap(s, chars, lines)
    assert out == expected
    assert all(len(line) <= chars for line in out)


def test_fit_shrinks_then_truncates():
    assert fit("abc", 100, 10) == ("abc", 10)
    assert fit("abcdefghij", 70, 10) == ("abcdefghij", 7)
    s, size = fit("x" * 40, 60, 10, min_size=6)
    assert size == 6 and len(s) == 10 and s.endswith("...")


def test_grid_merges_runs_and_skips_dots():
    svg = grid_to_svg(["aab.", ".bb."], {"a": "#111", "b": "#222"}, 0, 0, 2)
    assert svg.count("<rect") == 3
    assert '<rect x="0" y="0" width="4" height="2" fill="#111"/>' in svg


def test_shade():
    assert shade("#808080", 1.0) == "#ffffff"
    assert shade("#808080", -1.0) == "#000000"
    assert shade("#000000", 0.5) == "#808080"


def test_bar_fill_count():
    full = bar(0, 0, 100, 10, 1.0)
    half = bar(0, 0, 100, 10, 0.5)
    empty = bar(0, 0, 100, 10, -3)
    assert full.count("<rect") == 2 + 12
    assert half.count("<rect") == 2 + 6
    assert empty.count("<rect") == 2


def test_window_title_tab():
    w = window(0, 0, 200, 100, "STATS")
    assert "STATS" in w
    assert "<text" not in window(0, 0, 200, 100)


def test_used_chars_unescapes_and_dedupes():
    body = text(0, 0, "A&A") + text(0, 0, "b")
    assert used_chars(body) == "&Ab"


def test_svg_doc_is_valid_and_embeds_font_only_with_text():
    with_text = svg_doc(10, 10, text(0, 8, "Hi & <you> 🚀 日本"))
    root = assert_valid_svg(with_text)
    assert root.get("viewBox") == "0 0 10 10"
    assert "@font-face" in with_text and "base64," in with_text
    assert "@font-face" not in svg_doc(10, 10, "<rect/>")


def test_font_subset_is_small():
    assert len(font_face("ABC")) < 20_000


def test_data_uri():
    assert data_uri(b"\x89PNG") == "data:image/png;base64,iVBORw=="


def test_palette_has_accent():
    assert PALETTE["accent"] == "#85adff"


def test_font_subset_is_deterministic():
    """Subset fonts must not stamp the build time, or every nightly build rewrites every SVG."""
    import base64
    import io
    import re as _re

    from fontTools.ttLib import TTFont

    from generator.pixel import FONT_PATH

    rule = font_face("DET")
    data = base64.b64decode(_re.search(r"base64,([^)]+)\)", rule).group(1))
    subset_head = TTFont(io.BytesIO(data))["head"]
    original_head = TTFont(FONT_PATH)["head"]
    assert subset_head.modified == original_head.modified
