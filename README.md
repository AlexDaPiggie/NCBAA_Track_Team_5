# Apron · FBO Staffing Lab

Apron is a local demo for planning staff at an FBO. An FBO is a business at an airport that serves private and general aviation aircraft.
## Latest: six-screen event-week staffing workflow

Navigation follows the supplied planner brief: Setup & Inputs, Baseline vs Event Week, Gap Heatmap, Recommended Plan, Scenario Comparison, and Assumptions & Safety. The baseline/event screen displays the backend's 42 four-hour demand blocks; the heatmap uses the same block staffing requirements.

This remains a partial UI integration. The connected API models three departments, while the brief calls for seven zones and role qualifications. The API does not generate reassignment, overtime, part-time, or reserve recommendations or uncertainty intervals. Stage 6 adds same-scenario synthetic staffing impact metrics; these are not actual FBO performance. The synthetic event roster can be built and submitted for local manager approval.

## Latest: synthetic event-week planning comparison

The application defaults to the synthetic planning model. A synthetic-trained model and an optional JFK airline-activity proxy remain available; the proxy is not Los Angeles, private aviation, or FBO traffic. The Assumptions & Safety screen describes the source and validation limits.

Baseline vs Event Week shows ordinary and event demand; Scenario Comparison shows low/medium/high aircraft totals and peak staff requirements. These scenarios are planning cases, not confidence intervals. Manager approval remains required for the synthetic event roster.

Synthetic data and task requests are generated deterministically from a fixed seed. JFK proxy settings remain optional. The sections below explain setup and shared simulation assumptions.


The app estimates hourly work, compares staffing plans, and simulates waiting requests. A manager reviews any plan. The app does not assign real employees or control aircraft.

## How to use the website

1. **Setup & Inputs** configures the demand case, source, scale, seed, and current service-time assumptions. Click **Run Plan** to refresh demand outputs.
2. **Baseline vs Event Week** compares ordinary and event demand and lists all 42 four-hour blocks.
3. **Gap Heatmap** estimates required positions against the selected department coverage counts. It is not yet a seven-zone schedule coverage view.
4. **Recommended Plan** builds ordinary and event synthetic rosters under the same selected demand and disruption. Review the roster and submit an approve/reject decision with manager name and notes.
5. **Scenario Comparison** shows low/medium/high aircraft totals and peak staffing from the API. After building a roster, it also compares coverage, uncovered four-hour blocks, severe-gap blocks, modeled labor-cost delta, and an illustrative ramp delay-risk proxy against the unchanged ordinary-week roster under the same event inputs. Action hours and reserve efficiency are not available.
6. **Assumptions & Safety** explains provenance, privacy, uncertainty limits, and the manager's authority.

Roster decisions are saved locally through `/api/staffing-decisions`; no workers are contacted. Rebuild after changing any input before approving the roster.

The interface is English-only. Source details, assumptions, forecast scores and the optional workflow guide remain available without filling the default screen. The floor still replays the queue simulation using continuous staff positions. Shift-stress metrics are a separate capacity calculation, not a replay of waits under shift breaks. Worker availability is assumed and IDs are fictional.

The first shift schedule is separate from the seat-based simulation and supports the **Medium** scenario. The roster in [backend/synthetic_roster.py](backend/synthetic_roster.py) is entirely synthetic. It contains stable example IDs, department qualifications, day and shift availability, and weekly hour caps. It uses 6am–2pm, 2pm–10pm, and 10pm–6am shifts, each 8 hours long, and requires 10 hours of rest. For each department and block, shift demand is the maximum hourly integer seat requirement in that block. A deterministic greedy assignment favors workers with fewer assigned hours, then stable worker IDs. Any uncovered slot is shown as **outside staff needed**; this is an estimate, not a confirmed hire or a real-world staffing recommendation.

Queue cost, wait, and unfinished-work outputs remain available from the API's continuous seat simulation, which assumes selected positions are staffed. Schedule coverage is a separate roster feasibility estimate and does not alter those simulation results. The prototype does not validate the roster against real staffing conditions.

Departments in this demo: Passenger Services, Ramp Operations, and Fuel Services. This is a **staffing** project. “Fuel Services” means planning staff for fuel requests. It does not plan how much fuel to load.

## Data and limits

The default aircraft activity model is trained on generated synthetic history. JFK airline departures are available only as an optional proxy and are not FBO or Los Angeles data. Passenger counts, fuel demand, workers and service requests remain assumptions or synthetic. No mode has been validated for real FBO operations.

Service times, wages, staffing minimums, passenger counts, event multipliers, break durations, maximum hours, and rest periods are assumptions. They are not verified FBO rules or Super Bowl forecasts. Low, medium, and high are planning cases, not confidence intervals. Forecast scores come from generated holdout data and are not real-world accuracy. Shift plans use synthetic qualified workers who are assumed available; the model does not cover actual employee availability, fatigue, travel between tasks, or aircraft-task safety rules. Call-outs, arrival surges, and longer service times are synthetic stress inputs. Ask an FBO expert to review assumptions before treating results as realistic.

## Desktop program on Windows

Create the Python environment, then install the desktop dependencies and build:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
cd frontend
npm.cmd ci
npm.cmd run dev
cd ..
powershell -ExecutionPolicy Bypass -File .\build-desktop.ps1
```

Run `dist\ApronStaffingLab\ApronStaffingLab.exe`. Copy the entire program directory when sharing it. Edge WebView2 Runtime is required. No separate browser or backend terminal is needed. Approved decisions are stored locally under `%LOCALAPPDATA%\ApronStaffingLab`.

## Development preview on Windows

You need Python and Node.js installed. Open this folder in VS Code.

**Terminal 1 — backend**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m backend.model
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

**Terminal 2 — website**

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. Keep both terminals open while using the app. To stop a server, press **Ctrl+C** in its terminal.

### If simulation shows a 404

The website reached a server, but it did not find Apron's simulation API. In Terminal 1, stop the server with **Ctrl+C**. From the project root, start the backend again:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Check http://127.0.0.1:8000/docs. If the API page does not open, the backend is not running on the expected port. Keep it running, then refresh the website.

## Where things live

- [frontend/src/App.tsx](frontend/src/App.tsx) — pages, controls, charts, and manager review.
- [frontend/src/DepartmentView.tsx](frontend/src/DepartmentView.tsx) — animated request and staff-seat replay.
- [backend/main.py](backend/main.py) — API for simulations, replay, staffing plans, and manager decisions.
- [backend/model.py](backend/model.py) — demand, staffing needs, and waiting-line simulation.
- [backend/scheduling.py](backend/scheduling.py) — synthetic shift roster, break capacity, rest/hour limits, and disruption comparison.
- [backend/scheduler.py](backend/scheduler.py) and [backend/synthetic_roster.py](backend/synthetic_roster.py) — shift assignment algorithm and reviewable synthetic roster.
- [backend/training.py](backend/training.py) — train and measure the demo forecast model.
- [backend/data](backend/data) — synthetic input files and trained model.
- [backend/tests](backend/tests) — automated checks.

## API summary

- `POST /api/simulate` — runs the selected demand case and returns the hourly forecast, ordinary-week comparison profile, staffing requirements, plan metrics, provenance, and synthetic holdout report when the trained model is selected.
- `GET /api/scenario-summary` — accepts `multiplier`, `forecast_mode`, `proxy_scale`, and JSON `service_minutes` query parameters; returns ordinary-week totals plus low/medium/high event-week totals, peak activity, and peak concurrent seats by department.
- `POST /api/replay` — returns the seeded request trace for a selected staffing option.
- `POST /api/staffing-plan` — accepts the simulation inputs plus shift length, break minutes, weekly hour cap, rest gap, and disruption settings; builds baseline/event rosters and evaluates both under the same call-outs, arrival surge, and service delay. Returns four-hour understaffed/severe-gap counts and an `impact` object with same-scenario coverage, modeled cost, and delay-risk comparisons. The delay-risk proxy uses an assumed 10 minutes per uncovered Ramp Operations seat-hour and is not an aircraft delay forecast.
- `POST /api/schedule` — returns the legacy deterministic synthetic shift assignment for the Medium demand scenario.
- `POST /api/staffing-decisions` — recomputes and saves manager approval or rejection for a staffing roster.
- `POST /api/decisions` — stores a manager's approve/reject decision locally for a simulation snapshot.

Interactive request and response schemas are available at `http://127.0.0.1:8000/docs` while the backend is running.

Stage 6 impact inherits the selected data provenance. The repository has no verified LAX 2022 arrivals file, so results remain synthetic or clearly disclosed JFK airline-pattern proxy estimates; they are not validated LAX forecasts. See [Stage 6 metric definitions](docs/ASSUMPTIONS.md#stage-6-impact-metric-definitions).

## Useful commands

Run backend tests:

```powershell
python -m pytest backend/tests -q
```

Build the website:

```powershell
cd frontend
npm.cmd run build
```

Retrain the synthetic demo forecast:

```powershell
python -m backend.training
```

## Terms

- **Staff seat:** one qualified worker available to serve requests at the same time.
- **Baseline:** the simple starting staffing plan.
- **Scenario:** a low, medium, or high demand level.
- **Simulation:** a repeatable test of how requests wait for available staff.
- **Synthetic:** generated example data, not collected from a real FBO.
