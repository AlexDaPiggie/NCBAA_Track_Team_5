"""Arrival forecast with P10/P50/P90 and a naive baseline.

Model is trained on SYNTHETIC ordinary weeks only. Event-week uplift is a
scenario assumption (config), not learned. Backtest metrics are on synthetic
holdout and do not show real-world accuracy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.ensemble import HistGradientBoostingRegressor

from .config import HORIZON, HOURS

Z90 = 1.2816


def _features(day: np.ndarray, hour: np.ndarray) -> np.ndarray:
    ang = 2 * np.pi * hour / HOURS
    return np.column_stack([hour, day, np.sin(ang), np.cos(ang)])


class ArrivalForecaster:
    """Poisson gradient-boosted mean + Poisson quantile band.

    Row 1 (`p50`) is the EXPECTED arrivals per hour (planning basis).
    P10/P90 come from the Poisson distribution around that mean.
    """

    def __init__(self) -> None:
        self.model: HistGradientBoostingRegressor | None = None

    def fit(self, df: pd.DataFrame) -> "ArrivalForecaster":
        x = _features(df["day"].to_numpy(), df["hour"].to_numpy())
        y = df["arrivals"].to_numpy()
        self.model = HistGradientBoostingRegressor(
            loss="poisson", max_iter=60, learning_rate=0.06, max_depth=3,
            min_samples_leaf=30, l2_regularization=1.0, random_state=0,
        ).fit(x, y)
        return self

    def predict_week(self) -> np.ndarray:
        """Ordinary-week [p10, expected, p90], shape (3, 168)."""
        t = np.arange(HORIZON)
        mean = np.maximum(self.model.predict(_features(t // HOURS, t % HOURS)), 0.0)
        p10 = poisson.ppf(0.1, mean)
        p90 = poisson.ppf(0.9, mean)
        return np.vstack([np.minimum(p10, mean), mean, np.maximum(p90, mean)])


def apply_uplift(base_q: np.ndarray, multipliers: np.ndarray, sigma: float, intensity: float) -> np.ndarray:
    """Scale ordinary quantiles by the scenario day multipliers (an ASSUMPTION)
    and widen the band for uplift uncertainty."""
    m = np.repeat(multipliers, HOURS)[None, :]
    out = base_q * m
    s = sigma * intensity
    out[0] *= np.exp(-Z90 * s)
    out[2] *= np.exp(Z90 * s)
    return out


def apply_disruptions(q: np.ndarray, disruptions: list[dict]) -> np.ndarray:
    """Disruptions act on all quantiles (and on realized arrivals, 1-D)."""
    q = q.copy()
    for d in disruptions:
        a, b = int(d["start_hour"]), int(d["end_hour"])
        a, b = max(0, a), min(HORIZON, b)
        if b <= a:
            continue
        kind = d["kind"]
        if kind == "spike":
            q[..., a:b] += float(d.get("extra_arrivals", 0.0)) / (b - a)
        elif kind == "cancel":
            q[..., a:b] *= 1.0 - float(d.get("fraction", 0.5))
        elif kind == "delay":
            k = int(d.get("shift_hours", 3))
            moved = q[..., a:b].copy()
            q[..., a:b] = 0.0
            hi = min(HORIZON, b + k)
            n = hi - (a + k)
            if n > 0:
                q[..., a + k:hi] += moved[..., :n]
    return q


def backtest(df: pd.DataFrame) -> dict:
    """Hold out the last ordinary week. Compare model P50 with naive
    (same hour, previous week). SYNTHETIC data only."""
    last = int(df["week"].max())
    train, hold = df[df["week"] < last], df[df["week"] == last]
    fc = ArrivalForecaster().fit(train)
    q = fc.predict_week()
    y = hold.sort_values("t")["arrivals"].to_numpy()
    prev = df[df["week"] == last - 1].sort_values("t")["arrivals"].to_numpy()

    def wape(pred: np.ndarray) -> float:
        return float(np.abs(pred - y).sum() / max(y.sum(), 1e-9))

    def daily_mape(pred: np.ndarray) -> float:
        ya, pa = y.reshape(7, HOURS).sum(1), pred.reshape(7, HOURS).sum(1)
        return float(np.mean(np.abs(pa - ya) / np.maximum(ya, 1e-9)))

    cover = float(np.mean((y >= q[0]) & (y <= q[2])))
    return {
        "wape_hourly": wape(q[1]),
        "naive_wape_hourly": wape(prev),
        "mape_daily": daily_mape(q[1]),
        "naive_mape_daily": daily_mape(prev),
        "interval_coverage_p10_p90": cover,
        "target_coverage": 0.8,
        "holdout": "synthetic ordinary week",
    }
