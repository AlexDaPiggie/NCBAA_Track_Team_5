"""Build a seeded synthetic demand example shaped by observed LAX arrival timing.

The source contains commercial airline arrivals, not FBO or general-aviation demand.
Only the distribution across local hours is reused. All generated counts are synthetic.
"""
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "lax_super_bowl_week.csv"
OUTPUT = ROOT / "data" / "synthetic_fbo_demand_lax_timing_profile.csv"

SEED = 20261024
BASE_AIRCRAFT_PER_DAY = 17  # Fictional scale assumption, not learned from LAX.
PASSENGERS_PER_AIRCRAFT = 4.5  # Fictional service-volume assumption.
FUEL_REQUEST_PROBABILITY = 0.65  # Fictional per-aircraft assumption.
SCENARIOS = {"ordinary": 1.0, "low": 1.15, "medium": 1.4, "high": 1.7}
SIMULATION_DATES = pd.date_range("2027-02-08", periods=7, freq="D")


def learn_hourly_profile(path: Path = SOURCE) -> tuple[np.ndarray, np.ndarray]:
    """Estimate the local-hour arrival shares from valid LAX commercial arrivals."""
    frame = pd.read_csv(path)
    required = {"DEST", "ARR_TIME", "CANCELLED", "DIVERTED"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Source file is missing columns: {sorted(missing)}")

    actual = pd.to_numeric(frame["ARR_TIME"], errors="coerce")
    hour = np.floor(actual / 100)
    minute = actual % 100
    valid = (
        frame["DEST"].eq("LAX")
        & pd.to_numeric(frame["CANCELLED"], errors="coerce").eq(0)
        & pd.to_numeric(frame["DIVERTED"], errors="coerce").eq(0)
        & actual.notna()
        & hour.between(0, 23)
        & minute.between(0, 59)
    )
    counts = (
        pd.Series(hour.loc[valid].astype(int))
        .value_counts()
        .reindex(range(24), fill_value=0)
        .sort_index()
        .to_numpy(dtype=int)
    )
    if counts.sum() == 0:
        raise ValueError("No valid actual LAX arrivals found in the source file.")
    return counts, counts / counts.sum()


def build_dataset(seed: int = SEED) -> pd.DataFrame:
    source_counts, hourly_share = learn_hourly_profile()
    random = np.random.default_rng(seed)
    rows = []

    for scenario, multiplier in SCENARIOS.items():
        daily_total = round(BASE_AIRCRAFT_PER_DAY * multiplier)
        for day_index, date in enumerate(SIMULATION_DATES, start=1):
            hourly_counts = random.multinomial(daily_total, hourly_share)
            for hour, aircraft in enumerate(hourly_counts):
                passengers = int(random.poisson(aircraft * PASSENGERS_PER_AIRCRAFT))
                fuel_requests = int(random.binomial(aircraft, FUEL_REQUEST_PROBABILITY))
                rows.append({
                    "scenario": scenario,
                    "scenario_multiplier": multiplier,
                    "date_local": date.date().isoformat(),
                    "day_index": day_index,
                    "hour_local": hour,
                    "source_lax_airline_arrivals_at_hour": int(source_counts[hour]),
                    "learned_hour_share": round(float(hourly_share[hour]), 6),
                    "aircraft": int(aircraft),
                    "passengers": passengers,
                    "fuel_requests": fuel_requests,
                    "seed": seed,
                    "provenance": (
                        "Synthetic FBO demo counts; hourly shares derived from valid 2022 LAX "
                        "commercial airline arrivals; not observed FBO or GA demand"
                    ),
                })

    result = pd.DataFrame(rows)
    return result


if __name__ == "__main__":
    data = build_dataset()
    data.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(data)} rows to {OUTPUT}")
