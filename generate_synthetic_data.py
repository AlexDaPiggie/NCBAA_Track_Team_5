"""
generate_synthetic_data.py
Synthetic data for the fictional LAX FBO staffing planner ("Pacific Gateway Aviation").

EVERYTHING in this file is invented. Workers are anonymous IDs. Rates, ratios, ground
times and fuel amounts are ASSUMPTIONS, not measurements. Run it again with the same
seed and you get identical files; change SEED to get a different synthetic workforce.

Time model: 7 days (0-6) x 6 four-hour blocks per day:
  block 0 = 00:00-04:00, 1 = 04:00-08:00, 2 = 08:00-12:00,
  block 3 = 12:00-16:00, 4 = 16:00-20:00, 5 = 20:00-24:00
Peak blocks = 1-4 (04:00-20:00). Off-peak blocks = 0 and 5.
"""
import csv
import os
import random
from collections import defaultdict

SEED = 42
random.seed(SEED)
OUT = os.path.dirname(os.path.abspath(__file__))

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Shift patterns = two consecutive 4-hour blocks (an 8-hour shift)
PATTERNS = {"early": [1, 2], "day": [2, 3], "swing": [3, 4], "evening": [4, 5], "night": [0, 1]}
# Handing out patterns round-robin inside each role keeps coverage spread across the day
PATTERN_CYCLE = ["day", "early", "swing", "evening", "night", "day", "swing", "early"]

# role -> zone, headcount, hourly pay range, certifications the role requires,
# and the roles a worker of this role can be cross-trained to cover
ROLES = {
    "line_service_tech": dict(zone="Ramp", n=12, rate=(22, 30), fixed_ft=False,
                              certs=["RAMP_DRIVING", "AIRCRAFT_MARSHALLING"],
                              cross=["fueler", "hangar_tow_operator"]),
    "ramp_supervisor": dict(zone="Ramp", n=4, rate=(34, 42), fixed_ft=True,
                            certs=["RAMP_DRIVING", "AIRCRAFT_MARSHALLING", "TOWING"],
                            cross=["line_service_tech", "fueler"]),
    "fueler": dict(zone="Fuel", n=8, rate=(24, 32), fixed_ft=False,
                   certs=["FUELING", "RAMP_DRIVING"],
                   cross=["line_service_tech"]),
    "fuel_safety_lead": dict(zone="Fuel", n=2, rate=(36, 44), fixed_ft=True,
                             certs=["FUELING", "RAMP_DRIVING", "FUEL_SAFETY_LEAD"],
                             cross=["fueler"]),
    "customer_service_rep": dict(zone="Customer service", n=6, rate=(20, 26), fixed_ft=False,
                                 certs=[],
                                 cross=["concierge", "dispatcher"]),
    "concierge": dict(zone="Customer service", n=3, rate=(22, 28), fixed_ft=False,
                      certs=["GROUND_TRANSPORT_COORD"],
                      cross=["customer_service_rep"]),
    "duty_manager": dict(zone="Operations", n=4, rate=(42, 55), fixed_ft=True,
                         certs=["DUTY_MANAGER"],
                         cross=["dispatcher"]),
    "dispatcher": dict(zone="Operations", n=4, rate=(28, 36), fixed_ft=False,
                       certs=[],
                       cross=["customer_service_rep"]),
    "access_control_agent": dict(zone="Access control", n=5, rate=(23, 30), fixed_ft=False,
                                 certs=["SECURITY_ESCORT", "RAMP_ACCESS"],
                                 cross=["customer_service_rep", "international_arrivals_coordinator"]),
    "international_arrivals_coordinator": dict(zone="Customs support", n=3, rate=(28, 36), fixed_ft=False,
                                               certs=["CUSTOMS_ACCESS"],
                                               cross=["access_control_agent", "customer_service_rep"]),
    "hangar_tow_operator": dict(zone="Hangar", n=4, rate=(24, 32), fixed_ft=False,
                                certs=["TOWING", "RAMP_DRIVING"],
                                cross=["line_service_tech"]),
}


def pick_secondaries(role):
    """Choose 0-2 roles this worker is cross-trained for."""
    options = ROLES[role]["cross"]
    k = min(random.choice([0, 1, 1, 2]), len(options))
    return random.sample(options, k)


def build_certs(role, secondaries):
    """A worker holds the certs of their own role plus the certs of every role they cover."""
    certs = set(ROLES[role]["certs"])
    for r in secondaries:
        certs |= set(ROLES[r]["certs"])
    return sorted(certs)


def money(x):
    return round(x * 4) / 4  # nearest 25 cents


def write_csv(name, rows, fields):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


# ---------------------------------------------------------------- 1. workers + baseline schedule
# How many people an ordinary week should have on duty, per role and block (0..5).
# These are the targets the scheduler tries to meet. They are ASSUMPTIONS.
TARGETS = {
    "line_service_tech": [1, 2, 3, 3, 2, 1],
    "ramp_supervisor": [0, 1, 1, 1, 1, 0],
    "fueler": [0, 1, 2, 2, 2, 0],
    "fuel_safety_lead": [0, 0, 1, 1, 0, 0],
    "customer_service_rep": [0, 1, 1, 2, 1, 0],
    "concierge": [0, 0, 1, 1, 1, 0],
    "duty_manager": [0, 1, 1, 1, 1, 0],
    "dispatcher": [0, 0, 1, 1, 1, 0],
    "access_control_agent": [0, 1, 1, 1, 1, 0],
    "international_arrivals_coordinator": [0, 0, 0, 1, 1, 0],
    "hangar_tow_operator": [0, 0, 1, 1, 1, 0],
}

people = [dict(role=r) for r, info in ROLES.items() for _ in range(info["n"])]
for p in people:  # employment type, cross-training, contract hours
    info = ROLES[p["role"]]
    p["full_time"] = info["fixed_ft"] or random.random() < 0.65
    p["secondaries"] = pick_secondaries(p["role"])
    p["contracted"] = 40 if p["full_time"] else random.choice([16, 20, 24])


def candidates(p):
    """Every weekly pattern this worker could plausibly work: list of (label, days, blocks)."""
    options = []
    if p["full_time"]:  # 5 days on, 2 consecutive days off, one 8-hour pattern
        for label, blocks in PATTERNS.items():
            for off in range(7):
                days = [d for d in range(7) if d not in (off, (off + 1) % 7)]
                options.append((label, days, blocks))
    else:  # a single 4-hour block on N consecutive days
        n_days = p["contracted"] // 4
        for blk in (2, 3, 4, 5):
            for start in range(7):
                options.append(("single_block", [(start + j) % 7 for j in range(n_days)], [blk]))
    return options


# Greedy scheduling: for each worker, pick the option that fills the most still-uncovered
# (day, block) slots for their role. Full-time first (they are the backbone), then part-time.
cover = defaultdict(int)  # (role, day, block) -> people scheduled
random.shuffle(people)
for p in sorted(people, key=lambda q: not q["full_time"]):
    best, best_gain = [], -1
    for opt in candidates(p):
        _, days, blocks = opt
        gain = sum(1 for d in days for b in blocks if cover[(p["role"], d, b)] < TARGETS[p["role"]][b])
        if gain > best_gain:
            best, best_gain = [opt], gain
        elif gain == best_gain:
            best.append(opt)
    p["label"], p["days"], p["blocks"] = random.choice(best)
    for d in p["days"]:
        for b in p["blocks"]:
            cover[(p["role"], d, b)] += 1

random.shuffle(people)  # so IDs do not group by role
workers, schedule = [], []
for num, p in enumerate(people, start=1):
    role = p["role"]
    info = ROLES[role]
    wid = f"W-{num:03d}"
    work_days, blocks = p["days"], p["blocks"]
    for d in work_days:
        for b in blocks:
            schedule.append(dict(worker_id=wid, day_index=d, day_name=DAY_NAMES[d], block=b,
                                 zone=info["zone"], role=role, scheduled_hours=4))
    scheduled = 4 * len(work_days) * len(blocks)

    r = random.random()
    if r < 0.40:
        ot, max_extra = "yes", random.choice([12, 16])
    elif r < 0.75:
        ot, max_extra = "limited", random.choice([4, 8])
    else:
        ot, max_extra = "no", 0

    reg = money(random.uniform(*info["rate"]))
    bump = random.choice([8, 8, 4]) if random.random() < 0.10 else 0  # a few ran long last week
    time_off = str(random.choice(sorted(work_days))) if random.random() < 0.12 else ""

    workers.append(dict(
        worker_id=wid,
        primary_role=role,
        primary_zone=info["zone"],
        secondary_roles=";".join(p["secondaries"]),
        secondary_zones=";".join(sorted({ROLES[s]["zone"] for s in p["secondaries"]})),
        certifications=";".join(build_certs(role, p["secondaries"])),
        employment_type="full-time" if p["full_time"] else "part-time",
        contracted_weekly_hours=p["contracted"],
        scheduled_hours_this_week=scheduled,
        shift_pattern=p["label"],
        usual_blocks=";".join(map(str, blocks)),
        days_off=";".join(DAY_NAMES[d] for d in range(7) if d not in work_days),
        game_week_approved_time_off_days=time_off,
        overtime_willing=ot,
        max_extra_hours_per_week=max_extra,
        convert_to_full_time_willing="n/a" if p["full_time"] else random.choice(["yes", "no"]),
        hours_last_7_days=scheduled + bump,
        regular_rate_usd_hr=reg,
        overtime_rate_usd_hr=round(reg * 1.5, 2),
    ))

workers.sort(key=lambda w: w["worker_id"])
write_csv("workers.csv", workers, list(workers[0].keys()))
write_csv("baseline_schedule.csv", schedule,
          ["worker_id", "day_index", "day_name", "block", "zone", "role", "scheduled_hours"])

# ---------------------------------------------------------------- 2. reserve pool
reserve_plan = [("line_service_tech", 6), ("fueler", 3), ("customer_service_rep", 2), ("concierge", 1),
                ("access_control_agent", 2), ("international_arrivals_coordinator", 1),
                ("hangar_tow_operator", 1), ("dispatcher", 1), ("ramp_supervisor", 1)]
reserves = []
n = 0
for role, count in reserve_plan:
    for _ in range(count):
        n += 1
        agency = random.random() < 0.5
        sec = pick_secondaries(role)
        base = money(random.uniform(*ROLES[role]["rate"]))
        premium = round(random.uniform(1.40, 1.70) if agency else random.uniform(1.15, 1.45), 2)
        reserves.append(dict(
            reserve_id=f"R-{n:02d}",
            pool_type="staffing_agency" if agency else "internal_on_call",
            primary_role=role,
            primary_zone=ROLES[role]["zone"],
            secondary_roles=";".join(sec),
            certifications=";".join(build_certs(role, sec)),
            lead_time_hours=random.choice([6, 12, 24, 24, 48]),
            show_probability=round(random.uniform(0.85, 0.98), 2),
            base_rate_usd_hr=base,
            premium_multiplier=premium,
            effective_rate_usd_hr=round(base * premium, 2),
            min_shift_hours=random.choice([4, 8]),
            max_hours_in_window=random.choice([32, 40]),
            available_days=";".join(str(d) for d in sorted(random.sample(range(7), random.randint(4, 7)))),
        ))
write_csv("reserve_pool.csv", reserves, list(reserves[0].keys()))

# ---------------------------------------------------------------- 3. staffing ratios (ASSUMPTIONS)
ratios = [
    # zone, role, workload driver, capacity per staff per block, min peak, min off-peak
    # A floor of 0 means "workload-driven": the formula still gives at least 1 whenever workload > 0.
    ("Ramp", "line_service_tech", "movements x workload_multiplier", 4, 2, 1),
    ("Ramp", "ramp_supervisor", "movements", 12, 1, 0),
    ("Fuel", "fueler", "fuel_requests", 5, 0, 0),
    ("Fuel", "fuel_safety_lead", "fuel_requests", 15, 0, 0),
    ("Customer service", "customer_service_rep", "movements", 6, 1, 0),
    ("Customer service", "concierge", "ground_transport_requests", 8, 0, 0),
    ("Operations", "duty_manager", "movements", 30, 1, 0),
    ("Operations", "dispatcher", "movements", 20, 0, 0),
    ("Access control", "access_control_agent", "movements", 10, 1, 0),
    ("Customs support", "international_arrivals_coordinator", "international_movements", 3, 0, 0),
    ("Hangar", "hangar_tow_operator", "hangar_tows", 5, 0, 0),
]
write_csv("staffing_ratios.csv",
          [dict(zone=z, role=r, workload_driver=d, capacity_per_staff_per_block=c,
                min_staff_peak_blocks_1_to_4=mp, min_staff_offpeak_blocks_0_and_5=mo,
                required_staff_formula="max(minimum, ceil(workload / capacity))")
           for z, r, d, c, mp, mo in ratios],
          ["zone", "role", "workload_driver", "capacity_per_staff_per_block",
           "min_staff_peak_blocks_1_to_4", "min_staff_offpeak_blocks_0_and_5", "required_staff_formula"])

# ---------------------------------------------------------------- 4. aircraft mix (ASSUMPTIONS)
mix = [
    ("turboprop_piston", "King Air 350; Pilatus PC-12", 0.10, 0.02, 4, 18, 180, 0.8),
    ("light_jet", "Citation CJ3; Phenom 300", 0.25, 0.05, 5, 24, 350, 0.9),
    ("midsize_jet", "Citation Latitude; Praetor 500", 0.30, 0.10, 6, 30, 650, 1.0),
    ("large_cabin_jet", "Gulfstream G450; Challenger 650; Falcon 900", 0.25, 0.30, 7, 36, 1400, 1.3),
    ("ultra_long_range_jet", "Gulfstream G650; Global 7500", 0.10, 0.60, 8, 48, 2600, 1.6),
]
write_csv("aircraft_mix.csv",
          [dict(aircraft_class=a, example_types=e, share_of_arrivals=s, share_international=i,
                baseline_ground_time_hrs=g, event_ground_time_hrs=eg, avg_fuel_uplift_gal=f,
                workload_multiplier=m) for a, e, s, i, g, eg, f, m in mix],
          ["aircraft_class", "example_types", "share_of_arrivals", "share_international",
           "baseline_ground_time_hrs", "event_ground_time_hrs", "avg_fuel_uplift_gal", "workload_multiplier"])

# ---------------------------------------------------------------- 5. scenarios (lift values are PLACEHOLDERS)
scen = [
    ("low", 1.3, 1.00, 1.0, 1.00),
    ("medium", 1.8, 1.15, 1.2, 1.10),
    ("high", 2.5, 1.30, 1.5, 1.25),
]
write_csv("scenario_parameters.csv",
          [dict(scenario=s, arrivals_lift_vs_baseline=l, lift_source="PLACEHOLDER - replace with value derived from 2022 data",
                ground_time_multiplier=g, international_share_multiplier=i, fuel_uplift_multiplier=f)
           for s, l, g, i, f in scen],
          ["scenario", "arrivals_lift_vs_baseline", "lift_source", "ground_time_multiplier",
           "international_share_multiplier", "fuel_uplift_multiplier"])

# ---------------------------------------------------------------- 6. global constraints + workload rates
glob = [
    ("constraint", "max_consecutive_hours", 12, "hours", "Hard limit on one continuous stretch of work"),
    ("constraint", "min_rest_between_shifts", 8, "hours", "Hard limit"),
    ("constraint", "max_weekly_hours", 60, "hours", "Hard cap including overtime"),
    ("constraint", "meal_break_required_after", 6, "hours", "Break must fit inside the shift"),
    ("constraint", "overtime_multiplier", 1.5, "x regular rate", "Applied above 40 h/week here; check daily-overtime rules before costing"),
    ("workload", "fuel_requests_per_departure", 0.85, "requests", "Share of departures that buy fuel at this FBO"),
    ("workload", "ground_transport_requests_per_arrival", 0.80, "requests", "Arrivals needing a car or crew transport"),
    ("workload", "hangar_tows_per_movement", 0.15, "tows", "Aircraft towed into or out of the hangar"),
    ("workload", "departures_per_arrival", 1.0, "ratio", "Over a full window, departures balance arrivals; timing is offset by ground time"),
]
write_csv("global_assumptions.csv",
          [dict(category=c, parameter=p, value=v, unit=u, note=n) for c, p, v, u, n in glob],
          ["category", "parameter", "value", "unit", "note"])

# ---------------------------------------------------------------- coverage check on the baseline
print("\nBaseline check: (day, block) slots below the ordinary-week target, per role")
for role in ROLES:
    short = sum(1 for d in range(7) for b in range(6) if cover[(role, d, b)] < TARGETS[role][b])
    total = sum(1 for d in range(7) for b in range(6) if TARGETS[role][b] > 0)
    print(f"  {role:36s} {short:2d} of {total} target slots short")
