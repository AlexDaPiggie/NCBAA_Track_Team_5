# Apron: 48-hour team plan

## Goal

Improve the staffing demo around the organizer's needs: forecast workload, compare staffing plans, test disruptions, and keep a manager in control. All results stay labeled synthetic unless real FBO data is supplied and checked.

## Work for five people

| Member | Owns | Deliverable | Done when |
|---|---|---|---|
| 1. Data and forecast | Review public aviation data and forecast inputs. Record source, coverage, and limits. Keep synthetic data as the fallback. | Clear demand input and provenance notes. | Every value is either sourced or labeled an assumption; forecast evaluation uses held-out data. |
| 2. Workload model | Review service types and task durations with an aviation mentor. Make task times and staffing thresholds configurable. | Documented workload settings and examples. | A manager can change assumptions without editing code; unverified rules are labeled. |
| 3. Shift planner | Add individual worker availability, skills, shift limits, and configurable break/rest rules. | Feasible draft roster with uncovered-work metrics. | Tests check each constraint; no employee is assigned outside their configured availability. |
| 4. Disruption and web | Add arrival surge, delay, and worker call-out controls. Show baseline and proposed plans on the same scenario. | Interactive disruption comparison in the Apron UI. | Same seed and disruption feed both plans; changes and trade-offs are visible. |
| 5. Integration, QA, demo | Keep the API contract aligned, run integration checks, collect mentor feedback, and prepare the demo. | Working run instructions, tested demo, and pitch. | A new teammate can start the app from the README; demo finishes without manual code edits. |

## Timing

### Hours 0–2: agree on the handoff

Member 5 writes down the input/output fields for demand, worker availability, scenario, disruption, and plan metrics. Members 1–4 agree before changing files.

### Hours 2–20: build in parallel

Members 1–4 work in their own areas. Member 5 prepares the test checklist and checks changes against the shared API contract.

### Hours 20–32: connect the parts

Connect the forecast, workload model, roster, disruptions, and UI. Fix integration issues before adding more features.

### Hours 32–42: validate and simplify

Run deterministic tests. Compare baseline and proposed plans on identical demand and disruptions. Ask a mentor to review task and staffing assumptions. Remove claims the evidence does not support.

### Hours 42–48: rehearse

Freeze features, reset the demo data, rehearse the scenario, and prepare a screenshot or recording as backup.

## Demo acceptance checklist

- Show ordinary and event-week demand with low, medium, and high settings.
- Show an individual draft roster that follows configured availability and skills.
- Apply one arrival surge and one worker absence.
- Compare baseline and proposed plans with the same demand and disruption.
- Show workload covered, uncovered workload, scheduled hours, cost if configured, and uncertainty.
- Keep manager approval as the final step. Do not dispatch workers or authorize aircraft movement.
- Call synthetic results synthetic. Do not claim real-world accuracy or savings.

## Keep scope focused

This is a staffing planner. Fuel Services may be a team needing staff; fuel loading amounts are outside the project. Do not add aircraft movement control, passenger records, or automatic dispatch.
