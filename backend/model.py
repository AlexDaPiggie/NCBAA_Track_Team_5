"""Transparent synthetic demand baseline and finite-horizon discrete-event model."""
import math
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import simpy

DATA = Path(__file__).parent / 'data'
HORIZON = 7 * 24 * 60

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

SCENARIO_MULTIPLIERS = {'Low': 1.15, 'Medium': 1.4, 'High': 1.7}

def forecast(scenario='Medium', multiplier=1.0, week_type='event', scenario_multipliers=None):
    """Synthetic planning profile; event multipliers are assumptions, not forecasts."""
    if week_type not in ('ordinary', 'event'):
        raise ValueError('week_type must be ordinary or event')
    factors = scenario_multipliers or SCENARIO_MULTIPLIERS
    factor = (1.0 if week_type == 'ordinary' else factors[scenario]) * multiplier
    rows = []
    for hour in range(168):
        day, clock = divmod(hour, 24)
        arrivals = factor * (1.2 + 4 * math.exp(-((clock-11)/3)**2)
                             + 5 * math.exp(-((clock-18)/3)**2)) * [1,1.1,1.2,1.4,1.8,2,1.5][day]
        rows.append(dict(hour=hour, day=day+1, clock=clock, aircraft=round(arrivals,2),
                         passengers=round(arrivals*4.5,2), fuel_requests=round(arrivals*.65,2),
                         provenance='synthetic planning baseline'))
    return rows


def uploaded_profile(ordinary_demand, factor=1.0):
    """Scale supplied aggregate counts; uploaded provenance is not independently verified."""
    return [dict(hour=row['hour'], day=row['hour']//24+1, clock=row['hour'] % 24,
                 **{key: round(row[key]*factor, 2) for key in ('aircraft', 'passengers', 'fuel_requests')},
                 provenance='uploaded ordinary-week counts; any event scaling is a planning assumption')
            for row in sorted(ordinary_demand, key=lambda item: item['hour'])]

def requirements(rows, config):
    result = []
    for row in rows:
        for name, dept in config.items():
            demand = row[{'Passenger Services':'passengers','Ramp Operations':'aircraft','Fuel Services':'fuel_requests'}[name]]
            workload = demand * dept.minutes
            staff = max(dept.minimum, math.ceil(workload / (60*dept.utilization)))
            result.append(dict(hour=row['hour'], department=name, demand=demand,
                               workload_minutes=round(workload,2), required=staff,
                               next_staff_threshold=round(staff*60*dept.utilization/dept.minutes,2)))
    return result

def requests(rows, seed, config):
    rng = np.random.default_rng(seed)
    jobs = {name: [] for name in config}
    for row in rows:
        for _ in range(rng.poisson(row['aircraft'])):
            arrival = row['hour']*60 + rng.uniform(0,60)
            people = rng.poisson(row['passengers']/max(row['aircraft'],.001))
            for _ in range(people):
                jobs['Passenger Services'].append((arrival, rng.triangular(.6,1,1.4)*config['Passenger Services'].minutes))
            jobs['Ramp Operations'].append((arrival, rng.triangular(.6,1,1.4)*config['Ramp Operations'].minutes))
            if rng.random() < min(1,row['fuel_requests']/max(row['aircraft'],.001)):
                jobs['Fuel Services'].append((arrival, rng.triangular(.6,1,1.4)*config['Fuel Services'].minutes))
    return {name: sorted(values) for name, values in jobs.items()}

def simulate(jobs, staffing, config, include_trace=False):
    results = []
    traces = {}
    for name, tasks in jobs.items():
        dept, count = config[name], staffing[name]
        if count < dept.minimum:
            raise ValueError(f'{name} requires at least {dept.minimum} qualified employees')
        env = simpy.Environment()
        resource = simpy.Resource(env, capacity=count)
        waits, completed, busy = [], [], [0.]
        events = []
        free_seats = list(range(count))
        def serve(job_id, arrival, duration):
            yield env.timeout(arrival)
            with resource.request() as request:
                yield request
                start = env.now
                seat = free_seats.pop(0)
                if include_trace:
                    events.append(dict(id=job_id, arrival=arrival, start=start, end=start+duration, seat=seat))
                waits.append(start-arrival)
                busy[0] += max(0, min(duration, HORIZON-start))
                yield env.timeout(duration)
                completed.append(env.now)
                free_seats.append(seat)
                free_seats.sort()
        for job_id, (arrival, duration) in enumerate(tasks):
            env.process(serve(job_id,arrival,duration))
        env.run()  # Drain queues; explicitly report requests unfinished at week end.
        if include_trace:
            traces[name] = events
        results.append(dict(department=name, staff=count, cost=count*168*dept.wage,
                            average_wait=round(float(np.mean(waits)) if waits else 0,2),
                            utilization=round(busy[0]/(count*HORIZON),4),
                            service_level=round(sum(w<=dept.target_wait for w in waits)/max(1,len(waits)),4),
                            requests=len(tasks), delayed=sum(w>dept.target_wait for w in waits),
                            unfinished_at_close=sum(t>HORIZON for t in completed)))
    total = sum(r['requests'] for r in results)
    return dict(departments=results, **({'traces':traces} if include_trace else {}), cost=sum(r['cost'] for r in results),
                average_wait=round(sum(r['average_wait']*r['requests'] for r in results)/max(1,total),2),
                service_level=round(sum(r['service_level']*r['requests'] for r in results)/max(1,total),4),
                unfinished_at_close=sum(r['unfinished_at_close'] for r in results))

def scenario_summary(multiplier=1.0, config=None, forecast_mode='baseline', proxy_scale=.25,
                     scenario_multipliers=None, ordinary_demand=None):
    """Compact, reproducible comparison of ordinary demand and three event cases."""
    config = config or DEFAULTS
    factors = scenario_multipliers or SCENARIO_MULTIPLIERS
    ordinary = forecast('Medium', multiplier, 'ordinary', factors)
    if forecast_mode == 'uploaded':
        ordinary = uploaded_profile(ordinary_demand, multiplier)
    if forecast_mode == 'trained':
        from .training import predict
        values, _ = predict(ordinary)
        for row, prediction in zip(ordinary, values):
            for key, value in zip(['aircraft','passengers','fuel_requests'], prediction):
                row[key] = round(float(value)*multiplier, 2)
    elif forecast_mode == 'real_proxy':
        from .real_training import predict
        values, _ = predict()
        for row, value in zip(ordinary, values):
            aircraft = float(value)*multiplier*proxy_scale
            row.update(aircraft=round(aircraft,2), passengers=round(aircraft*4.5,2),
                       fuel_requests=round(aircraft*.65,2))
    summaries = []
    for scenario in ('Low', 'Medium', 'High'):
        rows = forecast(scenario, multiplier, 'event', factors)
        factor = factors[scenario] * multiplier
        if forecast_mode == 'uploaded':
            rows = uploaded_profile(ordinary_demand, factor)
        if forecast_mode == 'trained':
            values, _ = predict(rows)
            for row, prediction in zip(rows, values):
                for key, value in zip(['aircraft','passengers','fuel_requests'], prediction):
                    row[key] = round(float(value)*factor, 2)
        elif forecast_mode == 'real_proxy':
            values, _ = predict()
            for row, value in zip(rows, values):
                aircraft = float(value)*factor*proxy_scale
                row.update(aircraft=round(aircraft,2), passengers=round(aircraft*4.5,2),
                           fuel_requests=round(aircraft*.65,2))
        needs = requirements(rows, config)
        summaries.append(dict(
            scenario=scenario,
            total_aircraft=round(sum(r['aircraft'] for r in rows)),
            peak_aircraft_per_hour=round(max(r['aircraft'] for r in rows), 1),
            peak_seats={name: max(x['required'] for x in needs if x['department'] == name)
                        for name in config},
            event_multiplier=factors[scenario],
            effective_multiplier=factor,
        ))
    return dict(
        ordinary_total_aircraft=round(sum(r['aircraft'] for r in ordinary)),
        ordinary_peak_aircraft_per_hour=round(max(r['aircraft'] for r in ordinary), 1),
        scenarios=summaries,
        provenance=f'{forecast_mode} planning profile; event multipliers are demo assumptions.',
    )


def run(scenario='Medium', multiplier=1., seed=42, config=None, custom=None, forecast_mode='baseline',proxy_scale=.25, scenario_multipliers=None, ordinary_demand=None, include_queue_options=True):
    config = config or DEFAULTS
    factors = scenario_multipliers or SCENARIO_MULTIPLIERS
    rows = forecast(scenario, multiplier, 'event', factors)
    training_report = None
    if forecast_mode == 'uploaded':
        rows = uploaded_profile(ordinary_demand, factors[scenario]*multiplier)
    if forecast_mode == 'trained':
        from .training import predict
        values, training_report = predict(rows)
        factor = factors[scenario]*multiplier
        for row, prediction in zip(rows,values):
            for key, value in zip(['aircraft','passengers','fuel_requests'],prediction):
                row[key] = round(float(value)*factor,2)
            row['provenance'] = 'trained regression on synthetic history; scenario scaling is an assumption'
    if forecast_mode == 'real_proxy':
        from .real_training import predict
        values, training_report = predict()
        factor=factors[scenario]*multiplier*proxy_scale
        for row,value in zip(rows,values):
            aircraft=float(value)*factor
            row.update(aircraft=round(aircraft,2),passengers=round(aircraft*4.5,2),
                fuel_requests=round(aircraft*.65,2),provenance='real JFK departure-pattern model; scaled proxy; passenger/fuel ratios assumed')
    needs = requirements(rows, config)
    options = []
    if include_queue_options:
        jobs = requests(rows, seed, config)
        for label, quantile in [('Cost-Focused',.5),('Balanced',.85),('Service-Focused',1.)]:
            staffing = {name: max(dept.minimum, math.ceil(float(np.quantile(
                [r['required'] for r in needs if r['department']==name],quantile)))) for name,dept in config.items()}
            options.append(dict(name=label, staffing=staffing, **simulate(jobs,staffing,config)))
        if custom:
            options.append(dict(name='Manager Plan', staffing=custom, **simulate(jobs,custom,config)))
    ordinary_rows = forecast('Medium', multiplier, 'ordinary')
    if forecast_mode == 'uploaded':
        ordinary_rows = uploaded_profile(ordinary_demand, multiplier)
    if forecast_mode == 'trained':
        from .training import predict
        ordinary_values, _ = predict(ordinary_rows)
        for row, prediction in zip(ordinary_rows, ordinary_values):
            for key, value in zip(['aircraft','passengers','fuel_requests'], prediction):
                row[key] = round(float(value)*multiplier, 2)
            row['provenance'] = 'trained synthetic-history model; ordinary-week profile assumption'
    elif forecast_mode == 'real_proxy':
        from .real_training import predict
        ordinary_values, _ = predict()
        for row, value in zip(ordinary_rows, ordinary_values):
            aircraft = float(value)*multiplier*proxy_scale
            row.update(aircraft=round(aircraft,2), passengers=round(aircraft*4.5,2),
                       fuel_requests=round(aircraft*.65,2),
                       provenance='JFK airline-departure pattern; ordinary FBO scale is an assumption')
    return dict(forecast=rows, ordinary_forecast=ordinary_rows, requirements=needs, options=options, seed=seed,
                assumptions={name:asdict(dept) for name,dept in config.items()},
                training_report=training_report, forecast_mode=forecast_mode,
                provenance=('Uploaded ordinary-week counts; event scaling and workforce are assumptions; no forecast accuracy established' if forecast_mode=='uploaded' else 'Real JFK airline departure model; FBO scale and service demand are assumptions' if forecast_mode=='real_proxy' else 'Synthetic history; trained regression demo, not real-world validated' if training_report else 'Synthetic data; transparent planning profile, not trained ML'))

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
