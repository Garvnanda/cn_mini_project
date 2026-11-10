import copy
import json
from pathlib import Path

import pytest

from engine.planner import design

FIXTURES = Path(__file__).parent / "fixtures"
NAMES = ["campus", "metro", "wan", "three_tier"]


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


@pytest.fixture(scope="session")
def designs():
    return {n: design(load(n)) for n in NAMES}


@pytest.fixture
def raw():
    return lambda name: copy.deepcopy(load(name))
