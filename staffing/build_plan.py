"""Create a sample staffing plan from the generated CSVs."""

from pathlib import Path
import csv

from staffing.planner import load_scenario, load_workers, plan_staffing


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"


if __name__ == "__main__":
    workers = load_workers(DATA / "worker_profiles.csv")
    demand = load_scenario(DATA / "hourly_demand.csv", "event_medium")
    plan = plan_staffing(demand, workers)
    output = DATA / "staffing_plan_event_medium.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("hour_index", "role", "task_hours", "available_workers", "assigned_workers", "covered_task_hours", "uncovered_task_hours"))
        for item in plan.hourly:
            writer.writerow((item.hour_index, item.role, item.task_hours, item.available_workers, ";".join(item.assigned_workers), item.covered_task_hours, item.uncovered_task_hours))
    print(f"Scenario: event_medium")
    print(f"Task hours: {plan.total_task_hours:.1f}")
    print(f"Covered task hours: {plan.covered_task_hours:.1f}")
    print(f"Uncovered task hours: {plan.uncovered_task_hours:.1f}")
    print(f"Assigned labor hours: {plan.assigned_labor_hours:.1f}")
    print(f"Wrote: {output}")
