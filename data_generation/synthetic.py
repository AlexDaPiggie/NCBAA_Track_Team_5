"""Deterministic synthetic demand fixtures for the CrewPilot MVP.

All generated values are illustrative and are not FBO traffic forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
import random

HOURS_PER_WEEK = 7 * 24
TASK_TYPES = ("ramp", "customer_service", "baggage")


@dataclass(frozen=True)
class HourlyDemand:
    hour: int
    arrivals: int
    task_hours: dict[str, float]


def generate_week(seed: int, *, event_multiplier: float = 1.0) -> list[HourlyDemand]:
    """Generate one synthetic week with repeatable daily and hourly patterns."""
    if event_multiplier < 0:
        raise ValueError("event_multiplier must be non-negative")

    rng = random.Random(seed)
    result: list[HourlyDemand] = []
    for hour in range(HOURS_PER_WEEK):
        day_hour = hour % 24
        # Illustrative daytime profile; no site-specific data is implied.
        profile = 0.15 if day_hour < 6 or day_hour > 21 else 0.8 if 6 <= day_hour < 10 else 1.0 if day_hour < 18 else 0.55
        mean = 2.0 * profile * event_multiplier
        arrivals = max(0, round(rng.gauss(mean, max(0.25, mean * 0.35))))
        task_hours = {
            "ramp": arrivals * 0.75,
            "customer_service": arrivals * 0.35,
            "baggage": arrivals * 0.25,
        }
        result.append(HourlyDemand(hour, arrivals, task_hours))
    return result


def forecast_error(actual: list[HourlyDemand], forecast: list[HourlyDemand]) -> float:
    """Mean absolute error for hourly arrival counts; returns 0 for empty input."""
    if len(actual) != len(forecast):
        raise ValueError("actual and forecast must have equal lengths")
    if not actual:
        return 0.0
    return sum(abs(a.arrivals - f.arrivals) for a, f in zip(actual, forecast)) / len(actual)


def write_demo_dataset(output_dir: Path, seed: int = 17) -> None:
    """Write transparent hourly demand, fictional workers, and task assumptions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scenarios = (("ordinary", 1.0), ("event_low", 1.15), ("event_medium", 1.4), ("event_high", 1.7))
    with (output_dir / "hourly_demand.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("week_type", "scenario", "day_index", "hour_local", "arrivals", "ramp_task_hours", "customer_service_task_hours", "baggage_task_hours", "data_status", "seed"))
        for scenario, multiplier in scenarios:
            for item in generate_week(seed, event_multiplier=multiplier):
                writer.writerow(("ordinary" if scenario == "ordinary" else "event", scenario, item.hour // 24 + 1, item.hour % 24, item.arrivals, item.task_hours["ramp"], item.task_hours["customer_service"], item.task_hours["baggage"], "synthetic", seed))

    with (output_dir / "worker_profiles.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("worker_id", "role", "skills", "available_days", "shift_start_hour", "shift_end_hour", "max_weekly_hours", "data_status"))
        profiles = (("ramp", "ramp", "1-7", 6, 14, 36), ("ramp", "ramp", "1-7", 14, 22, 36), ("ramp", "ramp", "1-7", 6, 14, 36), ("customer_service", "customer_service", "1-7", 6, 14, 36), ("customer_service", "customer_service", "1-7", 14, 22, 36), ("customer_service", "customer_service", "1-7", 6, 14, 36), ("baggage", "baggage", "1-7", 6, 14, 36), ("baggage", "baggage", "1-7", 14, 22, 36), ("baggage", "baggage", "1-7", 6, 14, 36))
        for i, (role, skills, days, start, end, max_hours) in enumerate(profiles, 1):
            writer.writerow((f"SYN-{i:02d}", role, skills, days, start, end, max_hours, "synthetic"))

    with (output_dir / "task_assumptions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("task_type", "hours_per_arrival", "assumption_status"))
        writer.writerows((("ramp", 0.75, "unvalidated_demo_assumption"), ("customer_service", 0.35, "unvalidated_demo_assumption"), ("baggage", 0.25, "unvalidated_demo_assumption")))
