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
