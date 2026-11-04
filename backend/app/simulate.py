"""Monte Carlo risk: chance a plan is short of seats, per hour."""
from __future__ import annotations

import numpy as np

from .config import HORIZON, HOURS
from .optimizer import supply_seats
from .workload import required_seats


def risk_map(shifts: list[dict], expected: np.ndarray, intensity: float, cfg: dict, seed: int = 0) -> dict:
    r = cfg["risk"]
    rng = np.random.default_rng(cfg["seed"] + 7 + seed)
    sims = int(r["sims"])
    sigma = float(r["daily_sigma"]) + float(cfg["demand"]["event_sigma"]) * float(intensity)
    f_day = rng.lognormal(mean=-0.5 * sigma**2, sigma=sigma, size=(sims, 7))
    f = np.repeat(f_day, HOURS, axis=1)
    arr = rng.poisson(expected[None, :] * f).astype(float)
    req = required_seats(arr, cfg)
    sup = supply_seats(shifts)
    roles = cfg["staffing"]["roles"]
    any_short = np.zeros((sims, HORIZON), dtype=bool)
    short_seat_hours = np.zeros(sims)
    by_role = {}
    for role in roles:
        s = sup.get(role, np.zeros(HORIZON))[None, :]
        gap = req[role] - s
        short = gap > 1e-9
        any_short |= short
        short_seat_hours += np.maximum(gap, 0).sum(axis=1)
        by_role[role] = short.mean(axis=0)
    p = any_short.mean(axis=0)
    return {
        "p_understaffed": [round(float(v), 3) for v in p],
        "by_role": {k: [round(float(v), 3) for v in a] for k, a in by_role.items()},
        "expected_short_seat_hours": round(float(short_seat_hours.mean()), 1),
        "p90_short_seat_hours": round(float(np.percentile(short_seat_hours, 90)), 1),
        "sims": sims,
    }
