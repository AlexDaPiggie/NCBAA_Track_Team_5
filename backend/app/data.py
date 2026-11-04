"""Seeded SYNTHETIC demand. Not real FBO data."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import HORIZON, HOURS


def hourly_shape(cfg: dict) -> np.ndarray:
    p = cfg["demand"]["hourly_shape"]
    h = np.arange(HOURS)
    w = np.full(HOURS, float(p["floor"]))
    for mean, sd, weight in p["peaks"]:
        w += weight * np.exp(-0.5 * ((h - mean) / sd) ** 2)
    return w / w.sum()


def ordinary_mean(cfg: dict) -> np.ndarray:
    """Expected arrivals per hour for an ordinary week, shape (7, 24)."""
    d = cfg["demand"]
    dow = np.asarray(d["dow_factors"], dtype=float)
    return d["base_daily_arrivals"] * dow[:, None] * hourly_shape(cfg)[None, :]


def day_multipliers(cfg: dict, intensity: float) -> np.ndarray:
    curve = np.asarray(cfg["demand"]["event_day_curve"], dtype=float)
    return 1.0 + (curve - 1.0) * intensity


def intensity_for(cfg: dict, name: str, custom: float | None = None) -> float:
    if name == "custom":
        if custom is None:
            raise ValueError("custom scenario needs intensity")
        return float(custom)
    return float(cfg["demand"]["scenarios"][name])


def scenario_mean(cfg: dict, intensity: float) -> np.ndarray:
    """Expected hourly arrivals for the 7-day window, flat (168,)."""
    mean = ordinary_mean(cfg) * day_multipliers(cfg, intensity)[:, None]
    return mean.reshape(HORIZON)


def realized(cfg: dict, mean_flat: np.ndarray, stream: int) -> np.ndarray:
    """One Poisson realization. `stream` keeps seeds reproducible and distinct."""
    rng = np.random.default_rng(cfg["seed"] + 1000 * stream)
    return rng.poisson(mean_flat).astype(float)


def generate_history(cfg: dict) -> pd.DataFrame:
    """Synthetic ordinary weeks used to train the forecaster."""
    mean = scenario_mean(cfg, 0.0)
    rows = []
    for wk in range(cfg["demand"]["history_weeks"]):
        arr = realized(cfg, mean, stream=wk + 1)
        for t in range(HORIZON):
            rows.append((wk, t // HOURS, t % HOURS, t, arr[t]))
    return pd.DataFrame(rows, columns=["week", "day", "hour", "t", "arrivals"])
