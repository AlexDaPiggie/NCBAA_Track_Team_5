"""Deterministic greedy assignment for the synthetic seven-day shift prototype."""
from .synthetic_roster import WORKERS

SHIFTS = [
    {"name": "Morning", "start": 6, "end": 14},
    {"name": "Afternoon", "start": 14, "end": 22},
    {"name": "Overnight", "start": 22, "end": 6},
]
SHIFT_HOURS = 8
MIN_REST_HOURS = 10


def plan(requirements):
    req = {(r['hour'], r['department']): r['required'] for r in requirements}
    slots = []
    for day in range(7):
        for shift in SHIFTS:
            hours = ([(day * 24 + h) % 168 for h in range(shift['start'], shift['end'])]
                     if shift['start'] < shift['end'] else
                     [(day * 24 + h) % 168 for h in range(shift['start'], 24)] +
                     [((day + 1) * 24 + h) % 168 for h in range(0, shift['end'])])
            for department in sorted({r['department'] for r in requirements}):
                # Peak hourly seat requirement in a block is the conservative block requirement.
                needed = max((req.get((hour, department), 0) for hour in hours), default=0)
                for position in range(needed):
                    slots.append({"day": day, "shift": shift['name'], "start": day*24+shift['start'], "department": department, "position": position + 1})
    # Cover hardest-to-staff departments first, then chronological slots; stable IDs break ties.
    qualification_counts = {d: sum(d in w['departments'] for w in WORKERS) for d in {s['department'] for s in slots}}
    slots.sort(key=lambda s: (qualification_counts[s['department']], s['start'], s['department'], s['position']))
    hours_used = {w['id']: 0 for w in WORKERS}
    shifts_by_worker = {w['id']: [] for w in WORKERS}
    assignments, shortages = [], []
    for slot in slots:
        eligible, reasons = [], set()
        for worker in WORKERS:
            if slot['day'] not in worker['days'] or slot['shift'] not in worker['shifts']:
                reasons.add('unavailable')
                continue
            if slot['department'] not in worker['departments']:
                reasons.add('not qualified')
                continue
            if hours_used[worker['id']] + SHIFT_HOURS > worker['weekly_cap']:
                reasons.add('weekly hour cap')
                continue
            start = slot['start']
            # A shift consumes 8 hours; its start must be at least 18 hours from
            # another start (8 working + 10 rest), including across week wrap.
            if any(min((start-prev) % 168, (prev-start) % 168) < SHIFT_HOURS + MIN_REST_HOURS
                   for prev in shifts_by_worker[worker['id']]):
                reasons.add('minimum rest')
                continue
            eligible.append(worker)
        if not eligible:
            shortages.append({"day": slot['day']+1, "shift": slot['shift'], "department": slot['department'], "outside_staff_needed": 1, "ineligibility_reasons": sorted(reasons)})
            continue
        worker = min(eligible, key=lambda w: (hours_used[w['id']], w['id']))
        hours_used[worker['id']] += SHIFT_HOURS
        shifts_by_worker[worker['id']].append(slot['start'])
        assignments.append({"worker_id": worker['id'], "department": slot['department'], "day": slot['day']+1, "shift": slot['shift'], "start_hour": SHIFTS[[s['name'] for s in SHIFTS].index(slot['shift'])]['start'], "end_hour": SHIFTS[[s['name'] for s in SHIFTS].index(slot['shift'])]['end']})
    totals = {}
    for item in shortages:
        key = (item['department'], item['shift'])
        totals[key] = totals.get(key, 0) + item['outside_staff_needed']
    return {"scenario": "Medium", "window_days": 7, "assignments": assignments, "shortages": shortages,
            "outside_staff_by_department_shift": [{"department": d, "shift": s, "outside_staff_needed": n} for (d,s),n in sorted(totals.items())],
            "coverage": {"required_shift_slots": len(slots), "assigned_shift_slots": len(assignments), "outside_staff_needed": len(shortages)},
            "constraints": {"shift_hours": SHIFT_HOURS, "minimum_rest_hours": MIN_REST_HOURS, "weekly_caps": {w['id']: w['weekly_cap'] for w in WORKERS}, "rounding": "For each department and fixed 8-hour block, use the maximum integer hourly seat requirement in that block; no additional rounding.", "strategy": "Deterministic greedy assignment: least scheduled hours first, then stable worker ID."},
            "roster_label": "Synthetic worker roster"}
