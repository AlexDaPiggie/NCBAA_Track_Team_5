# CrewPilot AI MVP plan

Current frontend direction: the user's dark aviation command center, documented in `docs/COMMAND_CENTER_PLAN.md`. Mission Control and Crisis Mode are the first delivery priority. The selected-day task provider and the retained weekly Python planner are distinct models; see their separate API contracts. The guided light-site notes below describe the preceding implementation phase.

## Decision

Implement the event-week staffing stress tester in the existing repository stack where feasible. Optimize for a complete, inspectable demo; do not add unrelated FBO functions. All outputs remain manager-reviewed drafts.

## Selected-day replay: extend to 24 hours

### Decision

Use a 00:00–24:00 mission and demand/capacity chart. Staff it with synthetic fixed shifts: 00:00–08:00, 08:00–16:00, and 16:00–24:00. Each worker stays on one shift, leaving 16 hours between daily shifts. Let service tasks finish through 02:00 next day so late arrivals can meet their modeled service deadlines. The adjustable 15-minute simulation clock defaults to 14:00. This is a daily replay, not a rotating seven-day employee roster.

### Work breakdown

1. Extend the deterministic synthetic arrival generator and uploaded-demand filter to all 24 hours; retain the 80-aircraft safety cap and update its error text.
2. Create qualified workers for each of the three fixed shifts, with staggered breaks. Make worker availability repeat by day so overnight tail tasks can use the next 00:00 shift.
3. Extend demand/capacity samples and both task-timeline views; show the next-day service tail clearly.
4. Spread proposed hires across shift groups. Update assumptions, CSV guidance, demo steps, and API notes.
5. Update deterministic model fixtures and automated checks for all-day demand, shift coverage, overnight task windows, and 16-hour daily rest.

### Risks and limits

This does not model shift rotation, week-to-week availability, overtime, or local labor law. The traffic curve, shift sizes, break timing, and 16-hour rest are synthetic assumptions. The 24-hour window improves coverage completeness; it does not establish real VNY demand or operating policy.

## Implementation choice

The current app uses React, TypeScript, and Vite for the website, with FastAPI/Python for local APIs and the simulation model. Keep this stack for the hackathon; a framework migration adds risk without helping the staffing demo.

## Current website scope

The redesigned website uses four guided steps: Demand, Staffing plan, Stress test, Review. It opens with a ready synthetic demo and supports an optional validated ordinary-week CSV. The interface uses one light aviation design and plain-language explanations. See `docs/WEBSITE_REDESIGN_PLAN.md`.

- Shows ordinary-week demand against low, medium, and high synthetic event-week cases.
- Shows a chronological synthetic holdout forecast score beside a simple baseline; this is not real FBO accuracy.
- Compares coverage policies using the same seeded service requests, with cost, wait, and delay metrics.
- Builds ordinary-week and event-week worker rosters with synthetic IDs, shifts, staggered breaks, minimum rest, and maximum weekly hours.
- Stress-tests both rosters against the same arrival surge, service delay, and synthetic call-outs; reports uncovered seat-hours and any unfilled roster slots.
- Explains synthetic assumptions and uncertainty and keeps manager approval as the decision gate.
- Links to public airport-traffic context and documents VNY source figures in the research notes, separately from FBO demand.
- Event factors, task times, illustrative wages, shift rules, disruptions, and worker pool size are editable. Defaults are synthetic assumptions.
- Employee availability is assumed; qualifications and labor settings are unverified. This is not a real employee schedule or operational dispatch tool.

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
