# GitHub Profile README — "Character Sheet" Design

**Date:** 2026-09-27
**Repo:** `biozal/biozal` (GitHub profile repository)
**Status:** Approved

## Goal

Make https://github.com/biozal look striking and memorable with a retro pixel-art /
D&D "character sheet" theme that presents Aaron LaBeau as a 30+ year software veteran
and Developer Advocate at Ditto, expert in mobile, mobile databases, backend and
networking, with Cartyx and D&D as the personal thread.

**Audience:** developers, Ditto prospects and community, conference/meetup contacts.

**Success criteria**

- Reads as deliberate, high-quality pixel art (not a pixelated photo or a template).
- Looks intentional in both GitHub dark and light mode.
- Stays fresh with no manual work: live posts, videos, stars and contribution graph
  refresh nightly.
- A build or feed failure never breaks the rendered profile.
- Content is changed by editing one file, `profile.yml`.

## Visual Direction

- **Hero art:** `assets/portrait.png`, a 200×200, 64-color pixel portrait of Aaron as an
  Artificer (gears, wrench, leather strap) in a torchlit rune dungeon. Source: an
  AI-generated image the user supplied, snapped onto its true 200×200 grid (the source
  was 1024px at 5.12px per art-pixel) and palette-quantized without despeckling, so
  single-pixel highlights such as eye catchlights are preserved. Treated as a fixed,
  committed asset; the generator never re-derives it.
- **Palette:** derived from the portrait — deep purple-black backgrounds, amber/orange
  highlights, parchment tones for text panels — plus one cool accent (Cartyx blue
  `#85adff`) for links and interactive affordances. Palette constants live in
  `generator/pixel.py`.
- **Type:** Press Start 2P (OFL), embedded in each SVG that renders text, subset where
  practical to keep files small.
- **Frames:** every section is a dark "game window" with a pixel border, so it reads as
  intentional on GitHub's white light-mode background. No separate light variants.

## Page Layout (top to bottom)

1. **Title screen banner** — full width, animated. A dungeon corridor with the portrait
   framed at center, flickering torches (CSS animation inside the SVG), a pixel `BIOZAL`
   title, the subtitle `Lv.<N> Artificer · Developer Advocate @ Ditto`, and a blinking
   `▶ PRESS START`. `N` = current year − `career_start_year`, so the level rises on its own.
2. **Character sheet**, as two images placed side by side (they stack on narrow screens):
   - **Stat block** — six D&D-style abilities, each shown as score + modifier
     (`18 (+4)`, modifier = floor((score − 10) / 2)):
     MOB (mobile), DAT (databases/SQLite), NET (networking), BAK (backend),
     SYN (P2P sync), CHA (developer advocacy). Scores are set in `profile.yml`.
   - **Inventory** — 4×4 grid of 16×16 pixel item icons: Swift, Kotlin, C#,
     TypeScript, JavaScript, Java, C, Python, Rust, Dart/Flutter, React Native, SQLite,
     Mobile DBs, Networking, IoT, and a Ditto guild crest.
3. **Quest log** — six quest cards, each a separate image wrapped in a link to its repo,
   showing icon, name, one-line description, primary language and live ⭐ count:
   - Guild quests: `biozal/ditto-edge-studio`, `ditto-examples/ditto-whiteboard-datastreams`,
     `ditto-examples/demoapp-retail`
   - Side quests: `biozal/cartyx-app`, `biozal/cartyx-sim`, `biozal/ttrpg-sfx`
4. **Recent scrolls** — the latest 3 dev.to posts (user `biozal`) and latest 3 YouTube
   videos (channel `UCXgF-JqwBRGSawXajr6plGg`, "Costoda Coding Bits") as parchment
   cards, each linking to its post or video.
5. **Dungeon map** — the contribution graph as Pac-Man, regenerated nightly.
6. **Portals** — pixel buttons linking to dev.to (https://dev.to/biozal/), costoda.tech
   (https://costoda.tech/#blog), YouTube (https://www.youtube.com/costoda), LinkedIn
   (https://www.linkedin.com/in/aaron-labeau-b444747/) and Ditto Docs
   (https://docs.ditto.live), plus a "Guild: Ditto" crest.

### GitHub rendering constraints the design depends on

- README HTML is sanitized, with no CSS or JS in the page. All visual effects live inside
  SVG files referenced by `<img>`.
- Images served through `<img>` cannot load external resources, so the font and the
  portrait are embedded (base64) in the SVGs that use them.
- An image can carry only one link, so every clickable element (quest card, scroll,
  portal) is its own SVG wrapped in `<a>`.
- Target content width is 830px; SVGs use a `viewBox` and scale down on mobile.
- Pixel crispness: `shape-rendering="crispEdges"` on vector pixels and
  `image-rendering: pixelated` on the embedded portrait.

## Architecture

```
biozal/
├── README.md              # generated — never hand-edited
├── profile.yml            # all editable content
├── assets/
│   ├── portrait.png       # committed source art
│   ├── fonts/PressStart2P-Regular.ttf  (+ OFL license)
│   └── generated/         # generator output (committed) + cache.json
├── generator/
│   ├── build.py           # entry: load → fetch → render → write
│   ├── config.py          # loads and validates profile.yml
│   ├── fetch.py           # dev.to, YouTube RSS, GitHub repo stats
│   ├── pixel.py           # palette, window frame, text, icon-grid helpers
│   ├── icons.py           # 16×16 icon grids
│   ├── render/            # banner, sheet, inventory, quests, scrolls, portals, readme
│   └── tests/             # + fixtures/ with saved feed responses
├── docs/superpowers/specs/
└── .github/workflows/
    ├── build.yml
    └── pacman.yml
```

**Data flow:** `profile.yml` → `config` → `fetch` (live data merged with cache) →
each `render/*` module returns an SVG string → `build` writes
`assets/generated/*.svg`, `cache.json` and `README.md`.

**Units**

- `config.py` — parse and validate `profile.yml` (required keys, score range 1–20,
  URLs present). Input: a path. Output: a typed dataclass.
- `fetch.py` — one function per source; each returns data or raises. `build.py`
  catches errors per source and falls back to the cached value.
  - dev.to: `GET https://dev.to/api/articles?username=biozal&per_page=3`
  - YouTube: `GET https://www.youtube.com/feeds/videos.xml?channel_id=…` (Atom)
  - GitHub: repo stars, language and description via the REST API using `GITHUB_TOKEN`
- `pixel.py` — pure helpers: palette, `window(w, h, title)`, `text(x, y, s, size)`,
  `grid_to_svg(rows, palette)`. No I/O.
- `render/*` — pure functions from data to an SVG string. No network or file I/O.
- `render/readme.py` — assembles `README.md` from section images and links.

**Dependencies:** Python 3.12, `pyyaml`, and the standard library (`urllib`,
`xml.etree`, `base64`). No image libraries are needed at build time.

### `profile.yml` shape

```yaml
name: BIOZAL
real_name: Aaron LaBeau
title: Developer Advocate @ Ditto
class: Artificer
career_start_year: 1994        # → Lv.32 in 2026
stats: { MOB: 20, DAT: 19, NET: 17, BAK: 16, SYN: 18, CHA: 16 }
inventory: [swift, kotlin, csharp, typescript, javascript, java, c, python,
            rust, flutter, react-native, sqlite, mobile-db, networking, iot, ditto]
quests:
  guild: [biozal/ditto-edge-studio, ditto-examples/ditto-whiteboard-datastreams,
          ditto-examples/demoapp-retail]
  side:  [biozal/cartyx-app, biozal/cartyx-sim, biozal/ttrpg-sfx]
feeds:
  devto_user: biozal
  youtube_channel_id: UCXgF-JqwBRGSawXajr6plGg
portals:
  - { label: dev.to,       url: https://dev.to/biozal/ }
  - { label: costoda.tech, url: https://costoda.tech/#blog }
  - { label: YouTube,      url: https://www.youtube.com/costoda }
  - { label: LinkedIn,     url: https://www.linkedin.com/in/aaron-labeau-b444747/ }
  - { label: Ditto Docs,   url: https://docs.ditto.live }
```

Quest descriptions default to the GitHub repo description. An optional per-quest
`blurb` overrides it (several current descriptions are terse, e.g. "Retail Demo App").

## Automation

- **`build.yml`** — triggers: daily cron (06:00 UTC), `workflow_dispatch`, and push
  to `profile.yml`, `generator/**` or `assets/portrait.png`. Steps: checkout, set up
  Python, install dependencies, run tests, run the generator, commit
  `README.md` + `assets/generated/` as `github-actions[bot]` only if the diff is
  non-empty. Permissions: `contents: write`.
- **`pacman.yml`** — daily, using `abozanona/pacman-contribution-graph` for user
  `biozal`, with dark and light outputs published to an `output` branch and embedded
  through a `<picture>` element so the maze matches the viewer's theme.

## Error Handling

- Each live source is fetched independently. On failure, the last good value from
  `cache.json` is used and a warning is logged; the build still succeeds.
- With no cache and a failed fetch, that section renders a themed fallback card
  ("The scrolls are sealed…") that links to the source site.
- Invalid `profile.yml` fails the build with a clear message, before anything is written.
  The committed profile stays unchanged because nothing gets committed.

## Testing

- Unit tests: `config` validation, modifier math, level calculation, dev.to and
  YouTube parsing against saved fixtures, cache fallback behavior.
- Output checks: every generated SVG parses as XML and has a `viewBox`; README links
  match `profile.yml`.
- Local preview: `python -m generator.build --preview` writes `preview.html` that
  shows the README as it will look on GitHub, in dark and light mode.
- Final check: push, then view the live profile in dark and light mode on desktop
  and at phone width.

## Out of Scope

- An RSS feed for costoda.tech (the portal link only; the generator can adopt a feed
  later).
- Separate light-mode art beyond the Pac-Man graph.
- An animated full-body walking sprite (possible follow-up).
