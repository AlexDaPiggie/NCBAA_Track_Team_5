"""Simple, transparent hourly staffing planner for synthetic demo data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from data_generation.synthetic import TASK_TYPES


@dataclass(frozen=True)
class Worker:
    worker_id: str
    role: str
    skills: frozenset[str]
    available_days: frozenset[int]
    shift_start_hour: int
    shift_end_hour: int
    max_weekly_hours: int


def load_workers(path: Path) -> list[Worker]:
    """Read worker profiles from the demo CSV."""
    workers = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            workers.append(Worker(
                worker_id=row["worker_id"],
                role=row["role"],
                skills=frozenset(x.strip() for x in row["skills"].split(",") if x.strip()),
                available_days=_parse_days(row["available_days"]),
                shift_start_hour=int(row["shift_start_hour"]),
                shift_end_hour=int(row["shift_end_hour"]),
                max_weekly_hours=int(row["max_weekly_hours"]),
            ))
    return workers


def load_scenario(path: Path, scenario: str) -> list[dict[str, float | int]]:
    """Read one 168-hour scenario from the hourly demand CSV."""
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["scenario"] == scenario:
                rows.append({
                    "hour_index": (int(row["day_index"]) - 1) * 24 + int(row["hour_local"]),
                    "arrivals": int(row["arrivals"]),
                    **{task: float(row[f"{task}_task_hours"]) for task in TASK_TYPES},
                })
    if not rows:
        raise ValueError(f"scenario not found: {scenario}")
    return sorted(rows, key=lambda row: int(row["hour_index"]))


def load_task_assumptions(path: Path) -> dict[str, float]:
    """Read estimated task hours per arrival from the assumptions CSV."""
    with path.open(newline="", encoding="utf-8") as f:
        return {row["task_type"]: float(row["hours_per_arrival"]) for row in csv.DictReader(f)}


def _parse_days(value: str) -> frozenset[int]:
    """Parse values such as '1-5' or '1,3,5' into day numbers."""
    days: set[int] = set()
    for part in value.split(","):
        bounds = part.split("-")
        if len(bounds) == 1:
            days.add(int(bounds[0]))
        elif len(bounds) == 2:
            start, end = (int(x) for x in bounds)
            days.update(range(start, end + 1))
        else:
            raise ValueError(f"invalid available_days: {value}")
    return frozenset(days)
