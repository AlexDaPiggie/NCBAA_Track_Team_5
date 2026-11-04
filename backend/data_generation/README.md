# Synthetic demand from an observed timing pattern

## Files

- `../data/lax_super_bowl_week.csv`: existing observed LAX commercial airline records for February 7–13, 2022.
- `../data/synthetic_fbo_demand_lax_timing_profile.csv`: generated 7-day demo data. Four scenarios, 168 hours each.
- `generate_synthetic_lax_timing_profile.py`: generator.

## How it works

1. Keep non-cancelled, non-diverted flights with an actual arrival time and LAX as destination.
2. Count those arrivals by local hour. Convert each count to a share of the week. This is a simple frequency profile, not a trained AI model.
3. For each day and scenario, set a fictional total of 17 aircraft per day, then multiply by the scenario factor: ordinary 1.0, low 1.15, medium 1.4, high 1.7.
4. Use a fixed random seed to distribute each daily total across hours using the observed LAX hourly shares.
5. Generate passenger and fuel request estimates with assumed rates: 4.5 passengers per aircraft and a 0.65 chance of a fuel request per aircraft.

Regenerate from the project root:

```powershell
python backend/data_generation/generate_synthetic_lax_timing_profile.py
```

## Limits

The source shows large-airline commercial arrivals at LAX in 2022. It does not show Van Nuys traffic, private aircraft, FBO visits, passengers per FBO aircraft, fuel requests, or staffing needs. Only the hourly timing shape is reused. The daily scale, scenario factors, passenger estimates, and fuel requests are assumptions. Output rows are synthetic. Do not call this an LAX FBO forecast or real staffing demand. This dataset is a demonstration artifact and is not connected to the website planner.
