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

#### Phase 3 implementation status

- Implemented in the existing React, TypeScript, Vite, and FastAPI stack. The app entry now mounts the current six-page staffing workflow from `frontend/src/App.tsx`.
- The dashboard connects demand/scenario controls, hourly staffing needs, queue-plan comparisons, roster stress testing, and local manager approval to backend endpoints. Typed frontend payloads are in `frontend/src/plannerTypes.ts`.
- `/api/staffing-plan` calculates baseline and event rosters using the same selected scenario and disruption inputs. `/api/staffing-decisions` records a manager's approve/reject decision locally. `/api/schedule` remains available for the legacy synthetic shift assignment.
- The API and frontend entry merge conflicts were resolved so the app can import and launch. README run steps and endpoint notes now match the active UI.
- Verification: `npm run build` in `frontend/` passes. Backend integration tests were not run in this environment because the `python` command is unavailable; rerun them from the configured project virtual environment during Phase 4.

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

## Stage 2 audit work — four-hour demand blocks

The Stage 2 build step is additive: retain the existing 168 hourly series for current screens and queue simulation, and also expose 42 ordered four-hour blocks for the seven-day staffing plan. Each block sums aircraft, passenger, and fuel-request demand from its four source hours. Block staffing requirements use total workload divided by four hours of assumed per-person capacity, subject to the existing department minimum. Because aggregation removes within-block peaks, hourly requirements remain available and must be used wherever peak timing matters. The new block output follows the same synthetic/trained/JFK-proxy provenance as the hourly input; it does not turn the JFK proxy into LAX or FBO data.

Task breakdown:

1. Add strict validation for a complete ordered 168-hour week before aggregation.
2. Derive day, block index, start/end hour, provenance, and additive demand totals.
3. Calculate staffing requirements from four-hour capacity without changing hourly calculations.
4. Return ordinary and event block profiles and staffing requirements from the existing model/API response.
5. Add a reproducible four-hour CSV output to the existing data generator.

The current `main.py` merge conflict is unresolved, so this stage does not alter its routes. The existing simulation route already returns the model result object; its new fields are additive. UI consumption and exact 42-cell screen behavior remain later work.

## Definition of done

- One staffing-only end-to-end workflow works locally.
- Ordinary and event weeks, three demand scenarios, and a disruption are demonstrable.
- Baseline and recommendation face identical scenario inputs.
- Metrics are calculated from schedules, not fabricated.
- Deterministic tests cover key constraints and fair comparison.
- Synthetic data and unverified assumptions are visibly labeled.
- Manager approval is required; no automatic dispatch or sensitive passenger information.

## Stage 5 — six-screen workflow integration

### Plan

1. Replace the legacy navigation with the six screen purposes in the supplied Intelligent FBO Staffing Planner brief: Setup, Baseline vs Super Bowl week, Gap heatmap, Recommended plan, Scenario comparison, and Assumptions / uncertainty / safety.
2. Connect these screens to existing typed inputs and API responses. Reuse the 42 four-hour demand blocks and existing manager-reviewed synthetic roster workflow where those outputs are available.
3. Keep the UI honest about current API scope: the live demand/staffing model still exposes three departments; synthetic seven-zone/role CSV fixtures are not yet wired into the planner; recommendation actions such as overtime, part-time offers, reassignment, and reserves are not yet produced by the API. Show these as explicit implementation gaps instead of deriving invented recommendations.
4. Preserve labels for synthetic, JFK proxy, and assumption-based outputs; preserve manager approval and prohibit dispatch or movement authority.

### Task breakdown

- Rework navigation and page descriptions to the required six screens.
- Add editable setup controls for current supported scenario, dates as display-only planning context, service-time ratios, demand scaling, and roster constraints.
- Show ordinary/event four-hour profiles and available uncertainty/provenance caveats.
- Add a 42-block coverage heatmap from the existing block requirements; identify that its three department rows are provisional and not the requested seven-zone matrix.
- Present the existing baseline/proposed roster comparison and approval workflow as the currently supported preparation-plan review.
- Expand low/medium/high demand comparison with the API's available metrics and make unavailable staffing action metrics explicit.
- Create a dedicated assumptions, limitations, privacy, and human-authority screen.
- Update API/UI types only where needed; retain API compatibility.

### Acceptance

- All six required screen purposes are directly reachable from navigation.
- All displayed numeric values come from current API responses or user-editable assumptions.
- The 42 block grid is populated from the backend response, not a fabricated fixture.
- Synthetic and JFK-proxy provenance and the current three-department limitation remain visible.
- Approval is still manager initiated and bound to the built plan snapshot.
- Frontend production build succeeds.

### Status

Implemented in `frontend/src/App.tsx`, `frontend/src/GapHeatmap.tsx`, and `frontend/src/plannerTypes.ts`. Six navigation screens now follow the supplied brief; the heatmap and baseline/event table use live four-hour API fields, and the event roster remains manager-reviewed. Seven-zone/role optimization, actionable reassignment/overtime/part-time/reserve recommendations, and forecast uncertainty intervals remain unavailable and are labeled in the UI. Stage 6 adds a defined subset of calculated impact measures.

## Stage 6 — impact measurement and data readiness

### Plan

1. Compare the ordinary-week roster left unchanged with the event-week roster under the exact same selected event demand, scenario, and disruption inputs.
2. Return measured coverage, uncovered blocks, severe-gap blocks, modeled labor-cost delta, and an explicitly labeled service-delay proxy derived from the schedules and requirements.
3. Show these figures in Scenario Comparison and Recommended Plan, including definitions, the synthetic-data label, and unavailable reserve/action metrics.
4. Validate whether a suitable LAX 2022 arrivals source is present before integrating it. Keep JFK proxy results distinct; no LAX file or verified source is present in this checkout.

### Task breakdown

- Track hourly coverage gaps for both rosters and derive four-hour block impact counts.
- Compare both rosters under the same selected event demand and disruption.
- Define delay risk as a scenario indicator: 10 assumed delay minutes per uncovered Ramp Operations seat-hour. This is an unvalidated demo assumption, not an operational prediction.
- Calculate incremental modeled labor cost and cost per coverage percentage point only when the proposed plan improves coverage.
- Surface unavailable reserve efficiency and overtime/part-time/reassignment results rather than inventing them.
- Record missing/unverified LAX data as a dependency; maintain current provenance labels.
- Add deterministic API tests for same-scenario comparison and impact calculations.

### Acceptance

- Baseline and proposed metrics share event demand, scenario, and disruption inputs.
- Every displayed impact metric is derived from the API response, with formulas visible in UI/docs.
- Uncovered block counts distinguish any gap from peak gaps of at least three positions.
- Cost-per-coverage-point is absent when coverage does not improve; labor estimates remain labeled synthetic.
- No LAX provenance or real-world performance claim is made without a validated source.

### Data limitation

The data described in the supplied audit is a 2013 JFK airline-departure proxy. The LAX 2022 file and source metadata are not present in this working tree. Stage 6 can complete synthetic impact measurement now; actual LAX data integration remains pending source validation.

### Status

Implemented in `backend/scheduling.py`, `backend/main.py`, `backend/tests/test_main_integration.py`, `frontend/src/App.tsx`, and `frontend/src/plannerTypes.ts`. Staffing-plan responses now include same-scenario baseline/proposed coverage, four-hour gap counts, modeled labor-cost delta, cost per positive coverage point, and an explicitly assumed ramp delay-risk proxy. The decision record stores the impact snapshot. The UI exposes those values and keeps action-hours/reserve-efficiency metrics unavailable. LAX integration remains blocked on receiving and validating the source file. Verification: frontend production build passes; targeted integration tests pass (3); full backend suite reports 26 passed and one desktop test blocked because its local socket bind is not permitted in this environment.
