"""Exercise uploaded baselines, fair scenarios, scheduling, and saved review data."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.model import run, scenario_summary


def uploaded_inputs():
    return dict(forecast_mode='uploaded', source_name='ordinary-week.csv',
                include_queue_options=False, seed=42, scenario='Medium',
                ordinary_demand=[dict(hour=h,aircraft=2,passengers=8,fuel_requests=1) for h in range(168)])


def test_uploaded_counts_drive_every_scenario_without_claiming_accuracy():
    inputs=uploaded_inputs()
    inputs['scenario_multipliers']={'Low':1.1,'Medium':1.5,'High':2.0}
    result=TestClient(app).post('/api/staffing-plan',json={'inputs':inputs}).json()
    assert all(r['aircraft']==2 for r in result['simulation']['ordinary_forecast'])
    assert all(r['aircraft']==3 for r in result['simulation']['forecast'])
    assert result['simulation']['training_report'] is None
    assert result['simulation']['options']==[]
    assert [s['total_aircraft'] for s in result['scenario_summary']['scenarios']]==[370,504,672]
    assert 'Uploaded' in result['provenance']
    assert result['baseline']['metrics']['demand_seat_hours']==result['proposed']['metrics']['demand_seat_hours']


@pytest.mark.parametrize('invalid', ['missing','duplicate','negative','nonfinite','sensitive_column'])
def test_invalid_uploaded_counts_are_rejected(invalid):
    inputs=uploaded_inputs()
    if invalid=='missing': inputs['ordinary_demand'].pop()
    elif invalid=='duplicate': inputs['ordinary_demand'][1]['hour']=0
    elif invalid=='negative': inputs['ordinary_demand'][0]['aircraft']=-1
    elif invalid=='nonfinite': inputs['ordinary_demand'][0]['aircraft']='NaN'
    else: inputs['ordinary_demand'][0]['passenger_name']='Do not accept identity columns'
    assert TestClient(app).post('/api/staffing-plan',json={'inputs':inputs}).status_code==422


def test_missing_upload_is_rejected():
    assert TestClient(app).post('/api/staffing-plan',json={
        'inputs':{'forecast_mode':'uploaded'}}).status_code==422


def test_demand_cases_cannot_be_in_reverse_order():
    inputs=uploaded_inputs()
    inputs['scenario_multipliers']={'Low':2,'Medium':1.5,'High':1.1}
    assert TestClient(app).post('/api/staffing-plan',json={'inputs':inputs}).status_code==422


@pytest.mark.parametrize('mode',['baseline','trained'])
def test_custom_scenario_summary_matches_selected_forecast(mode):
    factors={'Low':1.05,'Medium':1.55,'High':2.2}
    summary=scenario_summary(forecast_mode=mode,scenario_multipliers=factors)
    for case in summary['scenarios']:
        result=run(case['scenario'],forecast_mode=mode,scenario_multipliers=factors,include_queue_options=False)
        assert case['total_aircraft']==round(sum(r['aircraft'] for r in result['forecast']))


def test_stress_keeps_rosters_fixed_and_obeys_rest_and_hours():
    client=TestClient(app)
    body={'inputs':uploaded_inputs(),'absences':0,'surge_percent':0,'service_delay_percent':0}
    ordinary=client.post('/api/staffing-plan',json=body).json()
    body.update(absences=2,surge_percent=50,service_delay_percent=25)
    stressed=client.post('/api/staffing-plan',json=body).json()
    assert stressed==client.post('/api/staffing-plan',json=body).json()
    for kind in ('baseline','proposed'):
        assert stressed[kind]['shifts']==ordinary[kind]['shifts']
        ids={s['employee_id'] for s in stressed[kind]['shifts']}
        for employee in ids:
            shifts=sorted((s for s in stressed[kind]['shifts'] if s['employee_id']==employee),key=lambda s:s['week_start_hour'])
            assert sum(s['shift_hours'] for s in shifts)<=40
            assert all(b['week_start_hour']-a['week_end_hour']>=8 for a,b in zip(shifts,shifts[1:]))
    assert stressed['baseline']['metrics']['demand_seat_hours']==stressed['proposed']['metrics']['demand_seat_hours']


def test_uploaded_decision_preserves_source_and_inputs(tmp_path,monkeypatch):
    import backend.main as main
    monkeypatch.setattr(main,'DATA',tmp_path)
    body=dict(inputs=uploaded_inputs(),manager='Demo manager',notes='Review assumptions',approved=True)
    response=TestClient(app).post('/api/staffing-decisions',json=body)
    assert response.status_code==200
    record=response.json()
    assert record['inputs']['source_name']=='ordinary-week.csv'
    assert len(record['inputs']['ordinary_demand'])==168
    assert record['approved'] is True
    assert record['proposed']['shifts']
    assert (tmp_path/'decisions.sqlite').exists()


def test_absent_workers_do_not_also_lose_break_capacity():
    from backend.model import Department
    from backend.scheduling import _evaluate
    department='Ramp Operations'
    shifts=[dict(employee_id='A',department=department,week_start_hour=0,week_end_hour=1,break_start=0,break_end=.5),
            dict(employee_id='B',department=department,week_start_hour=0,week_end_hour=1,break_start=0,break_end=0)]
    result=_evaluate(shifts,{department:[dict(hours=1),dict(hours=1)]},[dict(hour=0)],
        [dict(hour=0,department=department,required=1)],{department:Department(24,1,32)},
        40,30,1,0,0,0,0,1,42,{department:0})
    assert result['uncovered_seat_hours']==0
    assert result['coverage_percent']==100
