# Task-level operations provider

The Next.js command center currently uses `demoOperations`, a deterministic in-browser provider. It is not connected to the existing weekly FastAPI planner. The interfaces in `frontend/src/lib/operations-api.ts` define the seam for that later integration.

## Browser weekly proposal reporting

The separate browser seven-day planner exposes `WeeklyMetrics.slots`: one evaluated coverage record per day, 8-hour shift, and role (63 records). Each carries required, covered, and uncovered staff-hours from the same hourly evaluation used by weekly totals. `buildWeeklyReview` joins these records with actual baseline/proposed roster assignments to report scheduled positions, peak required positions, wage costs, proposed workers/breaks, and net staffing changes. This reporting does not alter roster generation or use a FastAPI endpoint. Additions and reductions, costs, daily shortages, and unique roster worker counts are checked against weekly summaries.

## Requests and responses

- `MissionRequest`: ordinary/event week, low/medium/high case, selected day 0–6, fixed seed, optional complete hourly count upload.
- `MissionResponse`: synthetic mission (aircraft, tasks, qualified workers, shifts, breaks), original assignment results, provenance and algorithm label.
- `CrisisRequest`: the original mission and original assignment plan plus unexpected arrival count, specific absent worker IDs, arrival-delay minutes, and number of upcoming flights to delay.
- `CrisisResponse`: changed aircraft/task demand and feasibility of the **unchanged original** assignments.
- `recover`: candidate assignments for the same affected task set. The Recovery Planner can add hypothetical role-qualified workers to the candidate roster; the unchanged original keeps the actual selected roster. Completed and feasible in-progress work is retained.
- `recommendRecoveryHeadcount`: browser-only bounded search over 0–20 proposed workers per role. It is not part of the HTTP provider interface or a global optimizer.

A later HTTP adapter can implement these methods, with equivalent validated request/response schemas, behind endpoints such as `/api/operations/mission`, `/api/operations/crisis`, and `/api/operations/recovery`. These endpoints are **proposed, not implemented**. Never silently interpret a network failure as a real operational result. The current interface always labels the local simulation.

## Domain constraints

Workers have one team qualification, a fixed repeating eight-hour shift, a staggered break, and an illustrative hourly wage. The demo uses 00:00–08:00, 08:00–16:00, and 16:00–24:00 shifts; fixed daily shifts leave 16 hours off. Arrivals cover the selected 00:00–24:00 day. Late tasks may finish through 02:00 the next day. Tasks have a synthetic aircraft reference, required qualification/team, earliest start, finish deadline, duration, and simultaneous worker count. Assignments must satisfy all these constraints and cannot overlap on the same worker.

Call-outs begin at the mission clock, 14:00. Arrival delays move the next three expected arrivals and their task windows. Extra aircraft create additional tasks. Original assignments that no longer fit are explicitly uncovered; no hidden recovery occurs when crisis is triggered.

Recovery uses five-minute start increments and an earliest-deadline greedy heuristic. It does not guarantee a global optimum. Uncovered tasks, unchanged coverage, or worse results must remain visible.

## Metrics

- Tasks covered/uncovered are counts calculated from feasible assignments.
- Required-work coverage is covered worker-minutes divided by required worker-minutes, weighted by task duration and required crew count.
- Uncovered worker-hours are uncovered required crew-minutes / 60.
- Allocated labor cost uses rostered shift hours and illustrative wage assumptions; paid breaks included. Without proposed workers, task reordering does not change cost. Proposed workers add their full paid-shift cost to the candidate only. The weekly estimate repeats that selected shift seven times.

## Review and provenance

Manager approval/rejection is a browser-local planning record and downloadable JSON. Recovery review records include proposed headcounts, added shift and seven-day estimated cost, and the candidate worker snapshot. A changed headcount or disruption clears the prior decision. It never hires or dispatches employees. Uploaded files contain aggregate counts only; generated task/worker identities remain synthetic. No real forecast accuracy or observed FBO savings are claimed for the task replay. The existing weekly API contract and synthetic holdout metrics are documented separately in `docs/API_CONTRACT.md`.
