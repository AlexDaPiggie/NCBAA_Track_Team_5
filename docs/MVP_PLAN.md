# CrewPilot AI MVP plan

## Decision

Implement the event-week staffing stress tester in the existing repository stack where feasible. Optimize for a complete, inspectable demo; do not add unrelated FBO functions. All outputs remain manager-reviewed drafts.

## Implementation choice

The current app uses React, TypeScript, and Vite for the website, with FastAPI/Python for local APIs and the simulation model. Keep this stack for the hackathon; a framework migration adds risk without helping the staffing demo.

## Current website scope

- Shows ordinary-week demand against low, medium, and high synthetic event-week cases.
- Shows a chronological synthetic holdout forecast score beside a simple baseline; this is not real FBO accuracy.
- Compares coverage policies using the same seeded service requests, with cost, wait, and delay metrics.
- Builds ordinary-week and event-week worker rosters with synthetic IDs, shifts, staggered breaks, minimum rest, and maximum weekly hours.
- Stress-tests both rosters against the same arrival surge, service delay, and synthetic call-outs; reports uncovered seat-hours and any unfilled roster slots.
- Explains synthetic assumptions and uncertainty and keeps manager approval as the decision gate.
- Employee availability is assumed; the 30-worker-per-department pool, qualifications, and labor settings are synthetic. This is not a real employee schedule or operational dispatch tool.

## 48-hour plan

### Phase 0 — decisions and assumptions (complete before code)

- Read organizer slides and record scope, unknowns, and guardrails.
- Compare at least three staffing product options and select one.
- Freeze a synthetic scenario schema, metrics, and demo narrative.

### Phase 1 — deterministic data and core model (hours 0–8)

- Inspect the repository and retain its working stack unless there is a concrete blocker.
- Create fixed-seed synthetic ordinary-week and event-week hourly arrival/task fixtures for seven days.
- Model roles/skills, employee availability, shifts, breaks, max hours, minimum rest, and service-task workload as configurable assumptions.
- Implement a transparent baseline and a constrained proposed schedule. No hard-coded output tables.
- Acceptance: same input/seed yields same result; constraints and infeasibility are explicit.

### Phase 2 — scenarios and evaluation (hours 8–16)

- Provide low/medium/high demand with explicit multipliers or quantiles.
- Add disruption controls for arrival surge, service delay, and absences.
- Evaluate baseline and proposed schedules under identical demand/disruptions.
- Report coverage / uncovered task-hours, labor hours, overtime, estimated cost only when configured, and schedule changes.
- Hold out a deterministic synthetic test week for forecast MAE or WAPE; label it synthetic validation only.
- Acceptance: tests cover constraint validity, deterministic results, and scenario fairness.

### Phase 3 — API/UI workflow (hours 16–32)

- Follow repository conventions; preferred target is Next.js/TypeScript and FastAPI/Python if setup supports it.
- Build a staffing dashboard: ordinary/event view, scenario selector, shift/role coverage, disruption controls, comparisons, explanation, and approval state.
- Expose typed API contracts; keep optimization and metrics on backend if backend exists.
- Acceptance: one command or documented local steps launch a complete end-to-end flow.

### Phase 4 — hardening and demo (hours 32–48)

- Test the full manager workflow and explain failures/infeasible scenarios.
- Update README, API contracts, tests, assumptions and pitch notes.
- Rehearse three-minute version as a practical default, while noting the organizer deck’s explicit 3-minute pitch requirement is for Track 2 only; Track 1 timing is unknown.
- Get mentor feedback on realism; adjust only configurable assumptions, not claim them as rules.

## Proposed task breakdown

1. Repository and environment reconnaissance.
2. Synthetic schema and reproducible fixtures.
3. Demand forecast and held-out metric.
4. Staffing baseline and constrained recommendation.
5. Disruption engine and fair comparative metrics.
6. API contracts and approval-state handling.
7. UI, README, and demo/pitch materials.

## Definition of done

- One staffing-only end-to-end workflow works locally.
- Ordinary and event weeks, three demand scenarios, and a disruption are demonstrable.
- Baseline and recommendation face identical scenario inputs.
- Metrics are calculated from schedules, not fabricated.
- Deterministic tests cover key constraints and fair comparison.
- Synthetic data and unverified assumptions are visibly labeled.
- Manager approval is required; no automatic dispatch or sensitive passenger information.
