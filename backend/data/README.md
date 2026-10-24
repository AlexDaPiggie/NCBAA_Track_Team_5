# Synthetic data: fictional LAX FBO ("Pacific Gateway Aviation")

All data is invented. Workers are anonymous IDs. Rates, ratios, ground times and fuel
amounts are **assumptions**, not measurements. Regenerate with `python generate_synthetic_data.py`
(same seed gives identical files).

**Time model:** days 0-6, six 4-hour blocks per day. Block 0 = 00-04, 1 = 04-08, 2 = 08-12,
3 = 12-16, 4 = 16-20, 5 = 20-24. Peak blocks = 1-4, off-peak = 0 and 5.

| File | Rows | What it is |
|---|---|---|
| `workers.csv` | 55 | One row per worker: role, zone, cross-training, certifications, employment type, hours, overtime and full-time willingness, time off, last-7-day hours, pay rates |
| `baseline_schedule.csv` | ~480 | Ordinary-week schedule: one row per worker per day per 4-hour block |
| `reserve_pool.csv` | 18 | On-call and agency reserves: roles, certifications, lead time, show probability, premium rate, available days |
| `staffing_ratios.csv` | 11 | Workload driver, capacity per person per block, and minimum floors per role |
| `aircraft_mix.csv` | 5 | Share of arrivals, international share, ground time (baseline and event), fuel uplift, workload multiplier per aircraft class |
| `scenario_parameters.csv` | 3 | Low / medium / high multipliers. **The arrivals lift values are placeholders: replace them with values derived from the 2022 data.** |
| `global_assumptions.csv` | 9 | Hard limits (consecutive hours, rest, weekly cap) and workload rates (fuel requests per departure, etc.) |

## Things to know

- **List fields** use semicolons (`FUELING;RAMP_DRIVING`). `days_off` uses day names; `game_week_approved_time_off_days` uses day indexes 0-6.
- **Certifications gate moves.** A worker can only be assigned to a secondary role if they hold that role's certifications, which the generator guarantees.
- **Overtime and willingness are consent records.** The planner may only *offer* overtime to `yes` or `limited` workers, up to `max_extra_hours_per_week`.
- **`hours_last_7_days`** is higher than scheduled for a few workers, so fatigue limits actually bind.
- **Baseline coverage is mostly full, with a few thin slots** (the generator prints them). That is intentional: an ordinary week is rarely perfect. The numbers are fixed by the generator's `TARGETS` table, which is itself an assumption.
- **Required staff** per role and block = `max(floor, ceil(workload / capacity))`. A floor of 0 means workload-driven: still at least 1 whenever there is work.
- **Overtime rule:** the dataset applies 1.5x above 40 h/week. California also has daily overtime rules, so check them before the cost model claims precise dollars.
- **Real-vs-synthetic boundary:** demand (arrivals per block) is *not* in this folder. It comes from your real arrivals data and the 2022 game-week lift.
