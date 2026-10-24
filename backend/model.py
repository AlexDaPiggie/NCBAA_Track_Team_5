"""Transparent synthetic demand baseline and finite-horizon discrete-event model."""
import math
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import simpy

DATA = Path(__file__).parent / 'data'
HORIZON = 7 * 24 * 60
SHIFT_HOURS = 8
SHIFT_BLOCKS = ((0, 8), (8, 16), (16, 24))

@dataclass
class Department:
    minutes: float
    minimum: int
    wage: float
    utilization: float = .8
    target_wait: float = 10

DEFAULTS = {'Passenger Services': Department(5, 1, 26),
            'Ramp Operations': Department(24, 2, 32),
            'Fuel Services': Department(30, 1, 35)}

def forecast(scenario='Medium', multiplier=1.0):
    """Planning profile, not a trained model or real event forecast.
    hourly_demand : {hour, day, clocktime, aircraftarrivals, passengers, fuelneeded, datatype}
    """

    factor = {'Low': .65, 'Medium': 1., 'High': 1.5}[scenario] * multiplier
    hourly_demand = []
    for hour in range(168):
        day, clock = divmod(hour, 24)
        arrivals = factor * (1.2 + 4 * math.exp(-((clock-11)/3)**2)
                             + 5 * math.exp(-((clock-18)/3)**2)) * [1,1.1,1.2,1.4,1.8,2,1.5][day]
        hourly_demand.append(dict(hour=hour, day=day+1, clock=clock, aircraft=round(arrivals,2),
                                  passengers=round(arrivals*4.5,2), fuel_requests=round(arrivals*.65,2),
                                  provenance='synthetic planning baseline'))
    return hourly_demand

def historical_forecast(scenario='Medium', multiplier=1.0, seed=42):
    """Build a seven-day LAX arrival profile from Feb 7-13, 2022 flight records."""
    factor = {'Low': .65, 'Medium': 1., 'High': 1.5}[scenario] * multiplier
    source = pd.read_csv(DATA/'lax_super_bowl_week.csv', usecols=[
        'FL_DATE', 'DEST', 'ARR_TIME', 'CANCELLED', 'DIVERTED'])
    source = source.loc[
        source['DEST'].eq('LAX')
        & source['CANCELLED'].eq(0)
        & source['DIVERTED'].eq(0)
    ].copy()
    source['date'] = pd.to_datetime(source['FL_DATE'], format='%Y-%m-%d', errors='raise')
    arrival = pd.to_numeric(source['ARR_TIME'], errors='coerce')
    hour = (arrival // 100).astype('Int64')
    minute = (arrival % 100).astype('Int64')
    valid_time = hour.between(0, 23).fillna(False) & minute.between(0, 59).fillna(False)
    source = source.loc[valid_time].copy()
    source['arrival_minute'] = (hour.loc[valid_time] * 60 + minute.loc[valid_time]).astype(int)
    source = source.loc[source['date'].between('2022-02-07', '2022-02-13')]

    rng = np.random.default_rng(seed)
    rows = []
    for day in range(7):
        date = pd.Timestamp('2022-02-07') + pd.Timedelta(days=day)
        day_flights = source.loc[source['date'].eq(date)]
        for clock in range(24):
            observed = day_flights.loc[
                (day_flights['arrival_minute'] // 60).eq(clock), 'arrival_minute'
            ].to_numpy(dtype=int)
            target = int(round(len(observed) * factor))
            if target <= len(observed):
                scaled = np.sort(rng.choice(observed, size=target, replace=False)) if target else np.array([], dtype=int)
            else:
                extra = rng.choice(observed, size=target-len(observed), replace=True)
                extra = (clock * 60 + rng.uniform(0, 60, size=len(extra))).astype(int)
                scaled = np.sort(np.concatenate((observed, extra)))
            aircraft = len(scaled)
            rows.append(dict(hour=day*24+clock, day=day+1, clock=clock,
                date=date.strftime('%Y-%m-%d'), aircraft=aircraft,
                passengers=round(aircraft*4.5, 2), fuel_requests=round(aircraft*.65, 2),
                observed_aircraft=len(observed), flight_arrivals=(scaled % 60).tolist(),
                provenance='Historical LAX inbound flight arrivals, Feb 7-13 2022; passenger/fuel counts estimated'))
    return rows

def requirements(hourly_demand, config):
    result = []
    for hour_data in hourly_demand:
        for name, dept in config.items():
            demand = hour_data[{'Passenger Services':'passengers','Ramp Operations':'aircraft','Fuel Services':'fuel_requests'}[name]]
            workload = demand * dept.minutes
            staff = max(dept.minimum, math.ceil(workload / (60*dept.utilization)))
            result.append(dict(hour=hour_data['hour'], department=name, demand=demand,
                               workload_minutes=round(workload,2), required=staff,
                               next_staff_threshold=round(staff*60*dept.utilization/dept.minutes,2)))
    return result

def requests(hourly_demand, seed, config):
    rng = np.random.default_rng(seed)
    jobs = {name: [] for name in config}
    for hour_data in hourly_demand:
        if 'flight_arrivals' in hour_data:
            arrivals = [hour_data['hour']*60 + minute for minute in hour_data['flight_arrivals']]
        else:
            arrivals = [hour_data['hour']*60 + rng.uniform(0,60)
                        for _ in range(rng.poisson(hour_data['aircraft']))]
        for arrival in arrivals:
            people = rng.poisson(hour_data['passengers']/max(hour_data['aircraft'],.001))
            for _ in range(people):
                jobs['Passenger Services'].append((arrival, rng.triangular(.6,1,1.4)*config['Passenger Services'].minutes))
            jobs['Ramp Operations'].append((arrival, rng.triangular(.6,1,1.4)*config['Ramp Operations'].minutes))
            if rng.random() < min(1,hour_data['fuel_requests']/max(hour_data['aircraft'],.001)):
                jobs['Fuel Services'].append((arrival, rng.triangular(.6,1,1.4)*config['Fuel Services'].minutes))
    return {name: sorted(values) for name, values in jobs.items()}

def simulate(jobs, staffing, config, include_trace=False):
    results = []
    traces = {}
    for name, tasks in jobs.items():
        dept = config[name]
        department_staffing = staffing[name]
        if isinstance(department_staffing, dict):
            shift_staffing = department_staffing
        else:
            shift_staffing = {f'{start:02d}-{end:02d}': department_staffing
                              for start, end in SHIFT_BLOCKS}
        if set(shift_staffing) != {f'{start:02d}-{end:02d}' for start, end in SHIFT_BLOCKS}:
            raise ValueError(f'{name} must provide staffing for all three 8-hour shifts')
        if any(count < dept.minimum for count in shift_staffing.values()):
            raise ValueError(f'{name} requires at least {dept.minimum} qualified employees')
        shift_hours = sum(shift_staffing.values()) * SHIFT_HOURS * 7
        waits, completed, busy = [], [], [0.]
        events = []
        env = simpy.Environment()
        queue = simpy.Store(env)

        def arrive(job_id, arrival, duration):
            yield env.timeout(arrival)
            yield queue.put((job_id, arrival, duration))

        def work(shift_start, shift_end, seat):
            yield env.timeout(shift_start)
            while env.now < shift_end:
                request = queue.get()
                shift_close = env.timeout(shift_end - env.now)
                outcome = yield request | shift_close
                if request not in outcome:
                    request.cancel()
                    break
                if env.now >= shift_end:
                    yield queue.put(outcome[request])
                    break
                job_id, arrival, duration = outcome[request]
                start = env.now
                end = start + duration
                if include_trace:
                    events.append(dict(id=job_id, arrival=arrival, start=start,
                                       end=end, seat=seat, seat_number=seat))
                waits.append(start - arrival)
                busy[0] += max(0, min(end, HORIZON) - min(start, HORIZON))
                yield env.timeout(duration)
                completed.append(env.now)

        for job_id, (arrival, duration) in enumerate(sorted(tasks, key=lambda task: task[0])):
            env.process(arrive(job_id, arrival, duration))
        daily_capacity = sum(shift_staffing.values()) * SHIFT_HOURS * 60
        drain_days = math.ceil(sum(duration for _, duration in tasks) / daily_capacity) + 2
        for day in range(7 + drain_days):
            for start_hour, end_hour in SHIFT_BLOCKS:
                shift_name = f'{start_hour:02d}-{end_hour:02d}'
                shift_start = day * 24 * 60 + start_hour * 60
                shift_end = day * 24 * 60 + end_hour * 60
                for seat in range(shift_staffing[shift_name]):
                    env.process(work(shift_start, shift_end, seat))
        env.run()
        if include_trace:
            traces[name] = events
        results.append(dict(department=name, staff=max(shift_staffing.values()),
                            shift_staffing=shift_staffing,
                            cost=shift_hours*dept.wage,
                            average_wait=round(float(np.mean(waits)) if waits else 0,2),
                            utilization=round(busy[0]/(shift_hours*60),4),
                            service_level=round(sum(w<=dept.target_wait for w in waits)/max(1,len(waits)),4),
                            requests=len(tasks), delayed=sum(w>dept.target_wait for w in waits),
                            unfinished_at_close=sum(t>HORIZON for t in completed)))
    total = sum(r['requests'] for r in results)
    return dict(departments=results, **({'traces':traces} if include_trace else {}), cost=sum(r['cost'] for r in results),
                average_wait=round(sum(r['average_wait']*r['requests'] for r in results)/max(1,total),2),
                service_level=round(sum(r['service_level']*r['requests'] for r in results)/max(1,total),4),
                unfinished_at_close=sum(r['unfinished_at_close'] for r in results))

def run(scenario='Medium', multiplier=1., seed=42, config=None, custom=None, forecast_mode='baseline'):
    config = config or DEFAULTS
    if forecast_mode not in ('baseline', 'trained', 'historical'):
        raise ValueError(f'Unknown forecast mode: {forecast_mode}')
    hourly_demand = (historical_forecast(scenario, multiplier, seed)
                     if forecast_mode == 'historical' else forecast(scenario, multiplier))
    training_report = None
    if forecast_mode == 'trained':
        from .training import predict
        values, training_report = predict(hourly_demand)
        factor = {'Low':.65,'Medium':1.,'High':1.5}[scenario]*multiplier
        for hour_data, prediction in zip(hourly_demand,values):
            for key, value in zip(['aircraft','passengers','fuel_requests'],prediction):
                hour_data[key] = round(float(value)*factor,2)
            hour_data['provenance'] = 'trained regression on synthetic history; scenario scaling is an assumption'
    needs = requirements(hourly_demand, config)
    jobs = requests(hourly_demand, seed, config)
    options = []
    for label, quantile in [('Cost-Focused',.5),('Balanced',.85),('Service-Focused',1.)]:
        shift_staffing = {}
        for name, dept in config.items():
            shift_staffing[name] = {}
            for start, end in SHIFT_BLOCKS:
                shift_name = f'{start:02d}-{end:02d}'
                block_needs = [row['required'] for row in needs
                               if row['department'] == name and row['hour'] % 24 in range(start, end)]
                shift_staffing[name][shift_name] = max(
                    dept.minimum, math.ceil(float(np.quantile(block_needs, quantile))))
        staffing = {name: max(shifts.values()) for name, shifts in shift_staffing.items()}
        options.append(dict(name=label, staffing=staffing, shift_staffing=shift_staffing,
                            **simulate(jobs,shift_staffing,config)))
    if custom:
        custom_shifts = {name: {f'{start:02d}-{end:02d}': count
                                for start, end in SHIFT_BLOCKS}
                         for name, count in custom.items()}
        options.append(dict(name='Manager Plan', staffing=custom, shift_staffing=custom_shifts,
                            **simulate(jobs,custom_shifts,config)))
    return dict(forecast=hourly_demand, requirements=needs, options=options, seed=seed,
                assumptions={name:asdict(dept) for name,dept in config.items()},
                training_report=training_report, forecast_mode=forecast_mode,
                provenance=(
                    'Historical LAX inbound flight records from Feb 7-13, 2022; airport-wide counts, not FBO activity. Passenger and fuel requests are estimates.'
                    if forecast_mode == 'historical' else
                    'Synthetic history; trained regression demo, not real-world validated'
                    if training_report else
                    'Synthetic data; transparent planning profile, not trained ML'))

def generate_data():
    DATA.mkdir(exist_ok=True)
    pd.DataFrame(forecast()).to_csv(DATA/'synthetic_hourly_demand.csv',index=False)
    pd.DataFrame([dict(employee_id=f'{i}-{j}',qualification=name,available_hours=40,
                       hourly_wage=dept.wage,provenance='synthetic')
                  for i,(name,dept) in enumerate(DEFAULTS.items()) for j in range(30)]).to_csv(DATA/'synthetic_employees.csv',index=False)
    pd.DataFrame([dict(department=name,arrival_minute=a,service_minutes=d,provenance='synthetic')
                  for name,tasks in requests(forecast(),42,DEFAULTS).items() for a,d in tasks]).to_csv(DATA/'synthetic_requests.csv',index=False)

if __name__ == '__main__':
    generate_data()
