from backend.scheduler import plan
from backend.synthetic_roster import WORKERS


def requirements_for(department, hours, seats=1):
    return [dict(hour=h, department=department, required=seats) for h in hours]


def test_assignments_only_use_qualified_workers_and_respect_weekly_caps():
    result = plan(requirements_for('Passenger Services', range(168), seats=1))
    roster = {worker['id']: worker for worker in WORKERS}
    totals = {}
    for assignment in result['assignments']:
        worker = roster[assignment['worker_id']]
        totals[worker['id']] = totals.get(worker['id'], 0) + 8
        assert assignment['department'] in worker['departments']
        assert assignment['day'] - 1 in worker['days']
        assert assignment['shift'] in worker['shifts']
    for worker_id, hours in totals.items():
        assert hours <= roster[worker_id]['weekly_cap']


def test_rest_period_is_enforced_for_assigned_shifts():
    result = plan(requirements_for('Passenger Services', range(168), seats=2))
    starts = {}
    for assignment in result['assignments']:
        hour = {'Morning': 6, 'Afternoon': 14, 'Overnight': 22}[assignment['shift']]
        starts.setdefault(assignment['worker_id'], []).append(((assignment['day']-1)*24+hour) % 168)
    for values in starts.values():
        for i, first in enumerate(values):
            for second in values[i+1:]:
                assert min((first-second) % 168, (second-first) % 168) >= 18


def test_unavailable_or_unqualified_demand_is_reported_as_outside_staff():
    result = plan(requirements_for('Fuel Services', range(168), seats=20))
    assert result['coverage']['outside_staff_needed'] == len(result['shortages'])
    assert result['coverage']['outside_staff_needed'] > 0
    assert all(item['outside_staff_needed'] == 1 for item in result['shortages'])
    assert any(item['ineligibility_reasons'] for item in result['shortages'])


def test_fixed_block_requirement_uses_peak_hourly_seat_count():
    rows = requirements_for('Passenger Services', range(6, 14), seats=1)
    rows += [dict(hour=11, department='Passenger Services', required=3)]
    result = plan(rows)
    morning = [a for a in result['assignments'] if a['day'] == 1 and a['shift'] == 'Morning']
    morning_short = [s for s in result['shortages'] if s['day'] == 1 and s['shift'] == 'Morning']
    assert len(morning) + len(morning_short) == 3
