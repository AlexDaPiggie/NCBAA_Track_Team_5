# BRAINSTORM

Status: draft for team review. Focus decided: **staffing** (arrivals/parking/fuel = drivers, judges OK'd). See README.

## Variations considered

| # | Product | Pain | Novelty | Judge appeal | Feasibility | Risk |
|---|---|---|---|---|---|---|
| A | **Staffing planner**: forecast demand -> optimized roster per scenario -> manager approval | Real. Event week = understaff (service fail) or overstaff (cost). | Medium. Scheduling software exists; event-surge + uncertainty + explain is the angle. | High. Hits all 3 judging lenses. | High. Forecast + solver + UI standard. | Low-medium |
| B | Arrivals forecaster only | Real but forecasting alone = no "field plan". | Low. | Medium. Weak on practical prep. | Very high | Low. Looks thin. |
| C | Parking/apron allocator | Real. Ramp space is scarce on event week. | Medium | Medium-high, visual | Medium (2D packing, geometry data) | Medium-high. Needs apron layout data we lack. |
| D | Fuel truck + inventory planner | Real. Fuel timing/stockouts matter. | Medium | Medium | Medium | Medium. Needs fuel-flow data we lack. |

## Recommendation

**A, staffing.** Reasons:
- Needs least unavailable data. Workload can be derived from arrivals x service times (assumptions, labeled).
- Constraint solver gives real, non-fake optimization.
- Approval gate maps directly to "humans in command".
- Arrivals, parking, fuel enter as workload drivers, widening the model without becoming separate products.

## AI angles (what makes demo impressive)

1. Forecast with uncertainty (P10/P50/P90) + backtest vs naive baseline.
2. Constraint solver produces roster per low/med/high scenario.
3. LLM co-pilot: manager types a disruption in plain words, agent calls forecast + solver tools, explains diff. Never invents numbers.
4. Monte Carlo risk heatmap: probability of understaffing per hour.
5. Live disruption injection with re-plan in seconds.
6. Visible approval gate + audit log + "AI never does" panel.
7. Stretch: Olympics 2028 profile swap.

## Anti-goals

- No auto dispatch, no movement authority, no passenger data.
- No hard-coded optimization outputs.
- No claims of real FBO performance from synthetic data.
- No second/third product (parking or fuel recommendations).

## Open questions

- Which airport/FBO profile and which public data source? Team to decide.
- Which LLM + who holds the API key?
- Aviation expert check on service times and crew roles (unverified).
