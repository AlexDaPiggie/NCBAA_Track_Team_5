"""FastAPI app. Planning support only: no dispatch, no movement authority."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import CopilotIn, DecisionIn, PlanIn, ScenarioIn
from .service import Engine

app = FastAPI(title="Staffing planner (synthetic data)")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])
engine = Engine()


def _plan_public(p: dict) -> dict:
    keys = ("id", "scenario_id", "status", "risk_z", "shifts", "baseline_shifts", "comparison",
            "solver", "solve_seconds", "required_seats", "supply_seats", "assumptions", "rationale")
    return {k: p[k] for k in keys}


def _guard(fn):
    try:
        return fn()
    except KeyError as e:
        raise HTTPException(404, {"error": "not_found", "detail": str(e)})
    except ValueError as e:
        raise HTTPException(422, {"error": "invalid", "detail": str(e)})


@app.get("/health")
def health():
    return {"ok": True, "data": "SYNTHETIC"}


@app.get("/assumptions")
def assumptions():
    return {"summary": engine.assumptions_summary(),
            "config": engine.cfg,
            "unverified": "All service times, uplift, pool sizes, wages: not verified with an aviation expert."}


@app.post("/scenarios")
def create_scenario(body: ScenarioIn):
    return _guard(lambda: engine.create_scenario(
        body.name, body.custom_intensity, [d.model_dump() for d in body.disruptions], body.parent_id))


@app.get("/scenario/{scenario_id}")
def get_scenario(scenario_id: str):
    return _guard(lambda: engine.scenario_public(engine.get_scenario(scenario_id)))


@app.get("/forecast")
def get_forecast(scenario_id: str):
    return _guard(lambda: engine.forecast_view(scenario_id))


@app.post("/plan")
def post_plan(body: PlanIn):
    return _guard(lambda: _plan_public(engine.make_plan(body.scenario_id, body.risk_z)))


@app.get("/plan/{plan_id}")
def get_plan(plan_id: str):
    return _guard(lambda: _plan_public(engine.get_plan(plan_id)))


@app.get("/risk")
def get_risk(plan_id: str):
    return _guard(lambda: engine.risk(plan_id))


@app.post("/decision")
def post_decision(body: DecisionIn):
    shifts = [s.model_dump() for s in body.shifts] if body.shifts else None
    return _guard(lambda: _plan_public(engine.decide(body.plan_id, body.action, body.actor, body.note, shifts)))


@app.get("/audit")
def get_audit():
    return engine.audit


@app.post("/copilot")
def post_copilot(body: CopilotIn):
    from .agent import run_copilot
    return _guard(lambda: run_copilot(engine, body.message, body.scenario_id, body.history))
