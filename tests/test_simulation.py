import unittest

from data_generation.synthetic import HOURS_PER_WEEK, forecast_error, generate_week
from staffing.planner import Worker
from staffing.shifts import add_arrival_surge, baseline_schedule, compare_schedules, recommended_schedule


class SyntheticWeekTests(unittest.TestCase):
    def test_fixed_seed_is_repeatable(self):
        self.assertEqual(generate_week(17), generate_week(17))

    def test_week_has_168_hour_buckets_and_nonnegative_demand(self):
        week = generate_week(17)
        self.assertEqual(len(week), HOURS_PER_WEEK)
        self.assertTrue(all(item.arrivals >= 0 for item in week))
        self.assertTrue(all(value >= 0 for item in week for value in item.task_hours.values()))

    def test_negative_multiplier_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_week(17, event_multiplier=-1)

    def test_mae_checks_alignment_and_calculates(self):
        actual = generate_week(17)
        self.assertEqual(forecast_error(actual, actual), 0)
        with self.assertRaises(ValueError):
            forecast_error(actual, actual[:-1])


class ShiftPlannerTests(unittest.TestCase):
    def setUp(self):
        self.workers = [
            Worker("R1", "ramp", frozenset({"ramp"}), frozenset(range(1, 8)), 6, 14, 16),
            Worker("R2", "ramp", frozenset({"ramp"}), frozenset(range(1, 8)), 6, 14, 16),
        ]
        self.demand = [
            {"hour_index": day * 24 + 6, "ramp": 1.5, "customer_service": 0, "baggage": 0}
            for day in range(7)
        ]

    def test_baseline_has_full_shifts_and_respects_weekly_limit(self):
        shifts = baseline_schedule(self.workers)
        self.assertTrue(all(s.end_hour - s.start_hour == 8 for s in shifts))
        for worker in self.workers:
            hours = sum(s.hours for s in shifts if s.worker_id == worker.worker_id)
            self.assertLessEqual(hours, worker.max_weekly_hours)

    def test_recommended_schedule_uses_available_days_and_skill(self):
        shifts = recommended_schedule(self.demand, self.workers)
        self.assertTrue(all(s.day in range(1, 8) and 6 <= s.start_hour < s.end_hour <= 14 for s in shifts))
        self.assertTrue(all(sum(s.worker_id == w.worker_id for s in shifts) <= 2 for w in self.workers))
        for worker in self.workers:
            days = [s.day for s in shifts if s.worker_id == worker.worker_id]
            self.assertEqual(len(days), len(set(days)))

    def test_same_scenario_and_callouts_apply_to_both_plans(self):
        result = compare_schedules(self.demand, self.workers, frozenset({"R1"}))
        self.assertEqual(result["baseline"][1].task_hours, result["recommended"][1].task_hours)
        self.assertNotIn("R1", {s.worker_id for s in result["baseline"][0]})
        self.assertNotIn("R1", {s.worker_id for s in result["recommended"][0]})

    def test_recommendation_targets_peak_day(self):
        demand = [
            {"hour_index": day * 24 + 6, "ramp": 2 if day == 6 else 0, "customer_service": 0, "baggage": 0}
            for day in range(7)
        ]
        result = compare_schedules(demand, self.workers)
        self.assertLess(result["recommended"][1].uncovered_task_hours, result["baseline"][1].uncovered_task_hours)

    def test_arrival_surge_changes_only_selected_hour(self):
        demand = [dict(row) for row in self.demand]
        surged = add_arrival_surge(
            demand, hour_index=6, extra_arrivals=2,
            task_hours_per_arrival={"ramp": 0.75, "customer_service": 0.35, "baggage": 0.25},
        )
        self.assertEqual(surged[0]["arrivals"], 2)
        self.assertEqual(surged[0]["ramp"], 1.5 + 1.5)
        self.assertEqual(surged[1:], demand[1:])


if __name__ == "__main__":
    unittest.main()
