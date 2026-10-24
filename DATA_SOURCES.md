# Data sources and model results

## Current command center

The Next.js dashboard uses a fixed-seed TypeScript operations fixture and calculated task assignments. No task metrics or improvements are placeholders. Demand profiles, aircraft, tasks, qualified crews, shift/break windows, service deadlines, and disruptions remain synthetic. Optional uploaded counts drive aircraft activity, but tasks/workforce assumptions are still synthetic. The dashboard is a selected-day task replay, not a trained forecast or full-week employee roster. It makes no accuracy or observed-savings claim.

The Python weekly planner below is retained separately and is not currently the task dashboard's data provider. Its generated holdout metrics must not be presented as validation of the new task fixture.

## Retained weekly planner

The default is a model fitted to generated synthetic history. Optional CSV uploads supply a complete ordinary-week profile with hour, aircraft activity, passenger count, and fuel-service-request counts. Uploaded values are not independently verified, and a single week does not establish forecast accuracy. Event scaling and workforce remain assumptions. The original CSV is not stored; manager decision records retain its counts and source name.

The former JFK proxy remains available through legacy API modes; it is not offered in the new guided interface. Its pipeline and limitations are documented below for reproducibility.

## Optional real-data proxy

The research notes record a separate LAWA reference: Van Nuys Airport recorded 47,501 aircraft operations in Q2 2025, including 39,552 general aviation operations. Source: [LAWA VNY Q2 2025 report](https://www.lawa.org/sites/lawa/files/2025-09/VNY%202q25_%2020250916_Quarterly%20Report2.pdf). These are airport-operation counts, not FBO service requests, employee hours, or inputs to the staffing forecast.

The aircraft-activity model is trained on **observed 2013 JFK airline departures** from nycflights13. This is not FBO arrival data. It provides a reproducible traffic-pattern proxy, not evidence that the application forecasts private aviation accurately.

- Original package documentation: https://nycflights13.tidyverse.org/reference/flights.html
- CSV mirror: https://vincentarelbundock.github.io/Rdatasets/csv/nycflights13/flights.csv
- Upstream source: RITA / U.S. Bureau of Transportation Statistics, as identified by the package documentation.
- Package license: CC0, declared at https://github.com/tidyverse/nycflights13/blob/main/DESCRIPTION
- Downloaded and inspected: 336,776 rows; actual columns recorded in `backend/data/real_forecast.json`.
- Raw-file SHA-256: `b791a2590c9167aa0bd3cb45af3f64101180878cf088c183eae4011e3a654f42`.

The 33 MB raw CSV stays in `backend/data/raw/` and is ignored by Git. Reproduce the download and training with:

```powershell
.\.venv\Scripts\python -m backend.real_training --download
```

This explicitly downloads the source only when absent. The app never needs a network connection for inference.

## Cleaning and aggregation

The pipeline verifies the actual columns, selects JFK (111,279 source rows), excludes 1,863 missing departure records, and reconstructs actual departure datetimes by adding `dep_delay` to the scheduled date and `sched_dep_time`. This handles departure delays crossing midnight. Three departures fall outside 2013 and are excluded. Result: **109,413 observed departures**, aggregated into **8,760 local wall-clock hourly bins**, including zero-activity bins. Local clock bins are used rather than absolute elapsed hours; DST repeated-hour observations share a bin and a missing-hour bin has zero activity. This is documented preprocessing, not a claim that the records contain complete FBO operations.

Generated files:

- `real_jfk_hourly_departures.csv`: observed hourly target, timestamps and explicit provenance.
- `real_forecast_holdout.csv`: later-period observed targets, fitted predictions and baseline predictions for audit.
- `real_forecast.json`: coefficients, source metadata, actual columns, cleaning counts and held-out metrics.

## Training and evaluation

The fitted model is ridge regression (alpha 10), using calendar features: hour indicators, weekday indicators, annual sine/cosine, and weekend-by-hour interactions. No future target counts are features. First 7,008 hours train the evaluation model; the final 1,752 hours (2013-10-20 through 2013-12-31) are held out. The comparator is a time-of-day mean computed on the training period only.

| Evaluation on real airline departures | Departures / hour |
| --- | ---: |
| Fitted model mean absolute error | 2.1146 |
| Simple time-of-day baseline mean absolute error | 2.1134 |
| Fitted model root mean squared error | 2.9510 |

**The fitted model does not outperform the baseline on this holdout.** Results establish a working real-data pipeline, not superior prediction. After evaluation, inference coefficients are refitted on the full dataset. The reported scores belong to the pre-refit evaluation model.

## What is still assumed?

The app samples a Monday–Sunday calendar profile for 2013-02-04 through 2013-02-10. This is an illustrative historical calendar profile, not a future-date forecast or an event-specific prediction. A configurable share of JFK activity (default 25%) is used as an FBO workload scenario. Using an airport activity pattern to drive inbound service requests is a deliberate scenario assumption, not a conversion of observed departures into observed FBO arrivals.

Passenger count (4.5 per aircraft), fueling probability (65%), all service durations, department minimums, productivity, wages and qualified employee seats remain assumptions. Low/Normal/Busy demand scaling is assumed. No passenger, fueling or staffing labels were present in the source CSV; they are not called real observations or separately trained real-data targets. Individual shift feasibility is not solved.

The older synthetic datasets and fitted synthetic model remain available as separate demo modes. The UI labels each mode. Better operational accuracy requires current target-airport arrivals, event history and FBO service logs with permission to use them. FAA or OpenSky adapters can be added later after access, coverage and schema review; they have not been used in this training run.
