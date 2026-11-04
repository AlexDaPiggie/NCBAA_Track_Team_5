"""Engine: scenarios -> forecast -> plan -> compare -> risk -> human decision.

Everything is SYNTHETIC. Plans are recommendations (`status: proposed`) until a
human decides. Nothing here dispatches workers or authorizes movements.
"""
from __future__ import annotations

import itertools
import threading
import time
from datetime import datetime, timezone

import numpy as np

from . import data, forecast, optimizer, simulate, workload
from .config import HORIZON, HOURS, get_config


def _r(a: np.ndarray, n: int = 2) -> list[float]:
    return [round(float(v), n) for v in a]


class Engine:
    def __init__(self, cfg: dict | None = None) -> None:
        self.cfg = cfg or get_config()
        self.lock = threading.Lock()
        self.history = data.generate_history(self.cfg)
        self.backtest = forecast.backtest(self.history)
        self.fc = forecast.ArrivalForecaster().fit(self.history)
        self.base_q = self.fc.predict_week()
        self.scenarios: dict[str, dict] = {}
        self.plans: dict[str, dict] = {}
        self.audit: list[dict] = []
        self._baseline_cache: dict[float, list[dict]] = {}
        self._ids = itertools.count(1)

    # ---- scenarios -------------------------------------------------------
    def create_scenario(self, name: str = "medium", custom_intensity: float | None = None,
                        disruptions: list[dict] | None = None, parent_id: str | None = None) -> dict:
        cfg = self.cfg
        intensity = data.intensity_for(cfg, name, custom_intensity)
        disruptions = disruptions or []
        q = forecast.apply_uplift(self.base_q, data.day_multipliers(cfg, intensity),
                                  cfg["demand"]["event_sigma"], intensity)
        q = forecast.apply_disruptions(q, disruptions)
        # same stream for same intensity so baseline and plan face one "reality"
        stream = 100 + int(round(intensity * 100))
        truth = forecast.apply_disruptions(
            data.realized(cfg, data.scenario_mean(cfg, intensity), stream=stream), disruptions)
        sid = f"sc{next(self._ids)}"
        sc = {"id": sid, "name": name, "intensity": intensity, "seed": cfg["seed"],
              "disruptions": disruptions, "parent_id": parent_id,
              "q": q, "truth": truth}
        self.scenarios[sid] = sc
        return self.scenario_public(sc)

    @staticmethod
    def scenario_public(sc: dict) -> dict:
        return {k: sc[k] for k in ("id", "name", "intensity", "seed", "disruptions", "parent_id")}

    def get_scenario(self, sid: str) -> dict:
        if sid not in self.scenarios:
            raise KeyError(f"unknown scenario {sid}")
        return self.scenarios[sid]

    # ---- forecast --------------------------------------------------------
    def forecast_view(self, sid: str) -> dict:
        sc = self.get_scenario(sid)
        q, truth = sc["q"], sc["truth"]
        y = truth
        hourly_wape = float(np.abs(q[1] - y).sum() / max(y.sum(), 1e-9))
        ya, pa = y.reshape(7, HOURS).sum(1), q[1].reshape(7, HOURS).sum(1)
        ord_q = self.base_q[1]
        naive_wape = float(np.abs(ord_q - y).sum() / max(y.sum(), 1e-9))
        return {
            "scenario_id": sid,
            "points": [{"day": t // HOURS, "hour": t % HOURS, "p10": round(float(q[0, t]), 3),
                        "expected": round(float(q[1, t]), 3), "p90": round(float(q[2, t]), 3),
                        "ordinary_expected": round(float(ord_q[t]), 3),
                        "realized_synthetic": float(truth[t])} for t in range(HORIZON)],
            "daily": {"forecast": _r(pa, 1), "realized_synthetic": _r(ya, 1),
                      "ordinary": _r(ord_q.reshape(7, HOURS).sum(1), 1)},
            "metrics": {
                "backtest": self.backtest,
                "scenario_check": {
                    "wape_hourly": round(hourly_wape, 3),
                    "naive_ordinary_week_wape_hourly": round(naive_wape, 3),
                    "mape_daily": round(float(np.mean(np.abs(pa - ya) / np.maximum(ya, 1e-9))), 3),
                    "interval_coverage_p10_p90": round(float(np.mean((y >= q[0]) & (y <= q[2]))), 3),
                    "note": "vs one SYNTHETIC realization. Not real-world accuracy.",
                },
            },
            "label": "SYNTHETIC",
        }

    # ---- planning --------------------------------------------------------
    def _plan_arrivals(self, q: np.ndarray, z: float) -> np.ndarray:
        return q[1] + z * (q[2] - q[1])

    def _baseline_roster(self, z: float) -> list[dict]:
        key = round(z, 3)
        if key not in self._baseline_cache:
            req = workload.required_seats(self._plan_arrivals(self.base_q, z), self.cfg)
            self._baseline_cache[key], _ = optimizer.solve_roster(req, self.cfg)
        return self._baseline_cache[key]

    def make_plan(self, sid: str, risk_z: float | None = None, seconds: float | None = None) -> dict:
        cfg = self.cfg
        sc = self.get_scenario(sid)
        z = cfg["planning"]["risk_z"] if risk_z is None else float(risk_z)
        t0 = time.time()
        plan_arr = self._plan_arrivals(sc["q"], z)
        req_plan = workload.required_seats(plan_arr, cfg)
        shifts, info = optimizer.solve_roster(req_plan, cfg, seconds)
        solve_s = time.time() - t0

        req_exp = workload.required_seats(sc["q"][1], cfg)
        req_real = workload.required_seats(sc["truth"], cfg)
        base_shifts = self._baseline_roster(z)
        comparison = {
            "baseline_definition": "ordinary-week roster (solved on ordinary forecast), reused for this scenario",
            "expected_demand": {"baseline": optimizer.evaluate(base_shifts, req_exp, cfg),
                                "proposed": optimizer.evaluate(shifts, req_exp, cfg)},
            "realized_synthetic_demand": {"baseline": optimizer.evaluate(base_shifts, req_real, cfg),
                                          "proposed": optimizer.evaluate(shifts, req_real, cfg)},
        }
        pid = f"plan{next(self._ids)}"
        plan = {
            "id": pid, "scenario_id": sid, "status": "proposed", "risk_z": z,
            "shifts": shifts, "baseline_shifts": base_shifts,
            "comparison": comparison, "solver": info, "solve_seconds": round(solve_s, 2),
            "required_seats": {r: _r(v, 0) for r, v in req_plan.items()},
            "supply_seats": {r: _r(v, 1) for r, v in optimizer.supply_seats(shifts).items()},
            "assumptions": self.assumptions_summary(),
        }
        plan["rationale"] = self._rationale(plan, sc, req_plan)
        self.plans[pid] = plan
        return plan

    def _rationale(self, plan: dict, sc: dict, req_plan: dict) -> list[str]:
        cfg = self.cfg
        exp = plan["comparison"]["expected_demand"]
        b, p = exp["baseline"], exp["proposed"]
        daily = sc["q"][1].reshape(7, HOURS).sum(1)
        peak = int(np.argmax(daily))
        label = cfg["window"]["day_labels"][peak]
        out = [
            f"Busiest day {label}: about {daily[peak]:.0f} arrivals expected "
            f"vs {self.base_q[1].reshape(7, HOURS).sum(1)[peak]:.0f} in an ordinary week.",
            "Peak seats needed: " + ", ".join(
                f"{r} {int(v.max())}" for r, v in req_plan.items()) + ".",
            f"Coverage of expected demand: {b['coverage_pct']}% (ordinary roster) -> {p['coverage_pct']}% (plan).",
            f"Labor cost: ${b['labor_cost_usd']:,.0f} -> ${p['labor_cost_usd']:,.0f} "
            f"(illustrative wages). Extra cost buys {b['understaffed_seat_hours'] - p['understaffed_seat_hours']:.0f} fewer short seat-hours.",
            f"Plan basis: expected + {plan['risk_z']:.2f} x (P90 - expected). Higher = safer, costlier.",
        ]
        if sc["disruptions"]:
            out.append("Disruptions applied: " + "; ".join(
                f"{d['kind']} h{d['start_hour']}-{d['end_hour']}" for d in sc["disruptions"]) + ".")
        out.append("Recommendation only. A manager must approve before use.")
        return out

    def assumptions_summary(self) -> list[str]:
        c = self.cfg
        return [
            "All demand is SYNTHETIC (seeded). Not real FBO data.",
            f"Event uplift curve is an assumption: {c['demand']['event_day_curve']} x intensity.",
            f"Service minutes per aircraft are assumptions: {c['service']['ramp_min_arrival']}/"
            f"{c['service']['ramp_min_departure']} ramp, {c['service']['fuel_min']} fuel, "
            f"{c['service']['cs_min_arrival']}/{c['service']['cs_min_departure']} customer service. UNVERIFIED.",
            f"Parking and fuel enter only as workload drivers (apron capacity {c['service']['apron_capacity']}, "
            f"fuel probability {c['service']['fuel_prob']}).",
            "Wages are illustrative. Shift rules: 8 h, 5 shifts/week, 8 h rest, 30 min break.",
        ]

    # ---- risk ------------------------------------------------------------
    def risk(self, pid: str) -> dict:
        plan = self.get_plan(pid)
        sc = self.get_scenario(plan["scenario_id"])
        return simulate.risk_map(plan["shifts"], sc["q"][1], sc["intensity"], self.cfg)

    # ---- human decision --------------------------------------------------
    def get_plan(self, pid: str) -> dict:
        if pid not in self.plans:
            raise KeyError(f"unknown plan {pid}")
        return self.plans[pid]

    def decide(self, pid: str, action: str, actor: str, note: str = "",
               shifts: list[dict] | None = None) -> dict:
        if action not in ("approve", "reject", "edit"):
            raise ValueError("action must be approve|reject|edit")
        plan = self.get_plan(pid)
        sc = self.get_scenario(plan["scenario_id"])
        if action == "edit":
            if not shifts:
                raise ValueError("edit needs shifts")
            plan["shifts"] = shifts
            req_exp = workload.required_seats(sc["q"][1], self.cfg)
            req_real = workload.required_seats(sc["truth"], self.cfg)
            plan["comparison"]["expected_demand"]["proposed"] = optimizer.evaluate(shifts, req_exp, self.cfg)
            plan["comparison"]["realized_synthetic_demand"]["proposed"] = optimizer.evaluate(shifts, req_real, self.cfg)
            plan["supply_seats"] = {r: _r(v, 1) for r, v in optimizer.supply_seats(shifts).items()}
        plan["status"] = {"approve": "approved", "reject": "rejected", "edit": "edited"}[action]
        self.audit.append({"plan_id": pid, "action": action, "actor": actor, "note": note,
                           "ts": datetime.now(timezone.utc).isoformat()})
        return plan
