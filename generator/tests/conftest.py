from datetime import date
from pathlib import Path

import pytest

from generator.config import load_profile

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 9, 27)


@pytest.fixture
def profile():
    return load_profile(ROOT / "profile.yml", TODAY)
