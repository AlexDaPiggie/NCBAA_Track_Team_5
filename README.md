# Apron · FBO Staffing Lab

Apron is a local demo for planning staff at an FBO. An FBO is a business at an airport that serves private and general aviation aircraft.
## Latest: synthetic event-week planning comparison

The application defaults to a forecast trained and checked on generated synthetic history. The Demand page shows its held-out error beside a simple baseline and labels both as synthetic validation, not real-world accuracy. An optional JFK airline-activity proxy remains available for exploration; it is not Los Angeles, private aviation, or FBO traffic.

Demand shows ordinary-week and event-week profiles, with an expandable low/medium/high comparison. Staffing shows current coverage, peak needs and additional peak positions by department. Plan options also report same-demand costs and service outcomes. The assumption panel explains that scenarios are planning cases, not confidence intervals. Manager approval remains required.

Synthetic data and task requests are generated deterministically from a fixed seed. JFK proxy settings remain optional. The sections below explain setup and shared simulation assumptions.


The app estimates hourly work, compares staffing plans, and simulates waiting requests. A manager reviews any plan. The app does not assign real employees or control aircraft.

## How to use the website

1. Choose Quiet, Normal or Busy demand and click **Run Simulation**. Source, scaling and seed are under **Settings**.
2. **Live Floor** shows staff positions, the waiting queue and average wait. Switch departments or try staff + / - and rerun.
3. **Demand** compares ordinary and event weeks. Use day and volume filters; expand the scenario comparison for all three event levels.
4. **Staffing** shows each department's current positions, peak requirement and extra positions needed. Edit counts or expand service-time settings.
5. **Compare Plans** shows cost and waiting-time trade-offs from the queue engine. Department detail and model explanations are expandable.
6. **Shifts & Stress** combines the incoming shift planner and disruption test. Set call-outs, extra arrivals and service delays; expand shift/rest/break rules if needed. Click **Build & Test Roster**. Compare ordinary/event roster coverage and costs, then expand the day-filtered shifts or department gaps.
7. **Review & Approve** supports either coverage-plan review (`/api/decisions`) or event-roster review (`/api/staffing-decisions`). Changed settings require rebuilding before roster approval. Decisions and exports remain local; no workers are contacted.

The interface is English-only. Source details, assumptions, forecast scores and the optional workflow guide remain available without filling the default screen. The floor still replays the queue simulation using continuous staff positions. Shift-stress metrics are a separate capacity calculation, not a replay of waits under shift breaks. Worker availability is assumed and IDs are fictional.

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

- [frontend/src/main.tsx](frontend/src/main.tsx) — pages, controls, charts, and manager review.
- [frontend/src/DepartmentView.tsx](frontend/src/DepartmentView.tsx) — animated request and staff-seat replay.
- [backend/main.py](backend/main.py) — API for simulations, replay, staffing plans, and manager decisions.
- [backend/model.py](backend/model.py) — demand, staffing needs, and waiting-line simulation.
- [backend/scheduling.py](backend/scheduling.py) — synthetic shift roster, break capacity, rest/hour limits, and disruption comparison.
- [backend/training.py](backend/training.py) — train and measure the demo forecast model.
- [backend/data](backend/data) — synthetic input files and trained model.
- [backend/tests](backend/tests) — automated checks.

## API summary

- `POST /api/simulate` — runs the selected demand case and returns the hourly forecast, ordinary-week comparison profile, staffing requirements, plan metrics, provenance, and synthetic holdout report when the trained model is selected.
- `GET /api/scenario-summary` — accepts `multiplier`, `forecast_mode`, `proxy_scale`, and JSON `service_minutes` query parameters; returns ordinary-week totals plus low/medium/high event-week totals, peak activity, and peak concurrent seats by department.
- `POST /api/replay` — returns the seeded request trace for a selected staffing option.
- `POST /api/staffing-plan` — accepts the simulation inputs plus shift length, break minutes, weekly hour cap, rest gap, and disruption settings; builds baseline/event rosters and evaluates both under the same call-outs, arrival surge, and service delay.
- `POST /api/staffing-decisions` — recomputes and saves manager approval or rejection for a staffing roster.
- `POST /api/decisions` — stores a manager's approve/reject decision locally for a simulation snapshot.

Interactive request and response schemas are available at `http://127.0.0.1:8000/docs` while the backend is running.

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
