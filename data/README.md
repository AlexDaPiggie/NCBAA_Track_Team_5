# Dataset notes

`processed/` contains reproducible demo CSVs generated with `python -m data_generation.build_dataset`. Run `python -m staffing.build_plan` to create `schedule_comparison.csv` and `schedule_metrics.csv`.

- `hourly_demand.csv`: 168 hours each for an ordinary scenario and three event demand scenarios.
- `worker_profiles.csv`: fictional worker roles, skills, availability and assumed weekly limits.
- `task_assumptions.csv`: estimated task hours per arrival. These are placeholders, not measured FBO service times.
- `schedule_metrics.csv`: baseline and recommended coverage summaries for ordinary, event, call-out and surge cases.
- `schedule_comparison.csv`: shift assignments for each plan and case.

## Evidence and limitations

The organizer permits public or synthetic data. FAA OPSNET publishes airport-operation counts, while the FAA Terminal Area Forecast (TAF) offers historical and forecast airport traffic. Neither source describes FBO-specific service requests, task duration, or staff hours, so neither can directly train a staffing model.

References:

- FAA OPSNET: https://www.aspm.faa.gov/aspmhelp/index/Operations_Network_%28OPSNET%29.html
- FAA TAF: https://www.faa.gov/data_research/aviation/taf
- FAA TAF query/download: https://taf.faa.gov/

The FAA TAF download was identified but could not be retrieved from this environment (the direct download connection was refused). No public traffic numbers are represented in the CSVs. The current data is fully synthetic and labeled as such. Event multipliers, hourly demand profile, work durations, staffing levels, skills, availability and max hours are configurable demo assumptions, not forecasts or aviation policy.
