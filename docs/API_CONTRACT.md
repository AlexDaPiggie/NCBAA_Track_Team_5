# CrewPilot planner API

This documents the existing weekly FastAPI engine. The new Next.js command center currently uses a local task-replay provider; see `docs/OPERATIONS_API_CONTRACT.md`. These are separate metric models and are not silently mixed in the UI.

Local FastAPI service, default `http://127.0.0.1:8000`. Interactive schemas: `/docs`.

## POST /api/staffing-plan

Body contains `inputs` plus workforce rules and a disruption. This is the main guided-site endpoint.

```json
{
  "inputs": {
    "scenario": "Medium",
    "forecast_mode": "trained",
    "include_queue_options": false,
    "seed": 42,
    "multiplier": 1,
    "scenario_multipliers": {"Low": 1.15, "Medium": 1.4, "High": 1.7}
  },
  "shift_hours": 8,
  "break_minutes": 30,
  "max_weekly_hours": 40,
  "minimum_rest_hours": 8,
  "worker_pool_size": 30,
  "absences": 2,
  "surge_percent": 50,
  "service_delay_percent": 25,
  "disruption_day": 5,
  "disruption_start": 15,
  "disruption_hours": 4
}
```

Use zero absences/surge/delay to build a plan without additional disruption. Day 0 is Monday; day 5 Saturday. Disruption must fit within a day. Shift lengths are 6, 8, or 12 hours. Worker pool is 1–100 per department, weekly cap must fit a shift and be at most 84 hours, rest is 0–24 hours, break is 0–60 minutes. Call-outs are 0–10, surge/delay 0–200%, disruption length 1–8 hours.

Optional `inputs` dictionaries keyed by `Passenger Services`, `Ramp Operations`, `Fuel Services`:

| Field | Meaning | Bounds |
| --- | --- | --- |
| `service_minutes` | Work minutes per demand unit | 0.1–240 |
| `service_wages` | Illustrative paid hourly rate | 0–500 |
| `staffing_minimums` | Minimum on-duty seats | 1–30 |
| `target_utilization` | Productive fraction of an hour | 0.25–1 |
| `target_wait_minutes` | Legacy queue metric threshold | 1–120 |

`multiplier` is 0.1–3; event factors are 1–3 and must satisfy Low <= Medium <= High. The new site does not use the legacy queue options; disabling them avoids computing unrelated continuous-seat queue simulations. Existing clients default to computing those options.

## Uploaded demand

Set `inputs.forecast_mode` to `uploaded`, add `source_name` (1–120 characters), and add `ordinary_demand`: exactly 168 objects with only `hour`, `aircraft`, `passengers`, and `fuel_requests`. Hours must be unique and cover 0–167. All counts must be finite and nonnegative. Hourly maximums: 1,000 aircraft, 10,000 passenger count, 1,000 fuel requests. Client CSV size limit: 100 KB.

The server rejects missing/duplicate hours, extra per-row keys, invalid counts, missing upload in uploaded mode, or supplied counts in another mode. `ordinary_demand` is optional for existing clients. Upload does not train or score a model. Ordinary counts are multiplied by `multiplier`; event counts additionally by the selected event factor. Scenario totals and staffing use the same values. Workforce remains synthetic.

## Successful response

- `simulation`: ordinary/event hourly profiles, staffing requirements, department assumptions, forecast provenance and optional training report. Uploaded mode has `training_report: null`.
- `scenario_summary`: ordinary total plus low/medium/high totals and peaks.
- `baseline` and `proposed`: synthetic worker shifts and calculated metrics. Both evaluated on the same selected event demand and disruption.
- `assumptions`: workforce rules and availability/qualification limitations.
- `provenance`: identifies synthetic or uploaded demand and synthetic workers.

Each roster's metrics include workers, shifts, labor hours, illustrative labor cost, required/covered/uncovered seat-hours, coverage percentage, unfilled slots, and department breakdown. `seat-hours` are displayed as `worker-hours` in the website. They estimate concurrent coverage, not task queue outcomes. Breaks of absent workers are not deducted again.

## POST /api/staffing-decisions

Same body as `/api/staffing-plan`, plus `manager`, `notes`, and `approved`. Manager must be nonempty (max 100 characters), notes max 2,000. Recomputes the plan and saves a record in local SQLite: ID, timestamp, source/inputs, assumptions, both rosters, metrics, and decision. Returns that record. No dispatch or external notifications.

## Errors and other endpoints

Invalid inputs return HTTP 422. Existing endpoints remain: `POST /api/simulate`, `POST /api/replay`, `POST /api/decisions`, `GET /api/dashboard`, `GET /api/scenario-summary`. The GET summary supports synthetic/proxy query modes; uploaded baselines use the POST staffing endpoint. Legacy JFK mode remains API-accessible but is not offered in the new guided website.
