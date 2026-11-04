# MVP_PLAN

Product: staffing planner for FBO, Super Bowl LXI week LA. AI assists, manager approves.

## Stack (justify any change)

- Frontend: Next.js + TypeScript.
- Backend: FastAPI + Python.
- Solver: OR-Tools CP-SAT (or PuLP fallback).
- Forecast: statsmodels / scikit-learn (gradient boosting or Poisson/NegBin with quantiles).
- LLM: Claude via API, tool-calling. Key via env var, never committed.
- Windows + VS Code friendly. No Docker required.

## Modules + owners

| Module | Owner | Output |
|---|---|---|
| `backend/data` | A | Seeded synthetic generator, LAX timing profile, fixtures |
| `backend/forecast` | A | Baseline + model forecast, P10/P50/P90, backtest metrics |
| `backend/optimizer` | B | Roster solver, Monte Carlo risk, baseline-vs-plan metrics |
| `backend/agent` + `backend/api` | C | FastAPI endpoints, LLM co-pilot, approval gate, audit log |
| `frontend` | D | Dashboard, approval UI, disruption injection, pitch assets |
| `config/assumptions.yaml` | shared | All staffing assumptions, configurable |

## Phases

1. **Foundation (h0-2):** contract (`docs/API_CONTRACT.md`), config, repo skeleton, mock fixtures.
2. **Modules vs mocks (h2-20):** each owner builds + unit tests against contract.
3. **Integration (h20-30):** replace mocks, end-to-end test.
4. **Demo features (h30-42):** disruption replay, risk heatmap, co-pilot polish, baseline comparison.
5. **Freeze (h42-48):** rehearsal, backup recording, docs.

## MVP scope (must)

- Seeded synthetic demand for ordinary week + Super Bowl week.
- Forecast with intervals, accuracy vs naive baseline.
- Solver roster for low/med/high with real constraints (shift length, min rest, weekly cap, breaks, role qualification, min coverage per role).
- Baseline vs proposed on same scenario: coverage, understaffed hours, labor cost.
- Approve / edit / reject per recommendation + audit log.
- Disruption test: demand spike or delay, re-plan.

## Nice to have (cut first)

LLM co-pilot (high value, do if time), Monte Carlo heatmap, morning briefing export, Olympics profile, override learning loop, voice.

## Success metrics (all measured, never invented)

- Forecast MAPE and P10-P90 coverage vs naive baseline, on holdout.
- Understaffed seat-hours, overtime hours, labor cost: baseline vs plan, same scenario.
- Re-plan latency after disruption.
- Test pass count.

## Definition of done

`README` run steps work on a clean Windows machine; tests green; demo script runs end to end offline (LLM fallback = scripted prompts cached) .
