# Task-level operations provider

The Next.js command center currently uses `demoOperations`, a deterministic in-browser provider. It is not connected to the existing weekly FastAPI planner. The interfaces in `frontend/src/lib/operations-api.ts` define the seam for that later integration.

## Requests and responses

- `MissionRequest`: ordinary/event week, low/medium/high case, selected day 0–6, fixed seed, optional complete hourly count upload.
- `MissionResponse`: synthetic mission (aircraft, tasks, qualified workers, shifts, breaks), original assignment results, provenance and algorithm label.
- `CrisisRequest`: the original mission and original assignment plan plus unexpected arrival count, specific absent worker IDs, arrival-delay minutes, and number of upcoming flights to delay.
- `CrisisResponse`: changed aircraft/task demand and feasibility of the **unchanged original** assignments.
- `recover`: candidate assignments for the same affected task set and workforce. Completed and feasible in-progress work is retained.

A later HTTP adapter can implement these methods, with equivalent validated request/response schemas, behind endpoints such as `/api/operations/mission`, `/api/operations/crisis`, and `/api/operations/recovery`. These endpoints are **proposed, not implemented**. Never silently interpret a network failure as a real operational result. The current interface always labels the local simulation.

## Domain constraints

Workers have one team qualification, a shift interval, a break interval, and an illustrative hourly wage. Tasks have a synthetic aircraft reference, required qualification/team, earliest start, finish deadline, duration, and simultaneous worker count. Assignments must satisfy all these constraints and cannot overlap on the same worker.

Call-outs begin at the mission clock, 14:00. Arrival delays move the next three expected arrivals and their task windows. Extra aircraft create additional tasks. Original assignments that no longer fit are explicitly uncovered; no hidden recovery occurs when crisis is triggered.

Recovery uses five-minute start increments and an earliest-deadline greedy heuristic. It does not guarantee a global optimum. Uncovered tasks, unchanged coverage, or worse results must remain visible.

## Metrics

- Tasks covered/uncovered are counts calculated from feasible assignments.
- Required-work coverage is covered worker-minutes divided by required worker-minutes, weighted by task duration and required crew count.
- Uncovered worker-hours are uncovered required crew-minutes / 60.
- Allocated labor cost uses the same rostered shift hours and wage assumptions for original and candidate; paid breaks included. No labor savings are invented from reordering tasks or worker call-outs.
- Impact Report compares selected-day replays under ordinary and event demand profiles. It is not a seven-day constrained employee schedule.

## Review and provenance

Manager approval/rejection is a browser-local planning record and downloadable JSON. It never dispatches employees. Uploaded files contain aggregate counts only; generated task/worker identities remain synthetic. No real forecast accuracy or observed FBO savings are claimed for the task replay. The existing weekly API contract and synthetic holdout metrics are documented separately in `docs/API_CONTRACT.md`.
