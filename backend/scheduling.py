"""Deterministic synthetic shift roster and disruption capacity evaluation."""
import math
import random
from collections import defaultdict

from .model import DEFAULTS

WORKER_POOL_SIZE = 30  # Matches the synthetic employee fixture per department.


def _plan_roster(needs, config, shift_hours, max_weekly_hours, minimum_rest_hours,
                break_minutes, prefix):
    """Cover each fixed shift using synthetic single-skill workers and hard limits."""
    shifts_per_day = 24 // shift_hours
    roster = []
    workers_by_department = {}
    unfilled_by_department = {}
    for department, rules in config.items():
        dept_code = {'Passenger Services': 'PS', 'Ramp Operations': 'RAMP',
                     'Fuel Services': 'FUEL'}.get(department, 'STAFF')
        hourly = {item['hour']: item['required'] for item in needs
                  if item['department'] == department}
        workers = []
        slots = []
        assigned = 0
        for day in range(7):
            for shift_index in range(shifts_per_day):
                start = day * 24 + shift_index * shift_hours
                end = start + shift_hours
                target = max(hourly.get(hour, rules.minimum)
                             for hour in range(start, end))
                for seat in range(target):
                    slots.append((day, start, end, shift_index, seat))

        for day, start, end, shift_index, seat in slots:
            eligible = [worker for worker in workers
                        if worker['hours'] + shift_hours <= max_weekly_hours
                        and start - worker['last_end'] >= minimum_rest_hours]
            if eligible:
                worker = min(eligible, key=lambda item: (item['hours'], item['id']))
            else:
                if len(workers) >= WORKER_POOL_SIZE:
                    continue
                worker_id = f'{prefix}-{dept_code}-{len(workers)+1:03d}'
                worker = dict(id=worker_id, hours=0, last_end=-minimum_rest_hours)
                workers.append(worker)
            worker['hours'] += shift_hours
            worker['last_end'] = end
            break_hours = break_minutes / 60
            # Stagger breaks in four windows around the middle of the shift.
            break_start = (start + shift_hours/2 - break_hours/2
                           + (seat % 4) * min(.25, break_hours/4 if break_hours else 0))
            roster.append(dict(employee_id=worker['id'], department=department,
                               day=day+1, start_hour=start % 24,
                               end_hour=24 if end % 24 == 0 else end % 24,
                               week_start_hour=start, week_end_hour=end,
                               shift_hours=shift_hours, break_start=round(break_start, 2),
                               break_end=round(break_start+break_hours, 2),
                               break_minutes=break_minutes, qualification=department,
                               provenance='synthetic worker; assumed available and qualified'))
            assigned += 1
        workers_by_department[department] = workers
        unfilled_by_department[department] = len(slots)-assigned
    return roster, workers_by_department, unfilled_by_department


def _evaluate(roster, workers_by_department, event_rows, requirements, config,
              max_weekly_hours, break_minutes, absences, surge_percent,
              service_delay_percent, disruption_day, disruption_start, disruption_hours,
              seed, unfilled_by_department):
    rng = random.Random(seed)
    affected_start = disruption_day * 24 + disruption_start
    affected_end = affected_start + disruption_hours
    affected_workers = sorted({shift['employee_id'] for shift in roster
                                if shift['week_start_hour'] < affected_end
                                and shift['week_end_hour'] > affected_start})
    global_absent_ids = set(rng.sample(affected_workers, min(absences, len(affected_workers))))
    results = []
    all_gap_by_hour = defaultdict(float)
    for department, rules in config.items():
        worker_ids = sorted({shift['employee_id'] for shift in roster
                             if shift['department'] == department
                             and shift['week_start_hour'] < affected_end
                             and shift['week_end_hour'] > affected_start})
        absent_ids = global_absent_ids.intersection(worker_ids)
        needed_by_hour = {item['hour']: item['required'] for item in requirements
                          if item['department'] == department}
        demand_hours = uncovered_seat_hours = covered_seat_hours = 0.0
        disrupted_hours = 0
        max_gap = 0
        for row in event_rows:
            hour = row['hour']
            in_disruption = affected_start <= hour < affected_end
            demand_factor = 1 + (surge_percent / 100 if in_disruption else 0)
            delay_factor = 1 + (service_delay_percent / 100 if in_disruption else 0)
            required = needed_by_hour[hour]
            if in_disruption:
                required = max(rules.minimum, math.ceil(required*demand_factor*delay_factor))
                disrupted_hours += 1
            demand_hours += required
            scheduled = [shift for shift in roster if shift['department'] == department
                         and shift['week_start_hour'] <= hour < shift['week_end_hour']]
            break_loss = sum(max(0, min(hour+1, shift['break_end'])
                                 - max(hour, shift['break_start']))
                             for shift in scheduled) / 1.0
            absent = sum(shift['employee_id'] in absent_ids for shift in scheduled) if in_disruption else 0
            capacity = max(0.0, len(scheduled)-break_loss-absent)
            gap = max(0.0, required-capacity)
            all_gap_by_hour[hour] += gap
            uncovered_seat_hours += gap
            covered_seat_hours += min(required, capacity)
            max_gap = max(max_gap, math.ceil(gap))
        department_shifts = [shift for shift in roster if shift['department'] == department]
        workers = workers_by_department[department]
        labor_hours = sum(worker['hours'] for worker in workers)
        overtime = sum(max(0, worker['hours']-max_weekly_hours) for worker in workers)
        results.append(dict(department=department, workers=len(workers), shifts=len(department_shifts),
                            unfilled_roster_slots=unfilled_by_department[department],
                            scheduled_labor_hours=labor_hours, estimated_labor_cost=round(labor_hours*rules.wage, 2),
                            demand_seat_hours=round(demand_hours, 1),
                            covered_seat_hours=round(covered_seat_hours, 1),
                            uncovered_seat_hours=round(uncovered_seat_hours, 1),
                            peak_uncovered_seats=max_gap, absent_workers=len(absent_ids),
                            overtime_hours=round(overtime, 1), disrupted_hours=disrupted_hours))
    block_gaps = {}
    for hour, gap in all_gap_by_hour.items():
        block_gaps.setdefault(hour // 4, []).append(gap)
    understaffed_blocks = sum(any(gap > 0 for gap in gaps) for gaps in block_gaps.values())
    severe_gap_blocks = sum(max(gaps, default=0) >= 3 for gaps in block_gaps.values())
    total_demand = sum(item['demand_seat_hours'] for item in results)
    total_uncovered = sum(item['uncovered_seat_hours'] for item in results)
    total_covered = sum(item['covered_seat_hours'] for item in results)
    return dict(departments=results,
                workers=sum(item['workers'] for item in results),
                shifts=len(roster),
                scheduled_labor_hours=sum(item['scheduled_labor_hours'] for item in results),
                estimated_labor_cost=round(sum(item['estimated_labor_cost'] for item in results), 2),
                demand_seat_hours=round(total_demand, 1),
                covered_seat_hours=round(total_covered, 1),
                uncovered_seat_hours=round(total_uncovered, 1),
                coverage_percent=round(100*total_covered/max(1,total_demand), 1),
                overtime_hours=round(sum(item['overtime_hours'] for item in results), 1),
                understaffed_blocks=understaffed_blocks,
                severe_gap_blocks=severe_gap_blocks,
                unfilled_roster_slots=sum(item['unfilled_roster_slots'] for item in results),
                absences=absences, surge_percent=surge_percent,
                service_delay_percent=service_delay_percent,
                disruption_window=dict(day=disruption_day+1, start_hour=disruption_start,
                                       hours=disruption_hours))


def compare_staffing_plans(event_rows, ordinary_rows, event_requirements,
                           config=None, seed=42, shift_hours=8, break_minutes=30,
                           max_weekly_hours=40, minimum_rest_hours=8, absences=2,
                           surge_percent=50, service_delay_percent=25,
                           disruption_day=5, disruption_start=15, disruption_hours=4):
    """Build ordinary/event rosters and evaluate both against the same stressed event."""
    config = config or DEFAULTS
    if shift_hours not in (6, 8, 12) or 24 % shift_hours:
        raise ValueError('Shift length must be 6, 8, or 12 hours')
    if not 0 <= break_minutes <= min(60, shift_hours*60/3):
        raise ValueError('Break duration is outside the supported range')
    if max_weekly_hours < shift_hours or max_weekly_hours > 84:
        raise ValueError('Maximum weekly hours must fit at least one shift and be at most 84')
    if minimum_rest_hours < 0 or minimum_rest_hours > 24:
        raise ValueError('Minimum rest must be between 0 and 24 hours')
    if not 0 <= absences <= 10 or not 0 <= surge_percent <= 200 or not 0 <= service_delay_percent <= 200:
        raise ValueError('Disruption values are outside the supported range')
    if not 0 <= disruption_day <= 6 or not 0 <= disruption_start <= 23 or not 1 <= disruption_hours <= 8:
        raise ValueError('Disruption window is invalid')
    if disruption_start + disruption_hours > 24:
        raise ValueError('Disruption window must fit within one day')

    from .model import requirements as get_requirements
    ordinary_requirements = get_requirements(ordinary_rows, config)
    baseline, baseline_workers, baseline_unfilled = _plan_roster(
        ordinary_requirements, config, shift_hours, max_weekly_hours,
        minimum_rest_hours, break_minutes, 'BASE')
    proposed, proposed_workers, proposed_unfilled = _plan_roster(
        event_requirements, config, shift_hours, max_weekly_hours,
        minimum_rest_hours, break_minutes, 'EVENT')
    kwargs = dict(max_weekly_hours=max_weekly_hours, break_minutes=break_minutes,
                  absences=absences, surge_percent=surge_percent,
                  service_delay_percent=service_delay_percent,
                  disruption_day=disruption_day, disruption_start=disruption_start,
                  disruption_hours=disruption_hours, seed=seed)
    baseline_result = _evaluate(baseline, baseline_workers, event_rows, event_requirements, config,
                                unfilled_by_department=baseline_unfilled, **kwargs)
    proposed_result = _evaluate(proposed, proposed_workers, event_rows, event_requirements, config,
                                unfilled_by_department=proposed_unfilled, **kwargs)
    coverage_change = round(proposed_result['coverage_percent'] - baseline_result['coverage_percent'], 1)
    cost_delta = round(proposed_result['estimated_labor_cost'] - baseline_result['estimated_labor_cost'], 2)
    ramp_baseline = next((item for item in baseline_result['departments']
                          if item['department'] == 'Ramp Operations'), None)
    ramp_proposed = next((item for item in proposed_result['departments']
                          if item['department'] == 'Ramp Operations'), None)
    impact = dict(
        comparison_basis='Both rosters evaluated against the same event demand and disruption.',
        baseline_coverage_percent=baseline_result['coverage_percent'],
        proposed_coverage_percent=proposed_result['coverage_percent'],
        coverage_change_percentage_points=coverage_change,
        baseline_understaffed_blocks=baseline_result['understaffed_blocks'],
        proposed_understaffed_blocks=proposed_result['understaffed_blocks'],
        baseline_severe_gap_blocks=baseline_result['severe_gap_blocks'],
        proposed_severe_gap_blocks=proposed_result['severe_gap_blocks'],
        modeled_labor_cost_delta=cost_delta,
        cost_per_coverage_point=(round(cost_delta / coverage_change, 2)
                                 if coverage_change > 0 else None),
        delay_risk_minutes_per_uncovered_ramp_seat_hour=10,
        baseline_delay_risk_minutes=round((ramp_baseline or {}).get('uncovered_seat_hours', 0) * 10, 1),
        proposed_delay_risk_minutes=round((ramp_proposed or {}).get('uncovered_seat_hours', 0) * 10, 1),
        delay_risk_definition='Illustrative proxy: 10 assumed minutes per uncovered Ramp Operations seat-hour; not an aircraft delay forecast.',
        reserve_efficiency=None,
        unavailable_action_metrics=['overtime offers', 'part-time offers', 'reassignments', 'reserve call-ins'],
    )
    return dict(baseline=dict(metrics=baseline_result, shifts=baseline),
                proposed=dict(metrics=proposed_result, shifts=proposed),
                impact=impact,
                assumptions=dict(shift_hours=shift_hours, break_minutes=break_minutes,
                                 max_weekly_hours=max_weekly_hours,
                                 minimum_rest_hours=minimum_rest_hours,
                                 employees_assumed_available=True,
                                 employee_skills='Each synthetic employee has one department qualification.',
                                 break_policy='Break time reduces coverage and is included in paid shift hours for cost estimates; pay treatment is an assumption.',
                                 overtime_rule='Roster scheduler observes the configured weekly maximum.'),
                provenance='Synthetic workers and demand; not an employee schedule for an operating FBO.')
