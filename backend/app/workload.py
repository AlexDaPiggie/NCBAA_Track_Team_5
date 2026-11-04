"""Arrivals -> crew workload -> required seats.

Arrivals are the driver. Parking (apron congestion) and fuel (uplift) enter as
workload terms for the staffing plan. They are not separate products.
Vectorised: `arr` may be (168,) or (sims, 168).
"""
from __future__ import annotations

import numpy as np

from .config import HORIZON, HOURS


def _shift_right(a: np.ndarray, k: int) -> np.ndarray:
    out = np.zeros_like(a)
    if k <= 0:
        return a.copy()
    if k < a.shape[-1]:
        out[..., k:] = a[..., :-k]
    return out


def workload_minutes(arr: np.ndarray, cfg: dict) -> dict[str, np.ndarray]:
    s = cfg["service"]
    dep = _shift_right(arr, int(s["departure_lag_hours"]))
    ground = np.zeros_like(arr)
    for k in range(int(s["apron_dwell_hours"])):
        ground += _shift_right(arr, k)
    excess = np.maximum(ground - s["apron_capacity"], 0.0)
    return {
        "ramp": arr * s["ramp_min_arrival"] + dep * s["ramp_min_departure"]
        + arr * s["reposition_min_per_arrival_at_full_apron"]
        * np.clip(excess / s["apron_capacity"], 0.0, 1.0),
        "fuel": dep * s["fuel_prob"] * s["fuel_min"],
        "cs": arr * s["cs_min_arrival"] + dep * s["cs_min_departure"],
    }


def min_seats_vector(cfg: dict, role: str) -> np.ndarray:
    st = cfg["staffing"]
    night = np.isin(np.arange(HORIZON) % HOURS, st["night_hours"])
    return np.where(night, st["min_seats"]["night"][role], st["min_seats"]["day"][role]).astype(float)


def required_seats(arr: np.ndarray, cfg: dict) -> dict[str, np.ndarray]:
    util = cfg["service"]["target_utilization"]
    tol = cfg["service"]["seat_tolerance"]
    out = {}
    for role, minutes in workload_minutes(arr, cfg).items():
        seats = np.ceil(minutes / 60.0 / util - tol)
        out[role] = np.maximum(seats, min_seats_vector(cfg, role))
    return out
