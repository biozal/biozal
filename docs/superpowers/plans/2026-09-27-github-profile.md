# Pixel-Art Character Sheet Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python generator that turns `profile.yml` plus live feeds into pixel-art SVGs and a `README.md` for the `biozal/biozal` GitHub profile, refreshed nightly by GitHub Actions.

**Architecture:** `profile.yml` → `config` (validated dataclass) → `fetch` (dev.to, YouTube, GitHub, with a JSON cache fallback) → pure `render/*` functions that each return one SVG string → `build` writes `assets/generated/*.svg`, `cache.json` and `README.md`. Every clickable element is its own SVG wrapped in a link. Text uses an embedded, per-SVG subset of Press Start 2P.

**Tech Stack:** Python 3.12 (CI) / 3.12+ locally, `pyyaml`, `fonttools` (font subsetting only), `pytest`; GitHub Actions; `abozanona/pacman-contribution-graph`.

**Spec:** `docs/superpowers/specs/2026-09-27-github-profile-design.md`

## Global Constraints

- Runtime dependencies: `pyyaml` and `fonttools` only (fonttools implements the spec's "subset where practical" for the embedded font). No image libraries at build time.
- `render/*` and `pixel.py` functions are pure: no network and no file I/O (the one exception is `pixel.py` reading the font file once).
- Every generated SVG has `xmlns`, a `viewBox`, and `shape-rendering="crispEdges"`, and parses as XML.
- All user or feed text goes through `pixel.esc()` before entering SVG or HTML.
- GitHub strips CSS and JS from READMEs: all animation lives inside SVGs as CSS `@keyframes`, with a `prefers-reduced-motion` opt-out.
- Content width is 830 units. Full-width images are `width="100%"`, half-width `width="49%"`, portals `width="19%"`.
- Palette constants live only in `generator/pixel.py:PALETTE`. Link accent is `#85adff`.
- Level = current year − `career_start_year` (1994 → Lv.32 in 2026). Modifier = floor((score − 10) / 2).
- A feed or GitHub API failure never fails the build: it falls back to `cache.json`, then to a sealed or star-less card.
- An invalid `profile.yml` fails the build before any file is written.
- Commit author for bot commits: `github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>`.
- Run everything from the repo root, using `.venv/bin/python`.

## Review Focus

1. Feed titles with `&`, `<`, quotes, emoji or non-Latin text → escaped, valid SVG; missing glyphs fall back to monospace rather than breaking (pinned in Task 2 and Task 7).
2. Very long titles, repo names and blurbs → wrapped or truncated with `...` inside their card, never overflowing (pinned in Task 2 and Task 6).
3. A feed returning zero items, or a repo that 404s → sealed scroll card or quest card without stars; the build still succeeds (pinned in Task 7).
4. A corrupt or old-format `cache.json` entry → treated as "no cache", not a crash (pinned in Task 5).
5. A quest or portal removed from `profile.yml` → its old SVG is deleted from `assets/generated/`, so no orphaned files accumulate (pinned in Task 7).

---

## File Structure

| Path | Responsibility |
|---|---|
| `profile.yml` | All editable content |
| `requirements.txt`, `pytest.ini`, `.gitignore` | Tooling |
| `assets/portrait.png` | 200×200 hero sprite (committed source art) |
| `assets/fonts/PressStart2P-Regular.ttf`, `assets/fonts/OFL.txt` | Font plus license |
| `assets/generated/` | Build output: SVGs and `cache.json` |
| `generator/models.py` | `FeedItem`, `RepoStats` dataclasses |
| `generator/config.py` | Load and validate `profile.yml`; `level`, `modifier` |
| `generator/pixel.py` | Palette, SVG document, text, wrap, window, grid, bar helpers |
| `generator/icons.py` | 16×16 item shapes, item catalog, star |
| `generator/render/banner.py` | Title-screen banner |
| `generator/render/header.py` | Section header plates |
| `generator/render/stats.py` | Ability-score block |
| `generator/render/inventory.py` | 4×4 item grid |
| `generator/render/quests.py` | Quest cards |
| `generator/render/scrolls.py` | Blog and video cards, plus the sealed fallback |
| `generator/render/portals.py` | Link buttons |
| `generator/fetch.py` | HTTP and parsers for dev.to, YouTube, GitHub |
| `generator/cache.py` | Cache load/save and the fetch-with-fallback helper |
| `generator/readme.py` | README HTML assembly and preview page |
| `generator/build.py` | Orchestration and CLI |
| `generator/tests/` | Tests; `svgcheck.py` holds shared assertions |
| `.github/workflows/build.yml`, `pacman.yml` | Automation |

---

### Task 1: Scaffold, models and config

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `.gitignore`, `profile.yml`
- Create: `generator/__init__.py`, `generator/render/__init__.py`, `generator/tests/__init__.py`
- Create: `generator/models.py`, `generator/config.py`
- Create: `generator/tests/conftest.py`, `generator/tests/svgcheck.py`, `generator/tests/test_config.py`

**Interfaces:**
- Produces: `generator.models.FeedItem(title: str, url: str, published: str)` and `generator.models.RepoStats(description: str, language: str, stars: int)`, both frozen dataclasses.
- Produces: `generator.config`: `ABILITIES: tuple[str, ...]`, `ConfigError(ValueError)`, `Portal(label, url)`, `Quest(repo, kind, blurb=None)` with a `.name` property, `Profile(...)` (fields below), `load_profile(path: Path, today: date | None = None) -> Profile`, `parse_profile(data: object, today: date | None = None) -> Profile`, `level(career_start_year: int, today: date) -> int`, `modifier(score: int) -> int`, `format_modifier(score: int) -> str`.
- Produces: the pytest fixture `profile` (the real `profile.yml` loaded with today = 2026-09-27) and `TODAY`; `generator.tests.svgcheck.assert_valid_svg(svg: str) -> Element`.

- [ ] **Step 1: Create the tooling files**

`requirements.txt`:
```
pyyaml>=6.0.3
fonttools>=4.59
pytest>=8.4
```

`pytest.ini`:
```ini
[pytest]
testpaths = generator/tests
pythonpath = .
```

`.gitignore`:
```
.venv/
__pycache__/
.pytest_cache/
preview.html
```

Create empty `generator/__init__.py`, `generator/render/__init__.py`, `generator/tests/__init__.py`.

Then run:
```bash
uv venv --python 3.12 .venv && uv pip install --python .venv -r requirements.txt
```
Expected: installs pyyaml, fonttools, pytest.

- [ ] **Step 2: Create `profile.yml`**

```yaml
# Everything on the profile comes from this file. Edit it; never edit README.md.
name: BIOZAL
real_name: Aaron LaBeau
github_user: biozal
title: Developer Advocate @ Ditto
class: Artificer
career_start_year: 1994
stats: { MOB: 20, DAT: 19, NET: 17, BAK: 16, SYN: 18, CHA: 16 }
inventory: [swift, kotlin, csharp, typescript, javascript, java, c, python,
            rust, flutter, react-native, sqlite, mobile-db, networking, iot, ditto]
quests:
  guild:
    - repo: biozal/ditto-edge-studio
      blurb: Query, sync and inspect Ditto databases on macOS and Android
    - repo: ditto-examples/ditto-whiteboard-datastreams
      blurb: Whiteboard demo built on the Ditto Data Stream API
    - repo: ditto-examples/demoapp-retail
      blurb: Retail demo app built on Ditto
  side:
    - repo: biozal/cartyx-app
      blurb: D&D campaign manager with a retro pixel-art UI
    - repo: biozal/cartyx-sim
      blurb: An AI Dungeon Master and four AI players on local models
    - repo: biozal/ttrpg-sfx
      blurb: Local AI sound effects and music for tabletop RPGs
feeds:
  devto_user: biozal
  youtube_channel_id: UCXgF-JqwBRGSawXajr6plGg
portals:
  - { label: dev.to,       url: "https://dev.to/biozal/" }
  - { label: costoda.tech, url: "https://costoda.tech/#blog" }
  - { label: YouTube,      url: "https://www.youtube.com/costoda" }
  - { label: LinkedIn,     url: "https://www.linkedin.com/in/aaron-labeau-b444747/" }
  - { label: Ditto Docs,   url: "https://docs.ditto.live" }
```

- [ ] **Step 3: Create `generator/models.py`**

```python
"""Plain data carried between fetch, cache and render."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    published: str  # YYYY-MM-DD


@dataclass(frozen=True)
class RepoStats:
    description: str
    language: str
    stars: int
```

- [ ] **Step 4: Create the test helpers**

`generator/tests/svgcheck.py`:
```python
import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"


def assert_valid_svg(svg: str) -> ET.Element:
    root = ET.fromstring(svg)
    assert root.tag == f"{SVG_NS}svg"
    assert root.get("viewBox"), "svg must have a viewBox"
    assert root.get("shape-rendering") == "crispEdges"
    return root
```

`generator/tests/conftest.py`:
```python
from datetime import date
from pathlib import Path

import pytest

from generator.config import load_profile

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 9, 27)


@pytest.fixture
def profile():
    return load_profile(ROOT / "profile.yml", TODAY)
```

- [ ] **Step 5: Write the failing tests**

`generator/tests/test_config.py`:
```python
import copy
from datetime import date

import pytest
import yaml

from generator.config import (
    ConfigError, Quest, format_modifier, level, modifier, parse_profile,
)
from generator.tests.conftest import ROOT, TODAY

RAW = yaml.safe_load((ROOT / "profile.yml").read_text())


def raw():
    return copy.deepcopy(RAW)


def test_real_profile_loads(profile):
    assert profile.name == "BIOZAL"
    assert profile.github_user == "biozal"
    assert profile.char_class == "Artificer"
    assert profile.stats["MOB"] == 20
    assert len(profile.inventory) == 16
    assert [q.kind for q in profile.quests] == ["guild"] * 3 + ["side"] * 3
    assert profile.quests[0] == Quest(
        "biozal/ditto-edge-studio", "guild",
        "Query, sync and inspect Ditto databases on macOS and Android")
    assert profile.quests[0].name == "ditto-edge-studio"
    assert profile.portals[0].label == "dev.to"


@pytest.mark.parametrize("score,mod,text", [
    (20, 5, "+5"), (19, 4, "+4"), (18, 4, "+4"), (11, 0, "+0"),
    (10, 0, "+0"), (9, -1, "-1"), (8, -1, "-1"), (1, -5, "-5"),
])
def test_modifier(score, mod, text):
    assert modifier(score) == mod
    assert format_modifier(score) == text


def test_level():
    assert level(1994, date(2026, 9, 27)) == 32
    assert level(1994, date(2027, 1, 1)) == 33


def test_quest_accepts_plain_string():
    data = raw()
    data["quests"] = {"side": ["biozal/ttrpg-sfx"]}
    assert parse_profile(data, TODAY).quests == [Quest("biozal/ttrpg-sfx", "side", None)]


@pytest.mark.parametrize("mutate,message", [
    (lambda d: d.pop("name"), "missing 'name'"),
    (lambda d: d.update(career_start_year="1994"), "'career_start_year' must be int"),
    (lambda d: d.update(career_start_year=2030), "career_start_year"),
    (lambda d: d["stats"].update(MOB=21), "stats.MOB"),
    (lambda d: d["stats"].update(MOB=True), "stats.MOB"),
    (lambda d: d["stats"].pop("CHA"), "stats must be exactly"),
    (lambda d: d.update(inventory=["swift"] * 17), "at most 16"),
    (lambda d: d["quests"].update(side=["not-a-repo"]), "owner/repo"),
    (lambda d: d["quests"].update(side=[{"blurb": "x"}]), "owner/repo"),
    (lambda d: d["portals"].append({"label": "x", "url": "http://x.com"}), "https://"),
    (lambda d: d["feeds"].pop("devto_user"), "missing 'devto_user'"),
])
def test_invalid_profile(mutate, message):
    data = raw()
    mutate(data)
    with pytest.raises(ConfigError, match=message):
        parse_profile(data, TODAY)


def test_non_mapping_rejected():
    with pytest.raises(ConfigError, match="mapping"):
        parse_profile(["nope"], TODAY)
```

- [ ] **Step 6: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_config.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'generator.config'`.

- [ ] **Step 7: Implement `generator/config.py`**

```python
"""Load and validate profile.yml into a typed Profile."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

ABILITIES = ("MOB", "DAT", "NET", "BAK", "SYN", "CHA")
QUEST_KINDS = ("guild", "side")
MAX_INVENTORY = 16


class ConfigError(ValueError):
    """profile.yml is missing data or holds invalid values."""


@dataclass(frozen=True)
class Portal:
    label: str
    url: str


@dataclass(frozen=True)
class Quest:
    repo: str
    kind: str
    blurb: str | None = None

    @property
    def name(self) -> str:
        return self.repo.split("/", 1)[1]


@dataclass(frozen=True)
class Profile:
    name: str
    real_name: str
    github_user: str
    title: str
    char_class: str
    career_start_year: int
    stats: dict[str, int]
    inventory: list[str]
    quests: list[Quest]
    devto_user: str
    youtube_channel_id: str
    portals: list[Portal]


def level(career_start_year: int, today: date) -> int:
    return today.year - career_start_year


def modifier(score: int) -> int:
    return (score - 10) // 2


def format_modifier(score: int) -> str:
    m = modifier(score)
    return f"+{m}" if m >= 0 else str(m)


def _require(data: dict, key: str, kind: type):
    if key not in data:
        raise ConfigError(f"profile.yml: missing '{key}'")
    value = data[key]
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        raise ConfigError(f"profile.yml: '{key}' must be {kind.__name__}")
    return value


def _is_repo(value: object) -> bool:
    if not isinstance(value, str) or value.count("/") != 1:
        return False
    owner, name = value.split("/")
    return bool(owner) and bool(name)


def _parse_quests(raw: dict) -> list[Quest]:
    quests = []
    for kind in QUEST_KINDS:
        for entry in raw.get(kind) or []:
            if isinstance(entry, str):
                repo, blurb = entry, None
            elif isinstance(entry, dict):
                repo, blurb = entry.get("repo"), entry.get("blurb")
            else:
                repo, blurb = None, None
            if not _is_repo(repo) or not (blurb is None or isinstance(blurb, str)):
                raise ConfigError(
                    f"profile.yml: quests.{kind} entries must be 'owner/repo' or {{repo: owner/repo, blurb: text}}")
            quests.append(Quest(repo, kind, blurb))
    return quests


def _parse_portals(raw: list) -> list[Portal]:
    portals = []
    for entry in raw:
        if not isinstance(entry, dict) or not isinstance(entry.get("label"), str):
            raise ConfigError("profile.yml: each portal needs a label and url")
        url = entry.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ConfigError(f"profile.yml: portal '{entry['label']}' url must start with https://")
        portals.append(Portal(entry["label"], url))
    return portals


def parse_profile(data: object, today: date | None = None) -> Profile:
    today = today or date.today()
    if not isinstance(data, dict):
        raise ConfigError("profile.yml: top level must be a mapping")

    start = _require(data, "career_start_year", int)
    if not 1950 <= start <= today.year:
        raise ConfigError(f"profile.yml: career_start_year must be between 1950 and {today.year}")

    stats = _require(data, "stats", dict)
    if set(stats) != set(ABILITIES):
        raise ConfigError(f"profile.yml: stats must be exactly {', '.join(ABILITIES)}")
    for key, value in stats.items():
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 20:
            raise ConfigError(f"profile.yml: stats.{key} must be an integer from 1 to 20")

    inventory = _require(data, "inventory", list)
    if len(inventory) > MAX_INVENTORY or not all(isinstance(i, str) for i in inventory):
        raise ConfigError(f"profile.yml: inventory must be a list of at most {MAX_INVENTORY} item ids")

    feeds = _require(data, "feeds", dict)
    return Profile(
        name=_require(data, "name", str),
        real_name=_require(data, "real_name", str),
        github_user=_require(data, "github_user", str),
        title=_require(data, "title", str),
        char_class=_require(data, "class", str),
        career_start_year=start,
        stats={k: stats[k] for k in ABILITIES},
        inventory=list(inventory),
        quests=_parse_quests(_require(data, "quests", dict)),
        devto_user=_require(feeds, "devto_user", str),
        youtube_channel_id=_require(feeds, "youtube_channel_id", str),
        portals=_parse_portals(_require(data, "portals", list)),
    )


def load_profile(path: Path, today: date | None = None) -> Profile:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"profile.yml: invalid YAML: {exc}") from exc
    return parse_profile(data, today)
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_config.py -q`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add requirements.txt pytest.ini .gitignore profile.yml generator
git commit -m "feat: add profile config, models and project scaffold"
```

---

### Task 2: Assets and pixel toolkit

**Files:**
- Create: `assets/portrait.png`, `assets/fonts/PressStart2P-Regular.ttf`, `assets/fonts/OFL.txt`
- Create: `generator/pixel.py`
- Test: `generator/tests/test_pixel.py`

**Interfaces:**
- Produces, in `generator.pixel`:
  - `PALETTE: dict[str, str]`
  - `esc(s: str) -> str`
  - `rect(x, y, w, h, fill: str, extra: str = "") -> str`
  - `text(x, y, s: str, size: int = 8, fill: str = PALETTE["text"], anchor: str = "start", cls: str = "t") -> str`
  - `text_width(s: str, size: int) -> int`
  - `fit(s: str, max_width: int, max_size: int, min_size: int = 6) -> tuple[str, int]`
  - `wrap(s: str, max_chars: int, max_lines: int) -> list[str]`
  - `window(x, y, w, h, title: str | None = None) -> str`
  - `grid_to_svg(rows: list[str], colors: dict[str, str], x, y, scale=1) -> str`
  - `bar(x, y, w, h, frac: float, fill: str = PALETTE["amber"]) -> str`
  - `shade(hex_color: str, amount: float) -> str`
  - `data_uri(png: bytes) -> str`
  - `used_chars(body: str) -> str`
  - `font_face(chars: str) -> str`
  - `svg_doc(width: int, height: int, body: str, css: str = "", defs: str = "") -> str`

- [ ] **Step 1: Add the assets**

```bash
mkdir -p assets/fonts
cp /private/tmp/claude-501/-Users-labeaaa-Developer-biozal/9bf1ee04-81e1-4f2e-bffa-2d706c6762af/scratchpad/final_64c.png assets/portrait.png
curl -sSfL -o assets/fonts/PressStart2P-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/PressStart2P-Regular.ttf
curl -sSfL -o assets/fonts/OFL.txt https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/OFL.txt
sips -g pixelWidth -g pixelHeight assets/portrait.png
```
Expected: `pixelWidth: 200`, `pixelHeight: 200`. If the scratchpad file is gone, stop and ask the user for the approved 200×200 portrait.

- [ ] **Step 2: Write the failing tests**

`generator/tests/test_pixel.py`:
```python
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
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_pixel.py -q`
Expected: `ModuleNotFoundError: No module named 'generator.pixel'`.

- [ ] **Step 4: Implement `generator/pixel.py`**

```python
"""Shared pixel-art SVG building blocks. Pure string builders; the font file is the only thing read."""
from __future__ import annotations

import base64
import html
import io
import re
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"

# Warm torchlit-dungeon palette sampled from the portrait, plus the Cartyx blue accent.
PALETTE = {
    "bg": "#120b16",
    "panel": "#1d1220",
    "panel_dark": "#150d18",
    "brick": "#2a1a24",
    "border": "#5a3a2a",
    "border_hi": "#c8792e",
    "shadow": "#07040a",
    "outline": "#1a0f14",
    "amber": "#f0a040",
    "orange": "#d8642a",
    "parchment": "#f1dfb8",
    "parchment_dark": "#c9a877",
    "ink": "#2a1a12",
    "text": "#f1dfb8",
    "muted": "#a08870",
    "accent": "#85adff",
}

_TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)


def esc(s: str) -> str:
    return escape(s, {'"': "&quot;"})


def rect(x, y, w, h, fill: str, extra: str = "") -> str:
    tail = f" {extra}" if extra else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{tail}/>'


def text(x, y, s: str, size: int = 8, fill: str = PALETTE["text"], anchor: str = "start",
         cls: str = "t") -> str:
    return (f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def text_width(s: str, size: int) -> int:
    """Press Start 2P is monospaced with a 1em advance."""
    return len(s) * size


def fit(s: str, max_width: int, max_size: int, min_size: int = 6) -> tuple[str, int]:
    """Shrink the font to fit; below min_size, truncate with '...'."""
    size = max(min_size, min(max_size, max_width // max(1, len(s))))
    max_chars = max_width // size
    if len(s) > max_chars:
        s = s[: max_chars - 3].rstrip() + "..."
    return s, size


def wrap(s: str, max_chars: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in s.split():
        while len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:max_chars])
            word = word[max_chars:]
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        lines = lines[: max_lines - 1] + [last[: max_chars - 3].rstrip() + "..."]
    return lines


def window(x, y, w, h, title: str | None = None) -> str:
    """Dark game window with a notched pixel border and an optional title tab."""
    p = PALETTE
    parts = [
        rect(x + 2, y, w - 4, h, p["shadow"]),
        rect(x, y + 2, w, h - 4, p["shadow"]),
        rect(x + 2, y + 2, w - 4, h - 4, p["border_hi"]),
        rect(x + 4, y + 4, w - 8, h - 8, p["border"]),
        rect(x + 6, y + 6, w - 12, h - 12, p["panel"]),
    ]
    if title:
        parts.append(rect(x + 14, y, text_width(title, 8) + 12, 14, p["border_hi"]))
        parts.append(text(x + 20, y + 11, title, 8, p["ink"]))
    return "".join(parts)


def grid_to_svg(rows: list[str], colors: dict[str, str], x, y, scale=1) -> str:
    """Draw a character grid; '.' is transparent and horizontal runs merge into one rect."""
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == ".":
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == ch:
                c += 1
            out.append(rect(x + start * scale, y + r * scale, (c - start) * scale, scale, colors[ch]))
    return "".join(out)


def bar(x, y, w, h, frac: float, fill: str = PALETTE["amber"]) -> str:
    """Segmented stat bar: 6-unit blocks with 2-unit gaps."""
    frac = max(0.0, min(1.0, frac))
    parts = [rect(x, y, w, h, PALETTE["shadow"]), rect(x + 1, y + 1, w - 2, h - 2, PALETTE["panel_dark"])]
    segments = (w - 4) // 8
    for i in range(round(segments * frac)):
        parts.append(rect(x + 2 + i * 8, y + 2, 6, h - 4, fill))
    return "".join(parts)


def shade(hex_color: str, amount: float) -> str:
    """amount > 0 mixes toward white, amount < 0 toward black."""
    target = 255 if amount > 0 else 0
    a = abs(amount)
    channels = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(v + (target - v) * a):02x}" for v in channels)


def data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def used_chars(body: str) -> str:
    chars: set[str] = set()
    for inner in _TEXT_RE.findall(body):
        chars.update(html.unescape(inner))
    return "".join(sorted(chars))


@lru_cache(maxsize=1)
def _font_bytes() -> bytes:
    return FONT_PATH.read_bytes()


@lru_cache(maxsize=256)
def font_face(chars: str) -> str:
    """@font-face rule embedding Press Start 2P subset to `chars`; missing glyphs fall back to monospace."""
    font = TTFont(io.BytesIO(_font_bytes()))
    subsetter = subset.Subsetter(subset.Options())
    subsetter.populate(text=chars)
    subsetter.subset(font)
    out = io.BytesIO()
    font.save(out)
    data = base64.b64encode(out.getvalue()).decode("ascii")
    return f"@font-face{{font-family:'PS2P';src:url(data:font/ttf;base64,{data}) format('truetype');}}"


def svg_doc(width: int, height: int, body: str, css: str = "", defs: str = "") -> str:
    chars = used_chars(body)
    font_css = font_face(chars) if chars else ""
    style = f"{font_css}.t{{font-family:'PS2P',monospace;}}{css}"
    defs_block = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
            f"<style>{style}</style>{defs_block}{body}</svg>")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_pixel.py -q`
Expected: all pass. fontTools may log a "Missing glyphs" warning for 🚀/日本. That is expected: those characters fall back to monospace.

- [ ] **Step 6: Commit**

```bash
git add assets/portrait.png assets/fonts generator/pixel.py generator/tests/test_pixel.py
git commit -m "feat: add pixel SVG toolkit, portrait and Press Start 2P font"
```

---

### Task 3: Item icons

**Files:**
- Create: `generator/icons.py`
- Test: `generator/tests/test_icons.py`

**Interfaces:**
- Consumes: `generator.pixel.grid_to_svg`, `shade`, `PALETTE`.
- Produces, in `generator.icons`:
  - `SHAPES: dict[str, list[str]]`, keys `potion`, `gem`, `tome`, `scroll`, `gear`, `shield`
  - `ITEMS: dict[str, tuple[str, str, str]]`, mapping id → (label, shape, hex color)
  - `icon(shape: str, color: str, x, y, scale=2) -> str`
  - `item_icon(item_id: str, x, y, scale=2) -> str`
  - `star(x, y, scale=2) -> str`

- [ ] **Step 1: Write the failing tests**

`generator/tests/test_icons.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_icons.py -q`
Expected: `ModuleNotFoundError: No module named 'generator.icons'`.

- [ ] **Step 3: Implement `generator/icons.py`**

Grid codes: `o` outline, `b` base color, `l` light, `d` dark, `w` highlight or paper.

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_icons.py -q`
Expected: all pass. If a shape row fails its length check, fix that row so it is exactly 16 characters, keeping the drawing symmetric.

- [ ] **Step 5: Commit**

```bash
git add generator/icons.py generator/tests/test_icons.py
git commit -m "feat: add pixel item icon set"
```

---

### Task 4: Title banner and section headers

**Files:**
- Create: `generator/render/banner.py`, `generator/render/header.py`
- Test: `generator/tests/test_banner.py`

**Interfaces:**
- Consumes: `Profile`, `level` (Task 1); `PALETTE`, `svg_doc`, `window`, `rect`, `text`, `fit`, `grid_to_svg`, `bar`, `data_uri`, `text_width` (Task 2).
- Produces: `generator.render.banner.render_banner(profile: Profile, portrait_png: bytes, today: date) -> str` (830×300) and `xp_fraction(today: date) -> float`; `generator.render.header.render_header(title: str) -> str` (830×40).

- [ ] **Step 1: Write the failing tests**

`generator/tests/test_banner.py`:
```python
from datetime import date

from generator.render.banner import render_banner, xp_fraction
from generator.render.header import render_header
from generator.tests.conftest import ROOT, TODAY
from generator.tests.svgcheck import SVG_NS, assert_valid_svg

PORTRAIT = (ROOT / "assets" / "portrait.png").read_bytes()


def texts(root):
    return [t.text for t in root.iter(f"{SVG_NS}text")]


def test_banner_content(profile):
    svg = render_banner(profile, PORTRAIT, TODAY)
    root = assert_valid_svg(svg)
    assert root.get("viewBox") == "0 0 830 300"
    all_text = texts(root)
    assert "BIOZAL" in all_text
    assert "Lv.32 Artificer" in all_text
    assert "Developer Advocate @ Ditto" in all_text
    assert "> PRESS START" in all_text
    assert "LV.33" in all_text
    assert "data:image/png;base64," in svg
    assert "@keyframes flick" in svg and "prefers-reduced-motion" in svg


def test_banner_fits_long_title(profile):
    from dataclasses import replace
    long = replace(profile, title="Principal Staff Senior Developer Advocate and Community Wizard @ Ditto")
    root = assert_valid_svg(render_banner(long, PORTRAIT, TODAY))
    title = next(t for t in root.iter(f"{SVG_NS}text") if (t.text or "").startswith("Principal"))
    assert len(title.text) * int(title.get("font-size")) <= 830 - 340


def test_xp_fraction():
    assert xp_fraction(date(2026, 1, 1)) == 0.0
    assert 0.73 < xp_fraction(TODAY) < 0.74
    assert xp_fraction(date(2026, 12, 31)) < 1.0


def test_header():
    root = assert_valid_svg(render_header("QUEST LOG"))
    assert root.get("viewBox") == "0 0 830 40"
    assert texts(root) == ["QUEST LOG"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_banner.py -q`
Expected: `ModuleNotFoundError: No module named 'generator.render.banner'`.

- [ ] **Step 3: Implement `generator/render/banner.py`**

```python
"""Title-screen banner: portrait, flickering torches, name, level and a blinking PRESS START."""
from __future__ import annotations

import calendar
from datetime import date

from generator.config import Profile, level
from generator.pixel import PALETTE as P, bar, data_uri, fit, grid_to_svg, rect, svg_doc, text, window

W, H = 830, 300
TEXT_X = 320
TEXT_MAX_W = W - 340

FLAME = [
    "..y..",
    ".yy..",
    ".ywy.",
    "yywyo",
    "ywwyo",
    "oyyyo",
    ".ooo.",
]
FLAME_COLORS = {"y": "#ffd060", "w": "#fff4c0", "o": "#e8641e"}

CSS = (
    "@keyframes flick{0%,100%{opacity:1;transform:scaleY(1)}"
    "40%{opacity:.8;transform:scaleY(.88)}70%{opacity:.95;transform:scaleY(1.06)}}"
    ".flame{animation:flick .9s steps(3) infinite;transform-box:fill-box;transform-origin:50% 100%}"
    ".flame2{animation-delay:-.45s}"
    "@keyframes glow{0%,100%{opacity:.55}50%{opacity:.35}}"
    ".glow{animation:glow 1.8s ease-in-out infinite}"
    "@keyframes blink{50%{opacity:0}}"
    ".blink{animation:blink 1.2s steps(1) infinite}"
    ".portrait{image-rendering:pixelated}"
    "@media (prefers-reduced-motion:reduce){.flame,.glow,.blink{animation:none}}"
)

DEFS = (
    '<pattern id="brick" width="32" height="16" patternUnits="userSpaceOnUse">'
    f'<rect width="32" height="16" fill="{P["panel"]}"/>'
    f'<rect x="0" y="0" width="31" height="7" fill="{P["brick"]}"/>'
    f'<rect x="-16" y="8" width="31" height="7" fill="{P["brick"]}"/>'
    f'<rect x="16" y="8" width="31" height="7" fill="{P["brick"]}"/>'
    "</pattern>"
    '<radialGradient id="torchglow">'
    f'<stop offset="0" stop-color="{P["amber"]}" stop-opacity=".6"/>'
    f'<stop offset="1" stop-color="{P["amber"]}" stop-opacity="0"/>'
    "</radialGradient>"
)


def xp_fraction(today: date) -> float:
    """Fraction of the current year elapsed: XP toward the next level."""
    days = 366 if calendar.isleap(today.year) else 365
    return (today.timetuple().tm_yday - 1) / days


def _torch(x: int, y: int, extra_cls: str = "") -> str:
    glow = f'<circle class="glow" cx="{x + 10}" cy="{y + 14}" r="34" fill="url(#torchglow)"/>'
    handle = rect(x + 6, y + 28, 8, 26, P["border"]) + rect(x + 4, y + 26, 12, 4, "#8a5a3a")
    flame = f'<g class="{("flame " + extra_cls).strip()}">'
    return glow + handle + flame + grid_to_svg(FLAME, FLAME_COLORS, x, y, 4) + "</g>"


def render_banner(profile: Profile, portrait_png: bytes, today: date) -> str:
    lvl = level(profile.career_start_year, today)
    name, name_size = fit(profile.name, TEXT_MAX_W, 40)
    title, title_size = fit(profile.title, TEXT_MAX_W, 12)
    subtitle, sub_size = fit(f"Lv.{lvl} {profile.char_class}", TEXT_MAX_W, 14)
    body = [
        window(0, 0, W, H),
        rect(6, 6, W - 12, H - 12, "url(#brick)"),
        _torch(284, 20),
        _torch(790, 20, "flame2"),
        rect(24, 24, 252, 252, P["shadow"]),
        rect(26, 26, 248, 248, P["border_hi"]),
        f'<image class="portrait" x="30" y="30" width="240" height="240" href="{data_uri(portrait_png)}"/>',
        text(TEXT_X + 4, 104, name, name_size, P["shadow"]),
        text(TEXT_X, 100, name, name_size, P["amber"]),
        text(TEXT_X, 140, subtitle, sub_size, P["parchment"]),
        text(TEXT_X, 168, title, title_size, P["text"]),
        text(TEXT_X, 190, profile.real_name, 8, P["muted"]),
        text(TEXT_X, 222, "XP", 8, P["amber"]),
        bar(TEXT_X + 26, 212, 260, 12, xp_fraction(today)),
        text(TEXT_X + 294, 222, f"LV.{lvl + 1}", 8, P["muted"]),
        text(TEXT_X, 266, "> PRESS START", 12, P["accent"], cls="t blink"),
    ]
    return svg_doc(W, H, "".join(body), css=CSS, defs=DEFS)
```

- [ ] **Step 4: Implement `generator/render/header.py`**

```python
"""Section header plate, e.g. 'QUEST LOG'."""
from __future__ import annotations

from generator.pixel import PALETTE as P, rect, svg_doc, text, text_width

W, H = 830, 40


def render_header(title: str) -> str:
    tw = text_width(title, 14)
    x = (W - tw - 40) // 2
    body = [
        rect(0, 19, W, 2, P["border_hi"]),
        rect(x, 2, tw + 40, 36, P["shadow"]),
        rect(x + 2, 4, tw + 36, 32, P["border_hi"]),
        rect(x + 4, 6, tw + 32, 28, P["bg"]),
        text(W // 2, 27, title, 14, P["amber"], anchor="middle"),
    ]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_banner.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add generator/render/banner.py generator/render/header.py generator/tests/test_banner.py
git commit -m "feat: render animated title banner and section headers"
```

---

### Task 5: Fetching and cache

**Files:**
- Create: `generator/fetch.py`, `generator/cache.py`
- Test: `generator/tests/test_fetch.py`, `generator/tests/test_cache.py`

**Interfaces:**
- Consumes: `FeedItem`, `RepoStats` (Task 1).
- Produces, in `generator.fetch`:
  - `Getter = Callable[[str, dict | None], bytes]`
  - `http_get(url: str, headers: dict | None = None) -> bytes`
  - `parse_devto(payload: bytes, limit: int = 3) -> list[FeedItem]`
  - `parse_youtube(payload: bytes, limit: int = 3) -> list[FeedItem]`
  - `parse_repo(payload: bytes) -> RepoStats`
  - `fetch_devto(user: str, get: Getter = http_get) -> list[FeedItem]`
  - `fetch_youtube(channel_id: str, get: Getter = http_get) -> list[FeedItem]`
  - `fetch_repo(full_name: str, token: str | None = None, get: Getter = http_get) -> RepoStats`
- Produces, in `generator.cache`:
  - `load_cache(path: Path) -> dict`
  - `save_cache(path: Path, cache: dict) -> None`
  - `resolve(cache: dict, key: str, fetch: Callable[[], T], encode: Callable[[T], object], decode: Callable[[object], T], log: Callable[[str], None] = print) -> T | None`
  - `encode_items`, `decode_items`, `encode_repo`, `decode_repo`

- [ ] **Step 1: Write the failing tests**

`generator/tests/test_fetch.py`:
```python
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
```

`generator/tests/test_cache.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_fetch.py generator/tests/test_cache.py -q`
Expected: `ModuleNotFoundError` for `generator.fetch` and `generator.cache`.

- [ ] **Step 3: Implement `generator/fetch.py`**

```python
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
```

- [ ] **Step 4: Implement `generator/cache.py`**

```python
"""Last-known-good values for live data, so a flaky feed never blanks the profile."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, TypeVar

from generator.models import FeedItem, RepoStats

T = TypeVar("T")


def load_cache(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(path: Path, cache: dict) -> None:
    Path(path).write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve(cache: dict, key: str, fetch: Callable[[], T], encode: Callable[[T], object],
            decode: Callable[[object], T], log: Callable[[str], None] = print) -> T | None:
    try:
        value = fetch()
    except Exception as exc:  # any failure (network, HTTP, parse) falls back to the cache
        if key not in cache:
            log(f"warning: {key}: {exc}; no cached value")
            return None
        log(f"warning: {key}: {exc}; using cached value")
        try:
            return decode(cache[key])
        except (TypeError, ValueError, KeyError) as bad:
            log(f"warning: {key}: cached value unreadable ({bad})")
            return None
    cache[key] = encode(value)
    return value


def encode_items(items: list[FeedItem]) -> list[dict]:
    return [asdict(i) for i in items]


def decode_items(raw: object) -> list[FeedItem]:
    return [FeedItem(**r) for r in raw]


def encode_repo(stats: RepoStats) -> dict:
    return asdict(stats)


def decode_repo(raw: object) -> RepoStats:
    return RepoStats(**raw)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_fetch.py generator/tests/test_cache.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add generator/fetch.py generator/cache.py generator/tests/test_fetch.py generator/tests/test_cache.py
git commit -m "feat: fetch dev.to, YouTube and repo stats with cache fallback"
```

---

### Task 6: Character sheet and cards

**Files:**
- Create: `generator/render/stats.py`, `generator/render/inventory.py`, `generator/render/quests.py`, `generator/render/scrolls.py`, `generator/render/portals.py`
- Test: `generator/tests/test_cards.py`

**Interfaces:**
- Consumes: `Profile`, `Quest`, `Portal`, `ABILITIES`, `format_modifier` (Task 1); `FeedItem`, `RepoStats` (Task 1); pixel helpers (Task 2); `icon`, `item_icon`, `star`, `ITEMS` (Task 3).
- Produces:
  - `render_stats(profile: Profile) -> str` (410×300)
  - `render_inventory(profile: Profile) -> str` (410×300)
  - `render_quest(quest: Quest, stats: RepoStats | None) -> str` (410×120)
  - `render_scroll(item: FeedItem, source: str) -> str` and `render_sealed_scroll(source: str) -> str` (410×100), where `source` is `"devto"` or `"youtube"`
  - `render_portal(portal: Portal) -> str` (160×44)

- [ ] **Step 1: Write the failing tests**

`generator/tests/test_cards.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_cards.py -q`
Expected: `ModuleNotFoundError: No module named 'generator.render.inventory'`.

- [ ] **Step 3: Implement `generator/render/stats.py`**

```python
"""Ability-score block: six D&D-style stats with segmented bars."""
from __future__ import annotations

from generator.config import ABILITIES, Profile, format_modifier
from generator.pixel import PALETTE as P, bar, svg_doc, text, window

W, H = 410, 300
ABILITY_NAMES = {"MOB": "MOBILE", "DAT": "DATA", "NET": "NETWORK",
                 "BAK": "BACKEND", "SYN": "P2P SYNC", "CHA": "ADVOCACY"}


def render_stats(profile: Profile) -> str:
    body = [window(0, 0, W, H, "STATS")]
    for i, ability in enumerate(ABILITIES):
        y = 44 + i * 42
        score = profile.stats[ability]
        body += [
            text(22, y + 12, ability, 12, P["amber"]),
            text(22, y + 26, ABILITY_NAMES[ability], 6, P["muted"]),
            bar(104, y + 2, 190, 14, score / 20),
            text(390, y + 14, f"{score} ({format_modifier(score)})", 9, P["text"], anchor="end"),
        ]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 4: Implement `generator/render/inventory.py`**

```python
"""4x4 inventory grid of skill items."""
from __future__ import annotations

from generator.config import Profile
from generator.icons import ITEMS, item_icon
from generator.pixel import PALETTE as P, rect, svg_doc, text, window

W, H = 410, 300


def render_inventory(profile: Profile) -> str:
    body = [window(0, 0, W, H, "INVENTORY")]
    for i, item_id in enumerate(profile.inventory):
        x0, y0 = 17 + (i % 4) * 94, 30 + (i // 4) * 64
        label = ITEMS[item_id][0]
        body += [
            rect(x0 + 3, y0 + 3, 88, 58, P["border"]),
            rect(x0 + 4, y0 + 4, 86, 56, P["panel_dark"]),
            item_icon(item_id, x0 + 31, y0 + 9, 2),
            text(x0 + 47, y0 + 54, label, 6, P["parchment"], anchor="middle"),
        ]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 5: Implement `generator/render/quests.py`**

```python
"""Quest cards: one per featured repo."""
from __future__ import annotations

from generator.config import Quest
from generator.icons import icon, star
from generator.models import RepoStats
from generator.pixel import PALETTE as P, fit, svg_doc, text, text_width, window, wrap

W, H = 410, 120
TEXT_X = 84
TEXT_W = W - TEXT_X - 16
KIND_STYLE = {"guild": ("GUILD QUEST", "shield", "#4a6cf7"),
              "side": ("SIDE QUEST", "potion", "#d8642a")}


def render_quest(quest: Quest, stats: RepoStats | None) -> str:
    label, shape, color = KIND_STYLE[quest.kind]
    blurb = quest.blurb or (stats.description if stats else "")
    name, name_size = fit(quest.name, TEXT_W, 10)
    body = [window(0, 0, W, H, label), icon(shape, color, 20, 34, 3),
            text(TEXT_X, 46, name, name_size, P["amber"])]
    for i, line in enumerate(wrap(blurb, TEXT_W // 7, 2)):
        body.append(text(TEXT_X, 66 + i * 12, line, 7, P["text"]))
    if stats:
        if stats.language:
            body.append(text(TEXT_X, 104, stats.language.upper(), 6, P["muted"]))
        count = str(stats.stars)
        count_x = W - 16 - text_width(count, 8)
        body += [star(count_x - 18, 91, 2), text(count_x, 104, count, 8, P["amber"])]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 6: Implement `generator/render/scrolls.py`**

```python
"""Parchment cards for recent dev.to posts and YouTube videos."""
from __future__ import annotations

from generator.icons import icon
from generator.models import FeedItem
from generator.pixel import PALETTE as P, rect, svg_doc, text, wrap

W, H = 410, 100
TEXT_X = 80
SOURCES = {"devto": ("DEV.TO", "tome", "#3b49df"),
           "youtube": ("YOUTUBE", "gem", "#ff3b3b")}


def _frame(source: str) -> list[str]:
    label, shape, color = SOURCES[source]
    return [
        rect(2, 0, W - 4, H, P["ink"]),
        rect(0, 2, W, H - 4, P["ink"]),
        rect(3, 3, W - 6, H - 6, P["parchment_dark"]),
        rect(5, 5, W - 10, H - 10, P["parchment"]),
        icon(shape, color, 16, 26, 3),
        text(TEXT_X, 24, label, 6, P["orange"]),
    ]


def render_scroll(item: FeedItem, source: str) -> str:
    body = _frame(source)
    body.append(text(W - 16, 24, item.published, 6, P["ink"], anchor="end"))
    for i, line in enumerate(wrap(item.title, (W - TEXT_X - 16) // 8, 3)):
        body.append(text(TEXT_X, 44 + i * 14, line, 8, P["ink"]))
    return svg_doc(W, H, "".join(body))


def render_sealed_scroll(source: str) -> str:
    body = _frame(source) + [
        text(TEXT_X, 50, "THE SCROLLS ARE SEALED...", 8, P["ink"]),
        text(TEXT_X, 70, "CLICK TO VISIT THE ARCHIVE", 6, P["orange"]),
    ]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 7: Implement `generator/render/portals.py`**

```python
"""Pixel link buttons for the footer."""
from __future__ import annotations

from generator.config import Portal
from generator.icons import icon
from generator.pixel import PALETTE as P, fit, rect, svg_doc, text

W, H = 160, 44
LABEL_X = 48
ICONS = {"dev.to": ("tome", "#e8e8e8"), "costoda.tech": ("scroll", "#f0a040"),
         "youtube": ("gem", "#ff3b3b"), "linkedin": ("shield", "#2f8fd8"),
         "ditto docs": ("shield", "#4a6cf7")}


def render_portal(portal: Portal) -> str:
    shape, color = ICONS.get(portal.label.lower(), ("scroll", P["amber"]))
    label, size = fit(portal.label.upper(), W - LABEL_X - 8, 8)
    body = [
        rect(2, 0, W - 4, H, P["shadow"]),
        rect(0, 2, W, H - 4, P["shadow"]),
        rect(2, 2, W - 4, H - 4, P["border_hi"]),
        rect(4, 4, W - 8, H - 8, P["panel"]),
        icon(shape, color, 8, 6, 2),
        text(LABEL_X, 26, label, size, P["parchment"]),
    ]
    return svg_doc(W, H, "".join(body))
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest generator/tests/test_cards.py -q`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add generator/render generator/tests/test_cards.py
git commit -m "feat: render stats, inventory, quest, scroll and portal cards"
```

---

### Task 7: README assembly, build CLI and preview

**Files:**
- Create: `generator/readme.py`, `generator/build.py`
- Test: `generator/tests/test_build.py`
- Generated (committed): `README.md`, `assets/generated/*`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `generator.readme`: `GENERATED_NOTE: str`, `Card(src, alt, width, href=None)`, `row(cards: list[Card]) -> str`, `pacman(user: str) -> str`, `render_readme(blocks: list[str]) -> str`, `render_preview(readme: str) -> str`
  - `generator.build`: `ROOT: Path`, `GENERATED: str`, `build(root: Path = ROOT, today: date | None = None, get: Getter = http_get, token: str | None = None, log=print) -> str` (returns the README text), `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write the failing tests**

`generator/tests/test_build.py`:
```python
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
    (tmp_path / "assets").mkdir()
    shutil.copy(ROOT / "assets" / "portrait.png", tmp_path / "assets" / "portrait.png")
    return tmp_path


def run(root, get=good_get):
    return build(root, TODAY, get, None, log=lambda m: None)


def test_build_writes_readme_and_valid_svgs(root):
    readme = run(root)
    assert (root / "README.md").read_text() == readme
    srcs = re.findall(r'src="(assets/generated/[^"]+)"', readme)
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest generator/tests/test_build.py -q`
Expected: `ModuleNotFoundError: No module named 'generator.build'`.

- [ ] **Step 3: Implement `generator/readme.py`**

```python
"""README.md assembly. GitHub allows only sanitized HTML: images, links, <p align>, <picture>."""
from __future__ import annotations

from dataclasses import dataclass

from generator.pixel import esc

GENERATED_NOTE = "<!-- Generated by generator/build.py. Edit profile.yml instead. -->"


@dataclass(frozen=True)
class Card:
    src: str
    alt: str
    width: str
    href: str | None = None


def _card_html(card: Card) -> str:
    img = f'<img src="{esc(card.src)}" alt="{esc(card.alt)}" width="{card.width}">'
    return f'<a href="{esc(card.href)}">{img}</a>' if card.href else img


def row(cards: list[Card]) -> str:
    return '<p align="center">\n' + "\n".join(_card_html(c) for c in cards) + "\n</p>"


def pacman(user: str) -> str:
    base = f"https://raw.githubusercontent.com/{user}/{user}/output/pacman-contribution-graph"
    return (
        '<p align="center">\n<picture>\n'
        f'  <source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="{base}.svg">\n'
        f'  <img alt="Pac-Man eating the contribution graph" src="{base}.svg" width="100%">\n'
        "</picture>\n</p>"
    )


def render_readme(blocks: list[str]) -> str:
    return GENERATED_NOTE + "\n\n" + "\n\n".join(blocks) + "\n"


def render_preview(readme: str) -> str:
    body = readme.replace(GENERATED_NOTE, "")

    def column(theme: str, bg: str, fg: str) -> str:
        return (f'<section style="background:{bg};color:{fg};padding:24px;width:830px;'
                f'font-family:sans-serif"><h3>{theme}</h3>{body}</section>')

    return ("<!doctype html><meta charset=utf-8><title>Profile preview</title>"
            "<body style=\"margin:0;padding:24px;display:flex;gap:24px;flex-wrap:wrap;background:#6e7681\">"
            + column("GitHub dark", "#0d1117", "#e6edf3")
            + column("GitHub light", "#ffffff", "#1f2328")
            + "</body>")
```

- [ ] **Step 4: Implement `generator/build.py`**

```python
"""Build the profile: profile.yml + live data -> assets/generated/*.svg + README.md."""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

from generator.cache import (
    decode_items, decode_repo, encode_items, encode_repo, load_cache, resolve, save_cache,
)
from generator.config import ConfigError, level, load_profile
from generator.fetch import Getter, fetch_devto, fetch_repo, fetch_youtube, http_get
from generator.icons import ITEMS
from generator.readme import Card, pacman, render_preview, render_readme, row
from generator.render.banner import render_banner
from generator.render.header import render_header
from generator.render.inventory import render_inventory
from generator.render.portals import render_portal
from generator.render.quests import render_quest
from generator.render.scrolls import render_scroll, render_sealed_scroll
from generator.render.stats import render_stats

ROOT = Path(__file__).resolve().parent.parent
GENERATED = "assets/generated"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _pairs(cards: list[Card]) -> list[str]:
    return [row(cards[i:i + 2]) for i in range(0, len(cards), 2)]


def build(root: Path = ROOT, today: date | None = None, get: Getter = http_get,
          token: str | None = None, log=print) -> str:
    today = today or date.today()
    profile = load_profile(root / "profile.yml", today)
    unknown = [i for i in profile.inventory if i not in ITEMS]
    if unknown:
        raise ConfigError(f"profile.yml: unknown inventory items: {', '.join(unknown)} "
                          f"(known: {', '.join(sorted(ITEMS))})")
    portrait = (root / "assets" / "portrait.png").read_bytes()

    out = root / GENERATED
    cache_path = out / "cache.json"
    cache = load_cache(cache_path)
    files: dict[str, str] = {}

    def add(name: str, svg: str) -> str:
        files[name] = svg
        return f"{GENERATED}/{name}"

    def header(title: str) -> str:
        return row([Card(add(f"header-{_slug(title)}.svg", render_header(title)), title.title(), "100%")])

    lvl = level(profile.career_start_year, today)
    blocks = [row([Card(add("banner.svg", render_banner(profile, portrait, today)),
                        f"{profile.name}: Lv.{lvl} {profile.char_class}, {profile.title}", "100%")])]

    blocks.append(header("CHARACTER SHEET"))
    stats_alt = "Stats: " + ", ".join(f"{k} {v}" for k, v in profile.stats.items())
    inventory_alt = "Inventory: " + ", ".join(ITEMS[i][0] for i in profile.inventory)
    blocks.append(row([Card(add("stats.svg", render_stats(profile)), stats_alt, "49%"),
                       Card(add("inventory.svg", render_inventory(profile)), inventory_alt, "49%")]))

    blocks.append(header("QUEST LOG"))
    quest_cards = []
    for quest in profile.quests:
        stats = resolve(cache, f"repo:{quest.repo}", lambda q=quest: fetch_repo(q.repo, token, get),
                        encode_repo, decode_repo, log)
        src = add(f"quest-{_slug(quest.repo)}.svg", render_quest(quest, stats))
        quest_cards.append(Card(src, f"{quest.repo}: {quest.blurb or ''}".rstrip(": "), "49%",
                                f"https://github.com/{quest.repo}"))
    blocks += _pairs(quest_cards)

    blocks.append(header("RECENT SCROLLS"))
    feeds = [
        ("devto", lambda: fetch_devto(profile.devto_user, get), f"https://dev.to/{profile.devto_user}"),
        ("youtube", lambda: fetch_youtube(profile.youtube_channel_id, get),
         f"https://www.youtube.com/channel/{profile.youtube_channel_id}"),
    ]
    scroll_cards = []
    for source, fetch, home in feeds:
        items = resolve(cache, source, fetch, encode_items, decode_items, log) or []
        if not items:
            src = add(f"scroll-{source}-1.svg", render_sealed_scroll(source))
            scroll_cards.append(Card(src, f"{source}: visit the archive", "49%", home))
        for n, item in enumerate(items, start=1):
            src = add(f"scroll-{source}-{n}.svg", render_scroll(item, source))
            scroll_cards.append(Card(src, item.title, "49%", item.url or home))
    blocks += _pairs(scroll_cards)

    blocks.append(header("DUNGEON MAP"))
    blocks.append(pacman(profile.github_user))

    blocks.append(header("PORTALS"))
    blocks.append(row([Card(add(f"portal-{_slug(p.label)}.svg", render_portal(p)), p.label, "19%", p.url)
                       for p in profile.portals]))

    readme = render_readme(blocks)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        if old.name not in files:
            old.unlink()
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
    save_cache(cache_path, cache)
    (root / "README.md").write_text(readme, encoding="utf-8")
    return readme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the GitHub profile README.")
    parser.add_argument("--preview", action="store_true", help="also write preview.html")
    args = parser.parse_args(argv)
    try:
        readme = build(ROOT, token=os.environ.get("GITHUB_TOKEN"))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.preview:
        path = ROOT / "preview.html"
        path.write_text(render_preview(readme), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: in `test_build_writes_readme_and_valid_svgs` the expected count is 1 banner + 5 headers + 2 sheet + 6 quests + 2 scrolls (one post and one video) + 5 portals = 21. Headers must be written *before* they are used, which `add()` guarantees.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest -q`
Expected: the whole suite passes.

- [ ] **Step 6: Build for real and preview**

Run:
```bash
.venv/bin/python -m generator.build --preview && open preview.html
```
Expected: `wrote .../preview.html`. The browser shows the profile in both dark and light columns, with real dev.to posts, YouTube videos and star counts. Pac-Man shows as a broken image until Task 8's workflow has run once; that is expected.

Then check visually (take a Playwright screenshot of `preview.html` if you're working headless):
- torches flicker and PRESS START blinks
- no text overflows any card, and the icons are recognizable
- light mode looks intentional

Fix any art or layout issue in the relevant `render/*` or `icons.py` file, rerun the tests, and rebuild.

- [ ] **Step 7: User visual review (checkpoint)**

Show the user `preview.html` (the screenshot or `open preview.html`) and wait for their approval or requested tweaks before continuing. Apply their tweaks, rerun `.venv/bin/python -m pytest -q` and rebuild.

- [ ] **Step 8: Commit**

```bash
git add generator/readme.py generator/build.py generator/tests/test_build.py README.md assets/generated
git commit -m "feat: assemble README with build CLI and preview"
```

---

### Task 8: GitHub Actions and publish

**Files:**
- Create: `.github/workflows/build.yml`, `.github/workflows/pacman.yml`

**Interfaces:**
- Consumes: `python -m generator.build` (Task 7), and `requirements.txt` plus `pytest.ini` (Task 1).

- [ ] **Step 1: Create `.github/workflows/build.yml`**

```yaml
name: build profile

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - profile.yml
      - generator/**
      - assets/portrait.png
      - assets/fonts/**
      - requirements.txt
      - .github/workflows/build.yml

permissions:
  contents: write

concurrency:
  group: build-profile
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
      - run: python -m generator.build
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: commit if changed
        run: |
          git add README.md assets/generated
          if git diff --cached --quiet; then
            echo "profile unchanged"
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "chore: refresh profile"
          git push
```

- [ ] **Step 2: Create `.github/workflows/pacman.yml`**

```yaml
name: pacman contribution graph

on:
  schedule:
    - cron: "0 5 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: abozanona/pacman-contribution-graph@main
        with:
          github_user_name: ${{ github.repository_owner }}
          games: pacman
      - uses: crazy-max/ghaction-github-pages@v3.1.0
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 3: Validate the YAML locally**

Run: `.venv/bin/python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]; print('ok')" .github/workflows/*.yml`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows
git commit -m "ci: nightly profile build and Pac-Man contribution graph"
```

- [ ] **Step 5: Ask before publishing (checkpoint)**

Pushing to `git@github.com:biozal/biozal.git` makes the profile public immediately. Ask the user for explicit approval to push. Do not push without it.

- [ ] **Step 6: Push and run the workflows**

After approval:
```bash
git push -u origin main
gh workflow run pacman.yml -R biozal/biozal
gh workflow run build.yml -R biozal/biozal
gh run list -R biozal/biozal --limit 4
```
Expected: both runs finish with `completed success`. If either fails, show `gh run view <id> --log-failed` output to the user and fix it.

- [ ] **Step 7: Verify live**

Open https://github.com/biozal in dark and light mode, on desktop and at phone width (a Playwright resize to 390px works). Check that the banner animates, every card links to the right place, Pac-Man renders, and there is no horizontal overflow. Report the results to the user with screenshots.
