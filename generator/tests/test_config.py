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
