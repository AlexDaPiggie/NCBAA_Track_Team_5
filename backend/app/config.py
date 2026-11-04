"""Load config/assumptions.yaml. Single source of truth for all assumptions."""
from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "assumptions.yaml"


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_config() -> dict:
    """Return a deep copy so callers can tweak without side effects."""
    return copy.deepcopy(_load())


HOURS = 24
HORIZON = 7 * HOURS  # hourly grain, 7-day window
