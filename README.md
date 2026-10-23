# Apron · FBO Staffing Lab

Apron is a local demo for planning staff at an FBO. An FBO is a business at an airport that serves private and general aviation aircraft.
## Latest: real flight patterns and clearer English interface

The application now defaults to a fitted **real-data aircraft-activity proxy** using observed 2013 JFK airline departures from nycflights13. It does not present those departures as FBO arrivals. Passenger/fuel ratios, FBO scaling and service assumptions remain explicit. See [DATA_SOURCES.md](DATA_SOURCES.md) for the source, downloaded schema, cleaning audit, training split and exact held-out results. The fitted model has similar error to the simple baseline and does not outperform it.

The UI remains English only. Menus use simpler names (Live Floor, Try a Plan, Compare Plans); text and metrics are larger; technical settings, formulas and detailed scores are collapsible. The floor focuses on department staff and queue information instead of also showing a second row of weekly totals.

Reproduce real-data training: `python -m backend.real_training --download`. The model, hourly aggregate and holdout predictions are included in source; the large raw CSV is not. Both synthetic modes remain available separately. The sections below explain setup and the shared simulation assumptions.


The app estimates hourly work, compares staffing plans, and simulates waiting requests. A manager reviews any plan. The app does not assign real employees or control aircraft.

## How to use the website

1. Start the backend and website using the steps below.
2. At the top, choose **Quiet**, **Normal**, or **Busy** demand. Click **Run Simulation**.
3. Choose **Demand** to view the 7-day demand pattern and data source. Choose **Staffing** to see how many staff seats may be needed each hour.
4. Choose **Live Floor** to watch sample service requests arrive, wait, and get served. Use **+ / −** to change the number of staff seats.
5. Choose **Try a Plan** to change staff seats or service times. Click **Apply Changes & Run** to update results.
6. Choose **Compare Plans** to compare cost, wait time, and unfinished work. Apron uses the same sample requests for each plan.
7. Choose **Review & Approve** to enter a manager name and notes, then approve or reject the plan. The decision is saved on this computer.

**More settings** has a random seed and demand scaling controls. Use the same seed to repeat a comparison. A staff seat means one qualified worker available at a time; the app does not assign named employees to shifts.

Departments in this demo: Passenger Services, Ramp Operations, and Fuel Services. This is a **staffing** project. “Fuel Services” means planning staff for fuel requests. It does not plan how much fuel to load.

## Data and limits

The default aircraft activity model uses observed 2013 JFK airline departures. This is a proxy, not FBO arrival data. Passenger counts, fuel demand, workers and service requests remain assumptions or synthetic. The synthetic-only models are available separately. Neither mode has been validated for real FBO operations.

Service times, wages, staffing minimums, passenger counts, and demand levels are assumptions. They are not verified FBO rules or Super Bowl forecasts. The simulation does not model breaks, fatigue, staff absences, travel between tasks, or aircraft-task safety rules. Ask an FBO expert to review assumptions before treating results as realistic.

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
- [backend/main.py](backend/main.py) — API for simulations, replay, and saved decisions.
- [backend/model.py](backend/model.py) — demand, staffing needs, and waiting-line simulation.
- [backend/training.py](backend/training.py) — train and measure the demo forecast model.
- [backend/data](backend/data) — synthetic input files and trained model.
- [backend/tests](backend/tests) — automated checks.

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
