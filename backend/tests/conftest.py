import copy
import json
from pathlib import Path

import pytest

from engine.planner import design

FIXTURES = Path(__file__).parent / "fixtures"
PRESETS = Path(__file__).parent.parent / "presets"
EXAMPLES = Path(__file__).parent.parent / "examples"
PRESET_NAMES = ["campus_lan", "metro_man", "global_wan"]
NAMES = ["campus", "metro", "wan", "three_tier", *PRESET_NAMES]


def load(name: str) -> dict:
    for d in (FIXTURES, PRESETS, EXAMPLES):
        if (d / f"{name}.json").exists():
            return json.loads((d / f"{name}.json").read_text())
    raise FileNotFoundError(name)


@pytest.fixture(scope="session")
def designs():
    return {n: design(load(n)) for n in NAMES}


@pytest.fixture
def raw():
    return lambda name: copy.deepcopy(load(name))
