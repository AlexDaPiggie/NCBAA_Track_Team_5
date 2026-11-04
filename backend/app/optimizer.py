"""Roster solver (OR-Tools CP-SAT). Real constraints, no canned output.

Per role: workers get at most one shift/day, weekly shift cap, min rest between
consecutive days, a 30 min break (half capacity for one hour of the shift).
Capacity is in half-seat units. Shortage is penalised hardest, then labor cost.
"""
from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from ortools.sat.python import cp_model

from .config import HORIZON, HOURS


def _starts(cfg: dict) -> list[int]:
    return list(range(0, HOURS, int(cfg["staffing"]["shift_start_step"])))


def solve_role(role: str, req_seats: np.ndarray, cfg: dict, seconds: float | None = None) -> tuple[list[dict], dict]:
    st = cfg["staffing"]
    L = int(st["shift_hours"])
    brk = int(st["break_offset_hours"])
    rest = int(st["min_rest_hours"])
    cap = int(st["weekly_shift_cap"])
    wage = float(st["wage_per_hour"][role])
    starts = _starts(cfg)
    req = (np.asarray(req_seats) * 2).astype(int)  # half-seat units

    # pool: enough for peak, bounded by config cap
    pool = int(min(st["pool_cap"][role], max(2, math.ceil(req.max() / 2 * 3.5))))

    m = cp_model.CpModel()
    x = {(w, d, s): m.NewBoolVar(f"x{w}_{d}_{s}")
         for w in range(pool) for d in range(7) for s in starts}
    for w in range(pool):
        for d in range(7):
            m.Add(sum(x[w, d, s] for s in starts) <= 1)
        m.Add(sum(x[w, d, s] for d in range(7) for s in starts) <= cap)
        for d in range(6):
            for s in starts:
                for s2 in starts:
                    if s2 + 24 - (s + L) < rest:
                        m.Add(x[w, d, s] + x[w, d + 1, s2] <= 1)
    # symmetry breaking: lower-index workers carry at least as many shifts
    tot = [sum(x[w, d, s] for d in range(7) for s in starts) for w in range(pool)]
    for w in range(pool - 1):
        m.Add(tot[w] >= tot[w + 1])

    cover: dict[int, list] = {t: [] for t in range(HORIZON)}
    cost_terms = []
    for (w, d, s), var in x.items():
        t0 = d * HOURS + s
        for k in range(L):
            t = t0 + k
            if t < HORIZON:
                cover[t].append((2 if k != brk else 1) * var)
                cost_terms.append(int(round(wage)) * var)  # in-window hours only
    short = []
    for t in range(HORIZON):
        sv = m.NewIntVar(0, int(req[t]), f"short{t}")
        m.Add(sv >= int(req[t]) - sum(cover[t]))
        short.append(sv)
    m.Minimize(int(st["shortage_penalty"]) * sum(short) + sum(cost_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds or st["solver_seconds"])
    solver.parameters.num_workers = 4
    solver.parameters.random_seed = int(cfg["seed"]) % 100000
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return [], {"status": solver.StatusName(status)}

    shifts = []
    for (w, d, s), var in x.items():
        if solver.Value(var):
            shifts.append({"worker_id": f"{role}-{w + 1:02d}", "role": role, "day": d,
                           "start_hour": s, "end_hour": s + L, "break_hour": s + brk})
    shifts.sort(key=lambda z: (z["day"], z["start_hour"], z["worker_id"]))
    return shifts, {"status": solver.StatusName(status), "pool": pool,
                    "objective": solver.ObjectiveValue(), "bound": solver.BestObjectiveBound()}


def solve_roster(req: dict[str, np.ndarray], cfg: dict, seconds: float | None = None) -> tuple[list[dict], dict]:
    roles = cfg["staffing"]["roles"]
    with ThreadPoolExecutor(max_workers=len(roles)) as ex:
        futs = {r: ex.submit(solve_role, r, req[r], cfg, seconds) for r in roles}
        results = {r: f.result() for r, f in futs.items()}
    shifts = [s for r in roles for s in results[r][0]]
    return shifts, {r: results[r][1] for r in roles}


def supply_seats(shifts: list[dict]) -> dict[str, np.ndarray]:
    """Seats on duty per hour (break hour counts half)."""
    out: dict[str, np.ndarray] = {}
    for s in shifts:
        arr = out.setdefault(s["role"], np.zeros(HORIZON))
        for t in range(s["start_hour"], s["end_hour"]):
            tt = s["day"] * HOURS + t
            if 0 <= tt < HORIZON:
                arr[tt] += 0.5 if t == s["break_hour"] else 1.0
    return out


def evaluate(shifts: list[dict], req: dict[str, np.ndarray], cfg: dict) -> dict:
    """Same function scores baseline and proposed plans on the same demand."""
    sup = supply_seats(shifts)
    roles = cfg["staffing"]["roles"]
    short_h = surplus_h = req_h = 0.0
    short_hours_any = np.zeros(HORIZON, dtype=bool)
    for r in roles:
        s = sup.get(r, np.zeros(HORIZON))
        gap = req[r] - s
        short_h += float(np.maximum(gap, 0).sum())
        surplus_h += float(np.maximum(-gap, 0).sum())
        req_h += float(req[r].sum())
        short_hours_any |= gap > 1e-9
    wage = cfg["staffing"]["wage_per_hour"]
    paid = 0.0
    cost = 0.0
    for sh in shifts:
        hrs = sum(1 for t in range(sh["start_hour"], sh["end_hour"])
                  if sh["day"] * HOURS + t < HORIZON)
        paid += hrs
        cost += hrs * float(wage[sh["role"]])
    return {
        "coverage_pct": round(100.0 * (1 - short_h / max(req_h, 1e-9)), 2),
        "understaffed_seat_hours": round(short_h, 1),
        "understaffed_hours": int(short_hours_any.sum()),
        "idle_seat_hours": round(surplus_h, 1),
        "paid_hours": round(paid, 1),
        "labor_cost_usd": round(cost, 2),
    }
