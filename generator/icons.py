"""16x16 pixel item icons. Shapes are shared; color gives each item its identity."""
from __future__ import annotations

from generator.pixel import PALETTE, grid_to_svg, shade

SHAPES: dict[str, list[str]] = {
    "potion": [
        "......oooo......",
        "......owwo......",
        "......oddo......",
        ".....oooooo.....",
        "......obbo......",
        "......obbo......",
        ".....oblbbo.....",
        "....oblbbbbo....",
        "...oblwbbbbbo...",
        "..obllbbbbbbdo..",
        "..oblbbbbbbbdo..",
        "..obbbbbbbbbdo..",
        "..obbbbbbbbddo..",
        "...obbbbbbddo...",
        "....oddddddo....",
        ".....oooooo.....",
    ],
    "gem": [
        "................",
        "................",
        "....oooooooo....",
        "...olwllbbbbo...",
        "..olwlllbbbbdo..",
        ".oooooooooooooo.",
        ".ollbbbbbbbbddo.",
        "..olbbbbbbbbdo..",
        "...olbbbbbbdo...",
        "....obbbbbbo....",
        ".....obbddo.....",
        "......obdo......",
        ".......oo.......",
        "................",
        "................",
        "................",
    ],
    "tome": [
        "................",
        "..oooooooooooo..",
        "..obbbbbbbbbbo..",
        "..oblllllllbbo..",
        "..oblwwwwwlbbo..",
        "..oblllllllbbo..",
        "..obbbbbbbbbbo..",
        "..obbbwwwbbbbo..",
        "..obbwbbbwbbbo..",
        "..obbbwwwbbbbo..",
        "..obbbbbbbbbbo..",
        "..obbbbbbbbbbo..",
        "..oddddddddddo..",
        "..owwwwwwwwwwo..",
        "..oooooooooooo..",
        "................",
    ],
    "scroll": [
        "................",
        "..oooooooooooo..",
        ".oddddddddddddo.",
        ".owwwwwwwwwwwwo.",
        "..owwwwwwwwwwo..",
        "..owbbbbbbbwwo..",
        "..owwwwwwwwwwo..",
        "..owbbbbbwwwwo..",
        "..owwwwwwwwwwo..",
        "..owbbbbbbwwwo..",
        "..owwwwwwwwwwo..",
        "..owbbbbwwwwwo..",
        "..owwwwwwwwwwo..",
        ".owwwwwwwwwwwwo.",
        ".oddddddddddddo.",
        "..oooooooooooo..",
    ],
    "gear": [
        "......oooo......",
        "...oo.obbo.oo...",
        "..obboobboobbo..",
        "...obbbbbbbbo...",
        "..obbbbllbbbbo..",
        "oobbbloooolbbboo",
        "obbbblo..olbbbbo",
        "obbbblo..obbbbdo",
        "obbbbbo..obbbbdo",
        "oobbbbboobbbbdoo",
        "..obbbbbbbbbdo..",
        "...obbbbbbbdo...",
        "..obdoobdoobdo..",
        "...oo.odbo.oo...",
        "......oooo......",
        "................",
    ],
    "shield": [
        "................",
        ".oooooooooooooo.",
        ".owllllbbbbbbdo.",
        ".olwlllbbbbbbdo.",
        ".ollllwbbbbbbdo.",
        ".obbbbbbbbbbbdo.",
        ".obbbbwwwwbbbdo.",
        ".obbbbwbbwbbbdo.",
        ".obbbbwbbwbbbdo.",
        "..obbbwwwwbbdo..",
        "..obbbbbbbbbdo..",
        "...obbbbbbbdo...",
        "....obbbbbdo....",
        ".....obbbdo.....",
        "......obdo......",
        ".......oo.......",
    ],
}

STAR = [
    "...o...",
    "..oyo..",
    "ooyyyoo",
    "oyyyyyo",
    ".oyyyo.",
    ".oyoyo.",
    "oo...oo",
]

# id -> (label shown under the icon, shape, base color)
ITEMS: dict[str, tuple[str, str, str]] = {
    "swift": ("SWIFT", "potion", "#f05138"),
    "kotlin": ("KOTLIN", "gem", "#a97bff"),
    "csharp": ("C#", "tome", "#9b4f96"),
    "typescript": ("TYPESCRIPT", "tome", "#3178c6"),
    "javascript": ("JAVASCRIPT", "scroll", "#e0c21a"),
    "java": ("JAVA", "potion", "#e76f00"),
    "c": ("C", "gear", "#a8b9cc"),
    "python": ("PYTHON", "gem", "#4b8bbe"),
    "rust": ("RUST", "gear", "#ce422b"),
    "flutter": ("FLUTTER", "gem", "#42a5f5"),
    "react-native": ("REACT NATIVE", "gem", "#61dafb"),
    "sqlite": ("SQLITE", "tome", "#0f80cc"),
    "mobile-db": ("MOBILE DB", "tome", "#2bb673"),
    "networking": ("NETWORKING", "gear", "#f0a040"),
    "iot": ("IOT", "gear", "#7ed957"),
    "ditto": ("DITTO", "shield", "#4a6cf7"),
}


def _colors(color: str) -> dict[str, str]:
    return {"o": PALETTE["outline"], "b": color, "l": shade(color, 0.45),
            "d": shade(color, -0.4), "w": "#fff6e0"}


def icon(shape: str, color: str, x, y, scale=2) -> str:
    return grid_to_svg(SHAPES[shape], _colors(color), x, y, scale)


def item_icon(item_id: str, x, y, scale=2) -> str:
    _, shape, color = ITEMS[item_id]
    return icon(shape, color, x, y, scale)


def star(x, y, scale=2) -> str:
    return grid_to_svg(STAR, {"o": PALETTE["outline"], "y": PALETTE["amber"]}, x, y, scale)
