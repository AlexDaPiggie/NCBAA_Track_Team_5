"""Simple, transparent hourly staffing planner for synthetic demo data."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import math
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


@dataclass(frozen=True)
class Assignment:
    hour_index: int
    role: str
    worker_id: str
    assigned_hours: float = 1.0


@dataclass(frozen=True)
class HourResult:
    hour_index: int
    role: str
    task_hours: float
    available_workers: int
    assigned_workers: tuple[str, ...]
    covered_task_hours: float
    uncovered_task_hours: float


@dataclass(frozen=True)
class StaffingPlan:
    hourly: tuple[HourResult, ...]
    assignments: tuple[Assignment, ...]
    total_task_hours: float
    covered_task_hours: float
    uncovered_task_hours: float
    assigned_labor_hours: float


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
                    **{task: float(row[f"{task}_task_hours"]) for task in TASK_TYPES},
                })
    if not rows:
        raise ValueError(f"scenario not found: {scenario}")
    return sorted(rows, key=lambda row: int(row["hour_index"]))


def plan_staffing(
    demand: list[dict[str, float | int]],
    workers: list[Worker],
    *,
    absent_worker_ids: frozenset[str] = frozenset(),
) -> StaffingPlan:
    """Assign qualified workers to hourly task workload, within availability and hour caps.

    The planner allocates whole workers for each one-hour bucket. This is a demo
    heuristic, not a labor-compliant roster optimizer. Breaks and minimum rest
    between shifts are not modeled.
    """
    weekly_used = {worker.worker_id: 0 for worker in workers}
    worker_by_id = {worker.worker_id: worker for worker in workers}
    hourly_results: list[HourResult] = []
    assignments: list[Assignment] = []

    for row in sorted(demand, key=lambda x: int(x["hour_index"])):
        hour_index = int(row["hour_index"])
        day = hour_index // 24 + 1
        hour = hour_index % 24
        for role in TASK_TYPES:
            task_hours = float(row[role])
            eligible = [w for w in workers if (
                w.worker_id not in absent_worker_ids
                and role in w.skills
                and day in w.available_days
                and w.shift_start_hour <= hour < w.shift_end_hour
                and weekly_used[w.worker_id] < w.max_weekly_hours
            )]
            required = math.ceil(task_hours)
            # Prefer workers with fewer assigned hours to spread workload.
            eligible.sort(key=lambda w: (weekly_used[w.worker_id], w.worker_id))
            chosen = eligible[:required]
            for worker in chosen:
                weekly_used[worker.worker_id] += 1
                assignments.append(Assignment(hour_index, role, worker.worker_id))
            labor = float(len(chosen))
            covered = min(task_hours, labor)
            hourly_results.append(HourResult(
                hour_index, role, task_hours, len(eligible),
                tuple(w.worker_id for w in chosen), covered,
                max(0.0, task_hours - covered),
            ))

    return StaffingPlan(
        hourly=tuple(hourly_results),
        assignments=tuple(assignments),
        total_task_hours=sum(item.task_hours for item in hourly_results),
        covered_task_hours=sum(item.covered_task_hours for item in hourly_results),
        uncovered_task_hours=sum(item.uncovered_task_hours for item in hourly_results),
        assigned_labor_hours=float(len(assignments)),
    )


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
