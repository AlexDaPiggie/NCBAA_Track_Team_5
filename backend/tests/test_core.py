import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import data, forecast, optimizer, workload  # noqa: E402
from app.config import HORIZON, get_config  # noqa: E402
from app.service import Engine  # noqa: E402

FAST = 3  # solver seconds per test plan


@pytest.fixture(scope="module")
def engine():
    return Engine()


def test_synthetic_data_is_deterministic():
    cfg = get_config()
    a, b = data.generate_history(cfg), data.generate_history(cfg)
    assert a.equals(b)
    assert len(a) == cfg["demand"]["history_weeks"] * HORIZON


def test_forecast_quantiles_ordered_and_beats_naive(engine):
    q = engine.base_q
    assert q.shape == (3, HORIZON)
    assert (q[0] <= q[1]).all() and (q[1] <= q[2]).all() and (q >= 0).all()
    bt = engine.backtest
    assert bt["wape_hourly"] < bt["naive_wape_hourly"]


def test_event_demand_exceeds_ordinary(engine):
    sc = engine.create_scenario("high")
    ev = engine.get_scenario(sc["id"])["q"][1].sum()
    assert ev > engine.base_q[1].sum() * 1.2


def test_same_scenario_same_reality(engine):
    a = engine.create_scenario("medium")
    b = engine.create_scenario("medium")
    ta, tb = engine.get_scenario(a["id"])["truth"], engine.get_scenario(b["id"])["truth"]
    assert np.array_equal(ta, tb)


def test_disruptions():
    base = np.ones((3, HORIZON))
    spike = forecast.apply_disruptions(base, [{"kind": "spike", "start_hour": 10, "end_hour": 14, "extra_arrivals": 8}])
    assert spike[1, 10:14].sum() == pytest.approx(4 + 8)
    cancel = forecast.apply_disruptions(base, [{"kind": "cancel", "start_hour": 0, "end_hour": 4, "fraction": 1.0}])
    assert cancel[1, :4].sum() == 0
    delay = forecast.apply_disruptions(base, [{"kind": "delay", "start_hour": 0, "end_hour": 4, "shift_hours": 2}])
    assert delay[1, 0:2].sum() == 0 and delay[1, 2:6].sum() == pytest.approx(6)  # moved 2 hrs, overlaps tail


def test_workload_monotone_and_respects_minimums():
    cfg = get_config()
    lo = workload.required_seats(np.full(HORIZON, 1.0), cfg)
    hi = workload.required_seats(np.full(HORIZON, 6.0), cfg)
    for r in cfg["staffing"]["roles"]:
        assert (hi[r] >= lo[r]).all()
        assert (lo[r] >= workload.min_seats_vector(cfg, r)).all()


def test_solver_respects_shift_rules(engine):
    plan = engine.make_plan(engine.create_scenario("medium")["id"], seconds=FAST)
    cfg = engine.cfg["staffing"]
    per_worker = defaultdict(list)
    for s in plan["shifts"]:
        per_worker[s["worker_id"]].append(s)
        assert s["end_hour"] - s["start_hour"] == cfg["shift_hours"]
    for w, shifts in per_worker.items():
        days = [s["day"] for s in shifts]
        assert len(days) == len(set(days)), f"{w} two shifts same day"
        assert len(shifts) <= cfg["weekly_shift_cap"]
        shifts.sort(key=lambda s: s["day"])
        for a, b in zip(shifts, shifts[1:]):
            if b["day"] == a["day"] + 1:
                gap = (b["day"] * 24 + b["start_hour"]) - (a["day"] * 24 + a["end_hour"])
                assert gap >= cfg["min_rest_hours"], f"{w} rest {gap}h"


def test_baseline_and_plan_scored_on_same_demand(engine):
    plan = engine.make_plan(engine.create_scenario("medium")["id"], seconds=FAST)
    comp = plan["comparison"]
    for key in ("expected_demand", "realized_synthetic_demand"):
        assert set(comp[key]) == {"baseline", "proposed"}
    # plan must not be worse than the ordinary-week roster on expected demand it was built for
    assert comp["expected_demand"]["proposed"]["understaffed_seat_hours"] <= \
        comp["expected_demand"]["baseline"]["understaffed_seat_hours"]


def test_evaluate_scores_empty_roster_as_fully_short(engine):
    cfg = engine.cfg
    req = workload.required_seats(np.full(HORIZON, 2.0), cfg)
    m = optimizer.evaluate([], req, cfg)
    assert m["coverage_pct"] == 0 and m["labor_cost_usd"] == 0


def test_human_approval_gate_and_audit(engine):
    plan = engine.make_plan(engine.create_scenario("low")["id"], seconds=FAST)
    assert plan["status"] == "proposed"
    n = len(engine.audit)
    out = engine.decide(plan["id"], "approve", "manager", "ok")
    assert out["status"] == "approved" and len(engine.audit) == n + 1
    assert engine.audit[-1]["actor"] == "manager"
    with pytest.raises(ValueError):
        engine.decide(plan["id"], "dispatch", "manager")


def test_edit_recomputes_metrics(engine):
    plan = engine.make_plan(engine.create_scenario("low")["id"], seconds=FAST)
    before = plan["comparison"]["expected_demand"]["proposed"]["coverage_pct"]
    out = engine.decide(plan["id"], "edit", "manager", "cut all", shifts=plan["shifts"][:5])
    assert out["status"] == "edited"
    assert out["comparison"]["expected_demand"]["proposed"]["coverage_pct"] < before


def test_risk_map_shape_and_range(engine):
    plan = engine.make_plan(engine.create_scenario("medium")["id"], seconds=FAST)
    r = engine.risk(plan["id"])
    assert len(r["p_understaffed"]) == HORIZON
    assert all(0 <= v <= 1 for v in r["p_understaffed"])


def test_no_passenger_fields_in_plan(engine):
    plan = engine.make_plan(engine.create_scenario("low")["id"], seconds=FAST)
    blob = str(plan).lower()
    for bad in ("passenger_name", "passport", "ssn", "tail_number"):
        assert bad not in blob


def test_api_404_and_422():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get("/forecast", params={"scenario_id": "nope"}).status_code == 404
    assert c.post("/decision", json={"plan_id": "nope", "action": "approve"}).status_code == 404
    assert c.post("/scenarios", json={"name": "custom"}).status_code == 422
