"""LLM co-pilot via OpenRouter. The model only calls tools; every number comes
from tool results. It can propose scenarios and plans, never approve or dispatch.
"""
from __future__ import annotations

import json
import os

import numpy as np
from openai import OpenAI

from .service import Engine

MAX_STEPS = 6

SYSTEM = """You are the planning co-pilot for an FBO operations manager (Super Bowl week, SYNTHETIC data).
Rules:
- Every number you state must come from a tool result. Never guess or invent numbers.
- Hour index = day*24 + hour of day, day 0 = Mon ... 6 = Sun. Convert times the manager gives you.
- To test a disruption: create_scenario (with disruptions) then make_plan, then explain the change versus the earlier plan.
- You recommend only. You cannot approve plans, dispatch workers, or authorize aircraft movements. Say so if asked.
- Mention uncertainty and that service times, uplift and wages are unverified assumptions when relevant.
- Be short and plain: 3-6 sentences or a tiny list. No filler."""

TOOLS = [
    {"type": "function", "function": {
        "name": "create_scenario",
        "description": "Create a demand scenario for the 7-day window, optionally with disruptions.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "enum": ["ordinary", "low", "medium", "high", "custom"]},
            "custom_intensity": {"type": "number", "description": "only for name=custom"},
            "disruptions": {"type": "array", "items": {"type": "object", "properties": {
                "kind": {"type": "string", "enum": ["spike", "delay", "cancel"]},
                "start_hour": {"type": "integer"}, "end_hour": {"type": "integer"},
                "extra_arrivals": {"type": "number"}, "shift_hours": {"type": "integer"},
                "fraction": {"type": "number"}, "note": {"type": "string"}},
                "required": ["kind", "start_hour", "end_hour"]}}},
            "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "get_forecast",
        "description": "Daily arrival forecast vs ordinary week plus accuracy metrics for a scenario.",
        "parameters": {"type": "object", "properties": {"scenario_id": {"type": "string"}},
                       "required": ["scenario_id"]}}},
    {"type": "function", "function": {
        "name": "make_plan",
        "description": "Optimize a staffing roster for a scenario and compare to the ordinary-week roster. "
                       "risk_z 0=lean, 1=protected.",
        "parameters": {"type": "object", "properties": {
            "scenario_id": {"type": "string"}, "risk_z": {"type": "number"}},
            "required": ["scenario_id"]}}},
    {"type": "function", "function": {
        "name": "get_risk",
        "description": "Monte Carlo risk of understaffing for a plan.",
        "parameters": {"type": "object", "properties": {"plan_id": {"type": "string"}},
                       "required": ["plan_id"]}}},
]


def _compact_plan(p: dict, cfg: dict) -> dict:
    c = p["comparison"]
    return {"plan_id": p["id"], "scenario_id": p["scenario_id"], "status": p["status"],
            "risk_z": p["risk_z"], "shift_count": len(p["shifts"]),
            "peak_seats_required": {r: int(max(v)) for r, v in p["required_seats"].items()},
            "expected_demand": c["expected_demand"], "realized_synthetic_demand": c["realized_synthetic_demand"],
            "baseline": c["baseline_definition"], "solve_seconds": p["solve_seconds"],
            "rationale": p["rationale"]}


def _run_tool(engine: Engine, name: str, args: dict) -> dict:
    if name == "create_scenario":
        return engine.create_scenario(args.get("name", "medium"), args.get("custom_intensity"),
                                      args.get("disruptions") or [])
    if name == "get_forecast":
        f = engine.forecast_view(args["scenario_id"])
        return {"daily": f["daily"], "metrics": f["metrics"], "label": f["label"]}
    if name == "make_plan":
        return _compact_plan(engine.make_plan(args["scenario_id"], args.get("risk_z")), engine.cfg)
    if name == "get_risk":
        r = engine.risk(args["plan_id"])
        p = np.asarray(r["p_understaffed"])
        top = np.argsort(-p)[:5]
        return {"expected_short_seat_hours": r["expected_short_seat_hours"],
                "p90_short_seat_hours": r["p90_short_seat_hours"],
                "riskiest_hours": [{"hour_index": int(t), "day": int(t // 24), "hour": int(t % 24),
                                    "p_understaffed": float(p[t])} for t in top]}
    raise ValueError(f"unknown tool {name}")


def run_copilot(engine: Engine, message: str, scenario_id: str | None = None,
                history: list[dict] | None = None) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set")
    cfg = engine.cfg["copilot"]
    model = os.environ.get(cfg["model_env"], cfg["default_model"])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

    ctx = f" Current scenario_id: {scenario_id}." if scenario_id else ""
    msgs = [{"role": "system", "content": SYSTEM + ctx}] + (history or []) + [{"role": "user", "content": message}]
    calls: list[dict] = []
    sid, pid = scenario_id, None
    for _ in range(MAX_STEPS):
        resp = client.chat.completions.create(model=model, messages=msgs, tools=TOOLS, temperature=0.2)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {"reply": msg.content or "", "tool_calls": calls, "scenario_id": sid,
                    "plan_id": pid, "model": model}
        msgs.append({"role": "assistant", "content": msg.content or "",
                     "tool_calls": [{"id": t.id, "type": "function",
                                     "function": {"name": t.function.name, "arguments": t.function.arguments}}
                                    for t in msg.tool_calls]})
        for t in msg.tool_calls:
            try:
                args = json.loads(t.function.arguments or "{}")
                result = _run_tool(engine, t.function.name, args)
            except Exception as e:  # report tool errors to the model, not silently
                args, result = {}, {"error": str(e)}
            if isinstance(result, dict):
                sid = result.get("id", sid) if t.function.name == "create_scenario" else result.get("scenario_id", sid)
                if t.function.name == "make_plan":
                    pid = result.get("plan_id", pid)
            calls.append({"name": t.function.name, "args": args, "result": result})
            msgs.append({"role": "tool", "tool_call_id": t.id, "content": json.dumps(result, default=float)})
    return {"reply": "Stopped: too many tool steps.", "tool_calls": calls, "scenario_id": sid,
            "plan_id": pid, "model": model}
