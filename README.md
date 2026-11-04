# SparkHill Hacks: Track 1 - The Intelligent FBO

## Challenge

- AI planning tool for FBO, 7-day window around Super Bowl LXI week, Los Angeles.
- Pick ONE pressure point: aircraft arrivals / parking / fuel / staffing.
- OUR DECISION: scope = ALL four (arrivals, parking, fuel, staffing) as one integrated plan. Judges confirmed OK (verbal, by team). Built so far: arrivals forecast + staffing optimizer; parking and fuel only enter as drivers, not yet their own plans.
- Public or synthetic data. Document every assumption.
- Stretch: adapt for LA 2028 Olympics.

## Required workflow

1. Baseline + forecast: ordinary week vs Super Bowl week demand.
2. Scenario plan: low / medium / high demand prep.
3. Measure impact: forecast accuracy + resource improvement.

## Deliverables

- Working prototype (planning workflow).
- 3-min pitch: user, problem, value.
- Demo: baseline comparison + demand spike or delay.
- Show: accuracy + savings, service maintained, explainable + safe.

## Judging

1. Innovation + accuracy
2. Practical preparation
3. Privacy, uncertainty, humans in command

## Rule: AI assists, people decide

- Planning support only. No movement authority. No auto dispatch.
- Every recommendation goes through human approval gate.
- No sensitive passenger data.
- Show uncertainty + assumptions.
- Pitch must answer: what should AI never decide? what stays human-only?
## Built so far (status)

Stack: FastAPI + Python backend, Next.js + TS frontend, OR-Tools CP-SAT solver, scikit-learn forecast, OpenRouter LLM co-pilot (key in env `OPENROUTER_API_KEY`, model default `anthropic/claude-sonnet-5.5`, override `OPENROUTER_MODEL`).

- `config/assumptions.yaml` = ALL assumptions, all unverified. Change values there only.
- `backend/app`: `data` (seeded synthetic), `forecast` (Poisson GBM + P10/P90 + naive baseline), `workload` (arrivals -> seats; parking + fuel as drivers), `optimizer` (roster solver + scoring), `simulate` (Monte Carlo risk), `service` (engine, approval gate, audit), `agent` (LLM tool-calling), `main` (API).
- `frontend/app`: single dashboard (scenarios, risk slider, KPIs baseline vs plan, forecast, seats, risk heatmap, co-pilot, approval, assumptions).
- Baseline = ordinary-week roster reused for event scenario. Same demand scores both.
- Not done: Olympics profile, roster edit UI, override learning, export.

## Run (Windows, global Python/Node, no venv)

```
pip install -r backend/requirements.txt
cd backend && python -m uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev      # http://localhost:3000
cd backend && python -m pytest -q              # 14 tests
```
