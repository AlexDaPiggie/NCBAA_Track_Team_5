import unittest

from data_generation.synthetic import HOURS_PER_WEEK, forecast_error, generate_week
from staffing.planner import Worker, plan_staffing


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


class StaffingPlannerTests(unittest.TestCase):
    def setUp(self):
        self.worker = Worker("SYN-01", "ramp", frozenset({"ramp"}), frozenset({1}), 6, 14, 8)
        self.demand = [{"hour_index": 6, "ramp": 0.75, "customer_service": 0, "baggage": 0}]

    def test_assigns_worker_for_covered_task(self):
        plan = plan_staffing(self.demand, [self.worker])
        self.assertEqual(plan.uncovered_task_hours, 0)
        self.assertEqual(plan.assigned_labor_hours, 1)

    def test_absence_creates_uncovered_work(self):
        plan = plan_staffing(self.demand, [self.worker], absent_worker_ids=frozenset({"SYN-01"}))
        self.assertEqual(plan.uncovered_task_hours, 0.75)
        self.assertEqual(plan.assigned_labor_hours, 0)

    def test_weekly_hour_limit_is_respected(self):
        demand = [{"hour_index": h, "ramp": 1, "customer_service": 0, "baggage": 0} for h in range(6, 15)]
        plan = plan_staffing(demand, [self.worker])
        self.assertEqual(plan.assigned_labor_hours, 8)
        self.assertGreater(plan.uncovered_task_hours, 0)


if __name__ == "__main__":
    unittest.main()
