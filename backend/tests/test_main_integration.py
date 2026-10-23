from collections import defaultdict
from fastapi.testclient import TestClient
from backend.main import app
from backend.model import DEFAULTS

def test_ordinary_and_event_summary_uses_selected_source():
    client=TestClient(app)
    response=client.get('/api/scenario-summary',params={'forecast_mode':'trained','service_minutes':'{"Ramp Operations":30}'})
    assert response.status_code==200
    data=response.json()
    assert [row['scenario'] for row in data['scenarios']]==['Low','Medium','High']
    totals=[data['ordinary_total_aircraft']]+[row['total_aircraft'] for row in data['scenarios']]
    assert totals==sorted(totals)
    assert all(set(row['peak_seats'])==set(DEFAULTS) for row in data['scenarios'])

def test_roster_api_preserves_limits_and_reports_costs_from_shifts():
    client=TestClient(app)
    response=client.post('/api/staffing-plan',json={'inputs':{'scenario':'Medium','forecast_mode':'trained'},'absences':2,'surge_percent':50})
    assert response.status_code==200
    data=response.json()
    for key in ['baseline','proposed']:
        roster=data[key]
        by_employee=defaultdict(list)
        for shift in roster['shifts']:
            assert shift['qualification']==shift['department']
            assert shift['week_start_hour']<=shift['break_start']<=shift['break_end']<=shift['week_end_hour']
            by_employee[shift['employee_id']].append(shift)
        for shifts in by_employee.values():
            shifts.sort(key=lambda row:row['week_start_hour'])
            assert sum(s['shift_hours'] for s in shifts)<=40
            assert all(b['week_start_hour']-a['week_end_hour']>=8 for a,b in zip(shifts,shifts[1:]))
        assert roster['metrics']['estimated_labor_cost']==sum(s['shift_hours']*DEFAULTS[s['department']].wage for s in roster['shifts'])
        assert roster['metrics']['absences']==2
        assert roster['metrics']['surge_percent']==50
    assert data['baseline']['metrics']['disruption_window']==data['proposed']['metrics']['disruption_window']
    assert data['simulation']['ordinary_forecast']

def test_roster_review_uses_separate_local_log(tmp_path,monkeypatch):
    import backend.main as api
    monkeypatch.setattr(api,'DATA',tmp_path)
    client=TestClient(app)
    response=client.post('/api/staffing-decisions',json={'inputs':{'scenario':'Low'},'manager':'Integration review','notes':'Synthetic fixture only','approved':True})
    assert response.status_code==200
    data=response.json()
    assert data['approved'] is True and data['proposed']['shifts']
    assert data['assumptions']['shift_hours']==8
    assert (tmp_path/'decisions.sqlite').exists()
    assert client.post('/api/staffing-plan',json={'inputs':{},'shift_hours':7}).status_code==422
