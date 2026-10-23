# CrewPilot AI

## How the data is made

The [data generator](data_generation/synthetic.py) makes 168 hourly records per week. It uses a fixed random seed, so each run gives the same data.

It creates one ordinary week and three event weeks. The low scenario assumes 15% more arrivals, medium assumes 40% more, and high assumes 70% more than the ordinary week. These are demo assumptions, not forecasts.

Each arrival adds estimated ramp, customer service, and baggage work. See [task assumptions](data/processed/task_assumptions.csv). Worker profiles are fictional. See [worker profiles](data/processed/worker_profiles.csv). All data is synthetic. It is not real FBO traffic or staffing data.

## Run locally (Windows / VS Code)

1. Open this folder in VS Code.
2. In PowerShell, run `python -m data_generation.build_dataset` to create the CSVs.
3. Run `python -m staffing.build_plan` to compare schedules.
4. Run `python -m staffing.server`.
5. Open `http://127.0.0.1:8000` in your browser.
6. Use the scenario menus to compare plans and test call-outs or an arrival surge.
7. Run `python -m unittest discover -s tests` to run checks.

The web page uses results from [schedule metrics](data/processed/schedule_metrics.csv) and [shift assignments](data/processed/schedule_comparison.csv). Manager decisions are saved to `data/processed/approval_log.csv`.

## How the staff planner works

It makes two schedules from the same workers and demand.

- **Baseline:** gives each worker up to four shifts, spread across the week.
- **Recommended:** places shifts on days with the most uncovered work for that worker's skills.

Both use 8-hour shifts. The planner follows worker availability, skills, and weekly hour limits. It then counts workload each hour and reports covered work, uncovered work, and scheduled hours. It compares ordinary demand with event demand. It also tests two worker call-outs and a four-arrival surge. Each disruption is applied to both schedules.

This is a simple planning model. It does not model breaks or fatigue. All data is synthetic. The approve/reject buttons log a manager's choice locally. They do not dispatch staff or control aircraft. A manager must review any plan.

No third-party Python packages are needed.
