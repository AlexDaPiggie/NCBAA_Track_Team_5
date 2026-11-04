# Data sources

## Current website

- The aircraft, tasks, workers, wages, and assignments in the live command-center demo are fixed-seed synthetic data.
- The selected-day replay covers all hours from 00:00 to 24:00. It uses an assumed synthetic overnight low and afternoon arrival peak, not an observed VNY profile. Twelve fictional workers cover fixed 00:00–08:00, 08:00–16:00, and 16:00–24:00 shifts; service tasks can finish through 02:00 next day. A fixed 14:00 PST checkpoint starts disruptions. These are demo settings, not FBO rules.
- The new 7-Day Staffing Plan runs in the browser; it requires no FastAPI connection. It compares an ordinary-week synthetic roster with three event cases (Low 1.15×, Medium 1.4×, High 1.7×). The same seed is used for ordinary and event demand. These factors are demo assumptions, not forecasts.
- For each synthetic task, the model places its full workload in the hour when its service window opens. It calculates required seats from workload, an 80% utilization target, and assumed minimums (ramp 2, fuel 1, customer service 1). For each day and 8-hour block, it plans to the peak hourly seat requirement.
- Synthetic workers have one team qualification, one 8-hour shift per day, a 40-hour weekly cap, an 8-hour minimum rest gap, and a staggered 30-minute break. The model creates enough workers up to a configured-in-code pool limit of 50 per team; any unfilled seats remain visible.
- Coverage is calculated as covered seat-hours divided by required seat-hours, with breaks reducing hourly capacity. This is a capacity estimate, not a task queue or flight-delay simulation.
- Estimated labor is scheduled paid hours multiplied by illustrative role rates ($32 ramp, $35 fuel, $26 customer service). Breaks are assumed paid. Benefits, overtime premiums, and actual payroll rules are omitted. Both baseline and event rosters face the same event demand within each comparison.
- Manager approval or rejection is saved in browser storage and can be downloaded. It does not dispatch workers.

## Synthetic data shaped by historical timing

- `backend/data/lax_super_bowl_week.csv` contains observed LAX commercial-airline records from February 7–13, 2022. The new optional generator reads valid actual arrivals and counts them by local hour.
- `backend/data_generation/generate_synthetic_lax_timing_profile.py` converts those counts to hourly shares, then uses seeded random sampling to create `backend/data/synthetic_fbo_demand_lax_timing_profile.csv`.
- This is a simple empirical profile, not a trained AI model. It generates 672 synthetic hourly rows: seven days × 24 hours × ordinary, low, medium, and high scenarios.
- The 17-aircraft daily base, event multipliers, 4.5 passengers per aircraft, and 0.65 fuel-request chance are demo assumptions. Only the hourly timing shares come from the observed LAX airline data.
- The source is commercial airline arrivals. It does not describe VNY, general aviation, FBO visits, or staffing demand. The synthetic output is a demonstration artifact and is not connected to the website planner. See [generation notes](../backend/data_generation/README.md) and the [pattern diagram](presentation/Synthetic_Data_Pattern_Diagram.png).

## Separate weekly FastAPI planner

- Default demand, workers, service rates, task times, and wages are configurable demo assumptions or synthetic fixtures.
- The optional JFK proxy uses observed 2013 commercial airline departures and scales them as an assumed workload. It is not LA traffic or FBO activity.
- The trained model uses generated synthetic history. Its holdout metrics do not establish real-world accuracy.
- Uploaded aggregate ordinary-week counts are user-supplied and are not independently verified.

All airport traffic must remain separate from FBO workload unless validated FBO demand data becomes available. No passenger identity data is used.
