# CrewPilot AI — Aviation operations command center

An aviation-focused staffing demo with light and dark modes for **The Intelligent FBO** track. Built with **Next.js App Router, TypeScript, Tailwind CSS, official shadcn/ui components, and Recharts**.

Use the **Light mode / Dark mode** switch in the top bar to change appearance. Light mode is the readable default for new visitors. Your choice is saved in this browser and restored before the page paints. Both modes cover charts, task timelines, warnings, dialogs, and reports. Light-mode body text, muted labels, and status palettes are checked against 4.5:1 contrast.

## Start the website

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open **http://127.0.0.1:5173**. Keep the terminal open. Node 20.9+ is required by Next.js; tests were run with Node 24. The default task-level demo runs locally in the browser; it does not require FastAPI or an external data service.

## Core demo

1. **Mission Control:** inspect aircraft demand, qualified crew capacity, risk, service activity, and the task timeline. Use the mission-day selector and ordinary/Super Bowl demand profiles.
2. **Crisis Mode:** choose unexpected aircraft, specific synthetic crew absences, and arrival delays. Click **Trigger disruption**. Original assignments remain fixed; newly infeasible services become explicit conflicts.
3. **Recovery Planner:** click **Calculate recovery candidate**. Inspect reassigned workers/times, explanations, remaining uncovered work, and unchanged allocated labor cost. Approve or reject a local draft and download the decision record.
4. **Workforce Timeline:** filter teams and click aircraft task blocks or uncovered-task entries for deadlines, required qualification, crew count, and feasibility explanations.
5. **Impact Report:** compare original and candidate outcomes under ordinary-week and event-week demand profiles. Values are calculated for the selected-day replay, not baked-in improvement claims.

The top mission clock is 14:00 PST in an illustrative 8–14 February 2027 window. Nothing is live airport telemetry. Workers, aircraft identities, tasks, service rules, and disruptions are synthetic. The date window is a product choice, not an organizer-prescribed date range.

## What the model calculates

The pure TypeScript engine generates deterministic demand with a fixed seed. Tasks require a specific team qualification, earliest start, finish deadline, duration, and simultaneous crew count. Feasible assignments must fit shift and break windows and cannot overlap on the same worker.

Crisis Mode adds service tasks for unexpected aircraft, makes selected workers unavailable from 14:00, and shifts the next three expected arrivals and task windows by the chosen delay. It first evaluates the original plan without silently reassigning work.

Recovery runs an earliest-deadline greedy heuristic with five-minute start increments. Feasible in-progress and completed tasks are retained. It does not establish a global optimum. Remaining uncovered work, zero improvement, or worse outcomes must be shown honestly.

- **Required-work coverage:** covered crew-minutes divided by required crew-minutes, weighted by duration and required worker count.
- **Uncovered tasks:** tasks without a full feasible crew assignment before the deadline.
- **Uncovered worker-hours:** required crew-minutes for uncovered tasks / 60.
- **Allocated labor cost:** same rostered paid shift hours and illustrative wages for original and candidate. Reordering work does not magically reduce labor cost.
- **Risk label:** a demo rule based on uncovered task share: none = low; up to 15% = watch; above 15% = high.

This selected-day replay does **not** evaluate full-week labor/rest rules, actual queue waits, or real forecast accuracy. Those are separate from the existing Python weekly planning model. Task durations and workforce rules need validation with an FBO expert.

## Data and optional upload

Open **Data & assumptions** to inspect provenance and modeled rules. CSV can replace the ordinary-week aggregate demand profile. Download a synthetic sample from the dialog.

Required headers: `hour,aircraft,passengers,fuel_requests`. Exactly 168 rows, one for each hour 0–167 of Monday–Sunday. Counts must be finite and nonnegative. Extra identity columns, missing hours, duplicate hours, malformed numeric values, and files over 100 KB are rejected. The selected-day task replay supports up to 80 aircraft in the eight-hour arrival window; larger profiles are rejected with an explanation.

Uploaded counts are not independently verified. Aircraft tasks, fictional worker identities, qualifications, task durations, and workforce remain synthetic assumptions. Uploading a week does not train or validate a forecast. The original CSV is not saved. Counts remain in browser memory until reset/refresh. Browser-local decision records include the generated mission snapshot, source metadata, assignments, assumptions implicit in the tasks/workers, and calculated metrics.

Manager approval never dispatches employees or authorizes aircraft movement. No real passenger identities are used. Fuel service means staffing work, not fuel loading or inventory planning.

## Checks and production build

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```

Next.js exports the website to `frontend/out`, then copies it to `frontend/dist` for compatibility with the existing desktop packager. No network font download is needed. Recharts animations are disabled and CSS respects reduced motion. Warnings use text and icons as well as color. shadcn/ui dialogs, sliders, tabs, tooltips, and buttons provide keyboard-accessible primitives.

A manual browser walkthrough was blocked by Computer Use's inability to verify the current Chrome URL in this session. Build, deterministic engine, API, and HTTP checks do not substitute for a completed visual/mobile walkthrough.

## Existing FastAPI weekly planner

The Python engine is retained separately, including synthetic holdout metrics, ordinary/event weekly rosters, configurable break/rest/weekly constraints, validated aggregate uploads, stress tests, and SQLite review records.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Schemas: http://127.0.0.1:8000/docs. Backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

The command center currently uses `demoOperations`; it does not claim that the weekly endpoints power the task-level dashboard. The request/response DTOs and async integration interface are in `frontend/src/lib/operations-api.ts`. Proposed task-level endpoints are documented in `docs/OPERATIONS_API_CONTRACT.md`; they are not implemented yet. Existing weekly endpoints are documented in `docs/API_CONTRACT.md`.

For the optional Windows desktop package, install `requirements-desktop.txt` and run `build-desktop.ps1`. Rebuild any old executable to include the Next.js export. Existing storage and executable names remain `ApronStaffingLab` for compatibility.

## Architecture

- `frontend/src/app` — Next.js layout, page, design tokens, responsive dark styles.
- `frontend/src/components/operations/command-center.tsx` — Mission Control, Crisis Mode and shared timeline/review/report views.
- `frontend/src/components/ui` — official shadcn/ui components, locally owned and themed.
- `frontend/src/lib/operations.ts` — pure synthetic data, constraints, fixed-plan evaluation, recovery, metrics, explanations.
- `frontend/src/lib/operations-api.ts` — typed demo and future HTTP integration boundary.
- `frontend/src/demand-csv.ts` — aggregate CSV validation, sample, exports.
- `backend` — retained weekly staffing API and tests.
- `docs/COMMAND_CENTER_PLAN.md` — architecture, alternatives, build phases, guardrails.
- `docs/ASSUMPTIONS.md` and `DATA_SOURCES.md` — evidence and assumptions.
- `docs/DEMO_SCRIPT.md` — judge walkthrough.
