# CrewPilot AI

## How the data is made

The [data generator](data_generation/synthetic.py) makes 168 hourly records per week. It uses a fixed random seed, so each run gives the same data.

It creates one ordinary week and three event weeks. The low scenario assumes 15% more arrivals, medium assumes 40% more, and high assumes 70% more than the ordinary week. These are demo assumptions, not forecasts.

Each arrival adds estimated ramp, customer service, and baggage work. See [task assumptions](data/processed/task_assumptions.csv). Worker profiles are fictional. See [worker profiles](data/processed/worker_profiles.csv). All data is synthetic. It is not real FBO traffic or staffing data.

## Run locally (Windows / VS Code)

1. Open this folder in VS Code.
2. In PowerShell, run `python -m data_generation.build_dataset` to create the CSVs.
3. Run `python -m staffing.build_plan` to plan the `event_medium` scenario.
4. See the [medium event staffing plan](data/processed/staffing_plan_event_medium.csv).
5. Run `python -m unittest discover -s tests`.

The planner assigns workers by hour and skill. It follows availability and weekly hour limits. It does not model breaks or minimum rest. Results are planning examples for manager review, not approved rosters. No third-party Python packages are needed.
