import pytest

from generator.icons import ITEMS, SHAPES, STAR, icon, item_icon, star
from generator.pixel import svg_doc
from generator.tests.svgcheck import assert_valid_svg


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_shapes_are_16x16_with_known_codes(name):
    rows = SHAPES[name]
    assert len(rows) == 16
    for row in rows:
        assert len(row) == 16, f"{name}: {row!r}"
        assert set(row) <= set(".obldw")


def test_star_is_7x7():
    assert len(STAR) == 7 and all(len(r) == 7 for r in STAR)


def test_items_reference_known_shapes_and_short_labels():
    for item_id, (label, shape, color) in ITEMS.items():
        assert shape in SHAPES, item_id
        assert len(label) <= 14, item_id
        assert color.startswith("#") and len(color) == 7, item_id


def test_profile_inventory_is_all_known(profile):
    assert [i for i in profile.inventory if i not in ITEMS] == []


def test_icons_render_valid_svg():
    body = icon("gem", "#ff0000", 0, 0, 2) + item_icon("swift", 40, 0) + star(80, 0)
    assert_valid_svg(svg_doc(120, 40, body))
    assert body.count("<rect") > 20
