from backend.model import DEFAULTS, forecast, requirements, run


def test_forecast_returns_hourly_fbo_profile():
    rows = forecast('Medium', 1.0)
    assert len(rows) == 168
    assert rows[0]['hour'] == 0
    assert rows[0]['aircraft'] > 0
    assert 'passengers' in rows[0]


def test_requirements_estimate_staffing_by_department():
    rows = forecast('High', 1.0)
    staffing = requirements(rows, DEFAULTS)
    departments = {item['department'] for item in staffing}
    assert departments == set(DEFAULTS)
    assert all(item['required'] >= DEFAULTS[item['department']].minimum for item in staffing)


def test_run_generates_three_simulation_options():
    result = run('Medium', 1.0, seed=42)
    option_names = [option['name'] for option in result['options']]
    assert option_names == ['Cost-Focused', 'Balanced', 'Service-Focused']
    assert all('staffing' in option for option in result['options'])


def test_dashboard_summary_endpoint_is_exposed():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    payload = response.json()
    assert 'scenario' in payload
    assert 'options' in payload
    assert len(payload['options']) == 3


def test_staffing_pool_size_is_configurable():
    from fastapi.testclient import TestClient
    from backend.main import app

    response = TestClient(app).post('/api/staffing-plan', json={
        'inputs': {'scenario': 'Medium'},
        'worker_pool_size': 1,
        'disruption_hours': 1,
    })
    assert response.status_code == 200
    assert response.json()['proposed']['metrics']['unfilled_roster_slots'] > 0
