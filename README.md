# Apron · FBO Staffing Lab

Apron is a local demo for planning staff at an FBO. An FBO is a business at an airport that serves private and general aviation aircraft.

The app estimates hourly work, compares staffing plans, and simulates waiting requests. A manager reviews any plan. The app does not assign real employees or control aircraft.

## What you can try

1. Choose low, medium, or high demand for the seven-day planning window.
2. See expected work by hour and the number of staff seats each department may need.
3. Change service times or staff counts, then run the simulation again.
4. Compare plans using the same simulated requests. See labor cost, waiting time, and unfinished work.
5. Watch a replay: service requests arrive, wait for staff, then get served.
6. Approve or reject a plan. The app saves that choice on this computer.

Departments in this demo: Passenger Services, Ramp Operations, and Fuel Services. This is a **staffing** project. “Fuel Services” means planning staff for fuel requests. It does not plan how much fuel to load.

## Data and limits

All included demand, workers, and service requests are synthetic. The forecast model is trained and checked on synthetic data too. Demo accuracy scores do not show real-world accuracy.

Service times, wages, staffing minimums, passenger counts, and demand levels are assumptions. They are not verified FBO rules or Super Bowl forecasts. The simulation does not model breaks, fatigue, staff absences, travel between tasks, or aircraft-task safety rules. Ask an FBO expert to review assumptions before treating results as realistic.

## Run on Windows

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
