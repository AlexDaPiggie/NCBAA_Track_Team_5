import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.model import Department, DEFAULTS, forecast, requirements, requests, simulate, run

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

def test_reproducible_and_monotonic_options():
    a=run()
    assert a==run()
    assert a['options'][0]['cost']<=a['options'][1]['cost']<=a['options'][2]['cost']
    assert a['options'][0]['average_wait']>=a['options'][1]['average_wait']>=a['options'][2]['average_wait']

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

def test_event_factors_are_configurable_and_ordered():
    factors={'Low':1.05,'Medium':1.3,'High':1.9}
    low=forecast('Low',scenario_multipliers=factors)
    high=forecast('High',scenario_multipliers=factors)
    assert sum(r['aircraft'] for r in high) > sum(r['aircraft'] for r in low)

def test_api_accepts_custom_event_factors_and_wages():
    response=TestClient(app).post('/api/simulate',json={
        'scenario':'High',
        'scenario_multipliers':{'Low':1.05,'Medium':1.3,'High':1.9},
        'service_wages':{'Passenger Services':30},
        'staffing_minimums':{'Passenger Services':3},
        'target_utilization':{'Ramp Operations':.7},
        'target_wait_minutes':{'Fuel Services':15},
    })
    assert response.status_code==200
    assert response.json()['assumptions']['Passenger Services']['wage']==30
    assert response.json()['assumptions']['Passenger Services']['minimum']==3
    assert response.json()['assumptions']['Ramp Operations']['utilization']==.7
    assert response.json()['assumptions']['Fuel Services']['target_wait']==15

def test_api_rejects_incomplete_scenario_factors():
    response=TestClient(app).post('/api/simulate',json={
        'scenario_multipliers':{'Low':1.1},
    })
    assert response.status_code==422

def test_scenario_summary_uses_ui_factors_and_staffing_settings():
    import json
    response=TestClient(app).get('/api/scenario-summary',params={
        'scenario_multipliers':json.dumps({'Low':1.1,'Medium':1.5,'High':2.0}),
        'staffing_minimums':json.dumps({'Ramp Operations':3}),
        'target_utilization':json.dumps({'Fuel Services':.6}),
    })
    assert response.status_code==200
    summary=response.json()
    assert [row['event_multiplier'] for row in summary['scenarios']]==[1.1,1.5,2.0]
