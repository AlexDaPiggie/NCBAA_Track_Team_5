"""Shift-based roster comparison with explicit, configurable constraints."""

from __future__ import annotations

from dataclasses import dataclass
import math

from data_generation.synthetic import TASK_TYPES
from staffing.planner import Worker

HOURS_PER_DAY = 24


@dataclass(frozen=True)
class Shift:
    worker_id: str
    day: int
    start_hour: int
    end_hour: int

    @property
    def hours(self) -> int:
        return self.end_hour - self.start_hour


@dataclass(frozen=True)
class PlanMetrics:
    task_hours: float
    covered_task_hours: float
    uncovered_task_hours: float
    scheduled_worker_hours: int
    coverage_percent: float


def baseline_schedule(workers: list[Worker], absent: frozenset[str] = frozenset()) -> list[Shift]:
    """Create a simple rotating four-shift-per-worker baseline roster."""
    shifts: list[Shift] = []
    for index, worker in enumerate(workers):
        if worker.worker_id in absent:
            continue
        shift_hours = worker.shift_end_hour - worker.shift_start_hour
        max_shifts = worker.max_weekly_hours // shift_hours
        days = sorted(worker.available_days)
        if not days:
            continue
        offset = (index * max_shifts) % len(days)
        rotated = days[offset:] + days[:offset]
        for day in rotated[:max_shifts]:
            shifts.append(Shift(worker.worker_id, day, worker.shift_start_hour, worker.shift_end_hour))
    return shifts


def recommended_schedule(
    demand: list[dict[str, float | int]],
    workers: list[Worker],
    absent: frozenset[str] = frozenset(),
) -> list[Shift]:
    """Place whole shifts on days with the most uncovered skill-matched work.

    Greedy heuristic. It respects each worker's available days, fixed shift
    window, one shift per day, and max weekly hours. Every shift for a worker
    uses the same time window, so this version does not create short turnarounds.
    """
    clean_workers = [w for w in workers if w.worker_id not in absent]
    coverage: dict[tuple[int, str, int], int] = {}
    counts: dict[tuple[str, int], int] = {}
    shifts: list[Shift] = []

    def score(worker: Worker, day: int) -> float:
        shift_hours = worker.shift_end_hour - worker.shift_start_hour
        total = 0.0
        for row in demand:
            hour_index = int(row["hour_index"])
            row_day = hour_index // HOURS_PER_DAY + 1
            hour = hour_index % HOURS_PER_DAY
            if row_day != day or not worker.shift_start_hour <= hour < worker.shift_end_hour:
                continue
            for role in TASK_TYPES:
                if role not in worker.skills:
                    continue
                workload = float(row[role])
                needed = math.ceil(workload)
                current = coverage.get((day, role, hour), 0)
                total += max(0, min(needed, current + 1) - min(needed, current))
        # Prefer an even spread when workload benefit is tied.
        return total - counts.get((worker.role, day), 0) * 0.01

    # At most floor(max weekly hours / shift length) full shifts per worker.
    # Add the next shift to the worker/day pairing with the largest marginal cover.
    for worker in clean_workers:
        shift_hours = worker.shift_end_hour - worker.shift_start_hour
        if shift_hours <= 0:
            continue
        max_shifts = worker.max_weekly_hours // shift_hours
        worked_days: set[int] = set()
        for _ in range(max_shifts):
            candidates = [d for d in sorted(worker.available_days) if d not in worked_days]
            if not candidates:
                break
            day = max(candidates, key=lambda d: (score(worker, d), -counts.get((worker.role, d), 0), -d))
            worked_days.add(day)
            shifts.append(Shift(worker.worker_id, day, worker.shift_start_hour, worker.shift_end_hour))
            counts[(worker.role, day)] = counts.get((worker.role, day), 0) + 1
            for row in demand:
                hour_index = int(row["hour_index"])
                if hour_index // HOURS_PER_DAY + 1 != day:
                    continue
                hour = hour_index % HOURS_PER_DAY
                if not worker.shift_start_hour <= hour < worker.shift_end_hour:
                    continue
                for role in worker.skills.intersection(TASK_TYPES):
                    key = (day, role, hour)
                    coverage[key] = coverage.get(key, 0) + 1
    return shifts


def evaluate_schedule(
    demand: list[dict[str, float | int]],
    shifts: list[Shift],
    workers: list[Worker],
) -> PlanMetrics:
    """Calculate demand coverage and scheduled hours for one roster."""
    worker_by_id = {w.worker_id: w for w in workers}
    by_day_role_hour: dict[tuple[int, str, int], int] = {}
    for shift in shifts:
        for hour in range(shift.start_hour, shift.end_hour):
            worker = worker_by_id[shift.worker_id]
            for role in worker.skills.intersection(TASK_TYPES):
                key = (shift.day, role, hour)
                by_day_role_hour[key] = by_day_role_hour.get(key, 0) + 1

    total = covered = 0.0
    for row in demand:
        hour_index = int(row["hour_index"])
        day, hour = hour_index // HOURS_PER_DAY + 1, hour_index % HOURS_PER_DAY
        for role in TASK_TYPES:
            workload = float(row[role])
            available = by_day_role_hour.get((day, role, hour), 0)
            total += workload
            covered += min(workload, float(available))
    uncovered = max(0.0, total - covered)
    percent = (covered / total * 100) if total else 100.0
    return PlanMetrics(total, covered, uncovered, sum(s.hours for s in shifts), percent)


def compare_schedules(
    demand: list[dict[str, float | int]],
    workers: list[Worker],
    absent: frozenset[str] = frozenset(),
) -> dict[str, tuple[list[Shift], PlanMetrics]]:
    """Compare baseline and recommended rosters on identical demand and absences."""
    baseline = baseline_schedule(workers, absent)
    proposed = recommended_schedule(demand, workers, absent)
    return {
        "baseline": (baseline, evaluate_schedule(demand, baseline, workers)),
        "recommended": (proposed, evaluate_schedule(demand, proposed, workers)),
    }


def add_arrival_surge(
    demand: list[dict[str, float | int]],
    *,
    hour_index: int,
    extra_arrivals: int,
    task_hours_per_arrival: dict[str, float],
) -> list[dict[str, float | int]]:
    """Return a copy of demand with extra arrivals and work in one hour."""
    if extra_arrivals < 0:
        raise ValueError("extra_arrivals must be non-negative")
    updated = [dict(row) for row in demand]
    target = next((row for row in updated if int(row["hour_index"]) == hour_index), None)
    if target is None:
        raise ValueError(f"hour not found: {hour_index}")
    target["arrivals"] = int(target.get("arrivals", 0)) + extra_arrivals
    for role in TASK_TYPES:
        target[role] = float(target[role]) + extra_arrivals * task_hours_per_arrival[role]
    return updated
