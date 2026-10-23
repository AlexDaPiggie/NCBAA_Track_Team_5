"""Build baseline and recommended shift rosters for demo scenarios."""

from pathlib import Path
import csv

from staffing.planner import load_scenario, load_task_assumptions, load_workers
from staffing.shifts import add_arrival_surge, compare_schedules

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
ABSENT_WORKERS = frozenset({"SYN-01", "SYN-07"})


def build_plan_files() -> None:
    workers = load_workers(DATA / "worker_profiles.csv")
    task_times = load_task_assumptions(DATA / "task_assumptions.csv")
    with (DATA / "schedule_comparison.csv").open("w", newline="", encoding="utf-8") as schedule_file, \
         (DATA / "schedule_metrics.csv").open("w", newline="", encoding="utf-8") as metrics_file:
        schedule_writer = csv.writer(schedule_file)
        schedule_writer.writerow(("scenario", "disruption", "plan", "worker_id", "day", "start_hour", "end_hour"))
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(("scenario", "disruption", "plan", "task_hours", "covered_task_hours", "uncovered_task_hours", "scheduled_worker_hours", "coverage_percent"))

        cases = [("ordinary", "none", None), ("event_low", "none", None),
                 ("event_medium", "none", None),
                 ("event_high", "none", None), ("event_medium", "two_callouts", ABSENT_WORKERS),
                 ("event_medium", "four_arrival_surge", frozenset())]
        for scenario, disruption, absences in cases:
            demand = load_scenario(DATA / "hourly_demand.csv", scenario)
            if disruption == "four_arrival_surge":
                # Day 4, 15:00 local. The same added workload goes to both plans.
                demand = add_arrival_surge(demand, hour_index=87, extra_arrivals=4, task_hours_per_arrival=task_times)
            results = compare_schedules(demand, workers, absences or frozenset())
            for plan_name, (shifts, metrics) in results.items():
                for shift in shifts:
                    schedule_writer.writerow((scenario, disruption, plan_name, shift.worker_id, shift.day, shift.start_hour, shift.end_hour))
                metrics_writer.writerow((scenario, disruption, plan_name, f"{metrics.task_hours:.1f}", f"{metrics.covered_task_hours:.1f}", f"{metrics.uncovered_task_hours:.1f}", metrics.scheduled_worker_hours, f"{metrics.coverage_percent:.1f}"))
                print(f"{scenario} / {disruption} / {plan_name}: "
                      f"uncovered {metrics.uncovered_task_hours:.1f} of {metrics.task_hours:.1f} task-hours; "
                      f"{metrics.scheduled_worker_hours} scheduled worker-hours; "
                      f"coverage {metrics.coverage_percent:.1f}%")

    print(f"Wrote {DATA / 'schedule_comparison.csv'}")
    print(f"Wrote {DATA / 'schedule_metrics.csv'}")


if __name__ == "__main__":
    build_plan_files()
