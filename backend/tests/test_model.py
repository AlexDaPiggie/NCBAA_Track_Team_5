import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.model import Department, DEFAULTS, forecast, historical_forecast, requirements, requests, simulate, run

def test_threshold_boundary():
    config={'Passenger Services':Department(5,1,26)}
    rows=[dict(hour=0,passengers=9.6),dict(hour=1,passengers=9.601)]
    assert [r['required'] for r in requirements(rows,config)]==[1,2]

def test_actual_queue_wait_and_utilization():
    config={'test':Department(10,1,20)}
    jobs={'test':[(0,10),(0,10),(0,10)]}
    one=simulate(jobs,{'test':1},config)
    three=simulate(jobs,{'test':3},config)
    assert one['average_wait']==10
    assert three['average_wait']==0
    assert one['cost']*3==three['cost']

def test_fixed_shift_cost_and_simulation_use_block_staffing():
    config={'test':Department(10,1,20)}
    jobs={'test':[(480,10),(480,10),(480,10)]}
    shifts={'test':{'00-08':1,'08-16':2,'16-24':1}}
    result=simulate(jobs,shifts,config)
    assert result['cost']==4*8*7*20
    assert result['average_wait']==3.33

def test_reproducible_and_monotonic_options():
    a=run()
    assert a==run()
    assert a['options'][0]['cost']<=a['options'][1]['cost']<=a['options'][2]['cost']
    assert a['options'][0]['average_wait']>=a['options'][1]['average_wait']>=a['options'][2]['average_wait']
    assert all(set(option['shift_staffing'])==set(DEFAULTS) for option in a['options'])

def test_department_drivers():
    rows=forecast()
    original=requirements(rows,DEFAULTS)
    for row in rows: row['passengers']*=10
    updated=requirements(rows,DEFAULTS)
    assert [r for r in original if r['department']!='Passenger Services']==[r for r in updated if r['department']!='Passenger Services']

def test_invalid_safety_and_inputs():
    client=TestClient(app)
    assert client.post('/api/simulate',json={'custom':{'Passenger Services':1,'Ramp Operations':1,'Fuel Services':1}}).status_code==422
    assert client.post('/api/simulate',json={'scenario':'unknown'}).status_code==422
    assert client.post('/api/simulate',json={'service_minutes':{'Fuel Services':0}}).status_code==422

def test_api_and_approval_snapshot(tmp_path,monkeypatch):
    import backend.main as main
    monkeypatch.setattr(main,'DATA',tmp_path)
    client=TestClient(app)
    response=client.post('/api/simulate',json={'scenario':'Low'})
    assert response.status_code==200
    assert len(response.json()['forecast'])==168
    response=client.post('/api/decisions',json={'inputs':{'scenario':'Low'},'option':'Balanced','manager':'Demo Manager','approved':True})
    assert response.status_code==200
    assert response.json()['plan']['name']=='Balanced'
    assert (tmp_path/'decisions.sqlite').exists()

def test_week_end_backlog():
    result=simulate({'test':[(10079,10)]},{'test':1},{'test':Department(10,1,20)})
    assert result['unfinished_at_close']==1

def test_high_demand_increases_requirements():
    assert max(r['required'] for r in requirements(forecast('High'),DEFAULTS)) > max(r['required'] for r in requirements(forecast('Low'),DEFAULTS))

def test_historical_flights_use_real_arrival_times_and_seven_day_window():
    rows=historical_forecast()
    assert len(rows)==168
    assert rows[0]['date']=='2022-02-07'
    assert rows[-1]['date']=='2022-02-13'
    game_day=[row for row in rows if row['date']=='2022-02-13']
    assert sum(row['observed_aircraft'] for row in game_day)==511
    assert all(row['aircraft']==len(row['flight_arrivals']) for row in rows)
    jobs=requests(rows,42,DEFAULTS)
    assert len(jobs['Ramp Operations'])==sum(row['aircraft'] for row in rows)
    expected=sorted(row['hour']*60+minute for row in rows for minute in row['flight_arrivals'])
    assert [arrival for arrival,_ in jobs['Ramp Operations']]==expected

def test_historical_scenario_scaling_is_seeded():
    a=historical_forecast('High',seed=7)
    assert a==historical_forecast('High',seed=7)
    assert sum(row['aircraft'] for row in a)>sum(row['observed_aircraft'] for row in a)

def test_historical_forecast_is_available_through_api():
    response=TestClient(app).post('/api/simulate',json={'forecast_mode':'historical'})
    assert response.status_code==200
    result=response.json()
    assert result['forecast_mode']=='historical'
    assert len(result['forecast'])==168
    assert sum(row['aircraft'] for row in result['forecast'])==3502
