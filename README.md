# Apron · FBO Staffing Lab

## Windows desktop application

The application can run in its own native Windows window using pywebview and Edge WebView2, with the same React interface and Python simulation engine. No browser tab, public hosting or separate backend terminal is needed. The UI uses embedded web technology; this is a desktop wrapper rather than a rewrite using native widgets.

Install and build once from the project root:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-desktop.txt
cd frontend
npm.cmd install
npm.cmd run build
cd ..
.\.venv\Scripts\python desktop.py
```

Then double-click `Start Apron.cmd` to launch from source. To make a distributable program:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-desktop.ps1
```

Open `dist\ApronStaffingLab\ApronStaffingLab.exe`. Distribute the **entire ApronStaffingLab directory**, not just the exe. Python and Node are not required on the destination computer; Microsoft Edge WebView2 Runtime is required. The loopback-only simulation server starts with the window and stops when it closes. Approved decisions are stored in `%LOCALAPPDATA%\ApronStaffingLab\decisions.sqlite`; startup errors are logged in the same directory. Initial packaging is unsigned.

Local hackathon MVP for demand, workload, staffing and human-reviewed decisions. **AI assists. People decide.** All supplied data is synthetic. Includes a fitted regression demonstration; no real FBO observations or real-world validation are included.

## Department replay and fitted forecasting

The desktop opens on **Department View**: use left/right arrows for Passenger Services, Ramp Operations and Fuel Services. The floor plan is an illustrative schematic inspired by the supplied sketch. Blue circles are qualified resource seats; orange circles/aircraft are waiting requests; green circles/aircraft are in service. Dots appear, change state and disappear according to the exact same SimPy event records used for comparison metrics. Geometry and walking/travel are not simulated. At most 120 queued icons are rendered, with the full queue count always shown.

Use Play/Pause, speed, Reset and the time slider. The timeline includes post-week queue drain. Each seat has a busy progress indicator. Current-hour expected demand, actual waiting/in-service/completed counts and completed-request mean wait are computed from results. Staff −/+ prepares a Manager Plan; **Run simulation** applies the change. Baseline and trained forecasts can be selected in the toolbar; selected option changes affect replay too.

Run `python -m backend.training` to generate 180 days / 4,320 hourly synthetic records and fit multi-output ridge regression with eight explicit calendar/event features using NumPy. Targets are aircraft, passengers and fuel requests. CSV columns and numeric/provenance constraints are inspected before fitting. Rows are split chronologically: first 3,456 for training, final 864 held out. Evaluation reports MAE/RMSE and a training-only hour-of-day mean baseline. After evaluation, coefficients are refit on all history and saved as portable JSON. Holdout scores refer to the pre-refit evaluation model, not the refitted model.

Files: `backend/data/synthetic_training_history.csv` and `backend/data/trained_forecast.json`. The JSON contains coefficients, feature names, provenance, split dates and metrics. The Demand Forecast screen displays these metrics. No pickle or executable model is loaded. The desktop bundle includes the JSON model. Packaging preserves an existing fitted artifact; it trains a synthetic demo only if none exists.

To train on a later inspected dataset: `python -m backend.training --csv PATH`. Required columns are `timestamp,hour,weekday,event_index,aircraft,passengers,fuel_requests,provenance`, at least 60 days of unique records. Hour is 0–23, weekday is 0–6 (Monday first), and event_index is a documented nonnegative intensity indicator known at prediction time. Prepare/aggregate external files into this schema first; do not fabricate missing real labels. Event multipliers and the displayed week remain hypothetical. The app always warns that forecasting is not real-world validated, including when external history is used.

**Synthetic holdout performance is not evidence of real FBO forecasting accuracy.** The generator deliberately contains predictable daily/event structure. Dataset truthfulness and event-feature availability require review for real use. There is no trained staffing optimizer: fitted demand feeds transparent workload thresholds, then actual queue simulation and human review.

## Run in VS Code (Windows PowerShell)

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.txt
.\.venv\Scripts\python -m backend.model
.\.venv\Scripts\python -m uvicorn backend.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs. Keep both terminals running. Vite proxies `/api` to FastAPI; no separate CORS setup is needed. Nothing is deployed.

`backend/requirements-lock.txt` records the exact Python environment used during verification. Use `pip install -r backend/requirements-lock.txt` for that environment, and `npm.cmd ci` after the initial install to reproduce the frontend lockfile.

## Architecture and minimum scope

- `backend/model.py`: reproducible hourly planning baseline, department workload, seat thresholds, common seeded service requests, and SimPy FIFO queues.
- `backend/main.py`: validated simulation API and explicit approve/reject decisions saved in SQLite. Backend recomputes the selected plan rather than trusting client metrics.
- `backend/import_data.py`: inspects and validates the CSV schema for future real-data work.
- `frontend/src`: React + TypeScript + Tailwind + Recharts, six dashboard views, editable staffing/durations/demand, comparison and decision export.
- `backend/data`: generated demand, employee skills/availability/wages, and service-request CSVs. Decision database is created only on review.

The first MVP covers all seven days with **constant concurrent qualified seats**, while showing hourly seat requirements. Options use median, 85th percentile and peak requirements. They are heuristic candidates, not optimized rosters. A manager can enter a fourth candidate and compare it using the same requests.

## Model and assumptions

Passenger Services uses passenger requests (5 minutes each), Ramp uses aircraft tasks (24 minutes), Fuel uses fueling requests (30 minutes). Baseline expected passengers use 4.5 per aircraft and fuel requests 65% of aircraft. For trained demand, per-aircraft passenger Poisson means and fueling probabilities are computed from predicted hourly passenger/aircraft and fuel/aircraft ratios (fuel probability capped at one). Aircraft follow independent hourly Poisson arrivals, uniform within each hour. Each job occupies one qualified seat. Ramp has two concurrent seats minimum; the other departments have one. **These are demo assumptions, not verified mandatory safety standards.** No task requires a multi-person crew in this MVP.

Workload minutes = expected requests × mean service minutes. Seats = max(minimum, ceil(workload / (60 × 0.8))). The next seat is needed when demand exceeds seats × 60 × 0.8 / mean service minutes. The 80% utilization threshold supplies capacity headroom; it does not guarantee a wait target. Simulation measures the fraction starting within ten minutes separately.

Triangular service-time multiplier (0.6, 1.0, 1.4) has mean one. All options receive identical requests and durations using seed 42 by default. Queues are independent by department. No abandonment, travel, equipment, aircraft-task precedence, fueling hazards, breaks, absenteeism or disruptions are modeled. Mean wait is over all service requests, not distinct customers. Queues drain after week end to measure waits; unfinished-at-close counts completions after 10,080 minutes. Utilization counts busy time inside the planning horizon only. Cost covers 168 hours per seat and excludes post-close overtime, benefits and equipment.

Synthetic employees have department qualifications and 40 available weekly hours. The simulator **does not assign or validate individual employees against those availability records**. Its resource pools assume all allocated seats are qualified. A real deployment requires an availability-aware shift solver, credential verification, multi-person task constraints and validated site-specific rules before any plan is considered operationally feasible. No option is represented as certified safe.

## Data provenance and importing later

Generation: `python -m backend.model`. CSVs contain explicit provenance. Generated files are actual simulation inputs/profile samples, not observed data. Inspect columns with `python -m backend.import_data backend/data/synthetic_hourly_demand.csv`. The validator requires 168 hourly rows with `hour, aircraft, passengers, fuel_requests, provenance` and validates values before use. To simulate a validated external profile in Python, pass `validate(path).to_dict('records')` to `requirements` and `requests`, then reuse the resulting requests across `simulate` calls. The dashboard can use the synthetic planning baseline or predictions from the fitted synthetic-history regression.

No public datasets have been downloaded or inspected. FAA ATADS and OpenSky are possible aircraft-demand sources; ground-handling data could inform task duration assumptions; scheduling benchmarks could validate a future roster solver. They must be inspected for schema, license, coverage and fitness before use. No claims about their actual contents are made. FBO passenger and employee records remain synthetic until an appropriate source is supplied. The included regression has chronological holdout scores on synthetic history only; no real-world accuracy is claimed.

## Validation

```powershell
.\.venv\Scripts\python -m pytest backend/tests -q
cd frontend
npm.cmd run build
```

Tests cover a staffing threshold boundary, independent department drivers, exact queue waits, repeatability, candidate cost/wait ordering, demand spikes, closing backlog, validation and persisted approval. These verify model behavior, not real operational accuracy.

## Three-minute demonstration

1. Overview: explain synthetic demand and the human approval principle (30 seconds).
2. Forecast and requirements: show the seven-day peaks and the threshold formula (40 seconds).
3. Comparison: contrast cost, delay and service level using identical arrivals (40 seconds).
4. Simulation: increase demand or change manager staffing and rerun (40 seconds).
5. Approval: select a plan, enter a manager name, approve locally and export the decision snapshot (30 seconds).

Next work: real-data adapters and real-world held-out evaluation, named shift feasibility with OR-Tools, hourly capacity changes, disruptions and replicated simulation confidence intervals. Keep these separate from claims supported by the current MVP.
