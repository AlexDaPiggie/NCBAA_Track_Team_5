import json
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .model import DATA, DEFAULTS, SCENARIO_MULTIPLIERS, Department, run, requests, scenario_summary
from .scheduling import compare_staffing_plans

app = FastAPI(title='CrewPilot AI · Event-week staffing planner')

@app.get('/api/dashboard')
def dashboard():
    return dict(scenario='Medium', **run())

@app.get('/api/scenario-summary')
def get_scenario_summary(multiplier: float = 1.0, forecast_mode: str = 'baseline',
                         proxy_scale: float = .25, service_minutes: str = '{}',
                         scenario_multipliers: str = '{}', staffing_minimums: str = '{}',
                         target_utilization: str = '{}'):
    if not .1 <= multiplier <= 3:
        raise HTTPException(422, 'Demand multiplier must be between .1 and 3')
    if forecast_mode not in ('baseline', 'trained', 'real_proxy'):
        raise HTTPException(422, 'Unknown forecast mode')
    if not .01 <= proxy_scale <= 1:
        raise HTTPException(422, 'Proxy scale must be between .01 and 1')
    try:
        minutes = json.loads(service_minutes)
        factors = json.loads(scenario_multipliers)
        minimums = json.loads(staffing_minimums)
        utilizations = json.loads(target_utilization)
    except json.JSONDecodeError:
        raise HTTPException(422, 'service_minutes must be a JSON object')
    if not isinstance(minutes, dict) or set(minutes)-set(DEFAULTS) or any(
        not isinstance(value, (int, float)) or not .1 <= value <= 240 for value in minutes.values()):
        raise HTTPException(422, 'Invalid service_minutes values')
    if not isinstance(factors, dict) or set(factors)-set(SCENARIO_MULTIPLIERS):
        raise HTTPException(422, 'Invalid scenario_multipliers')
    factors = {**SCENARIO_MULTIPLIERS, **factors}
    if any(not 1 <= value <= 3 for value in factors.values()):
        raise HTTPException(422, 'Scenario multipliers must be between 1 and 3')
    if not factors['Low'] <= factors['Medium'] <= factors['High']:
        raise HTTPException(422, 'Keep demand factors ordered: Low <= Medium <= High')
    if not isinstance(minimums, dict) or set(minimums)-set(DEFAULTS) or any(
        not isinstance(value, int) or not 1 <= value <= 30 for value in minimums.values()):
        raise HTTPException(422, 'Invalid staffing_minimums values')
    if not isinstance(utilizations, dict) or set(utilizations)-set(DEFAULTS) or any(
        not isinstance(value, (int, float)) or not .25 <= value <= 1 for value in utilizations.values()):
        raise HTTPException(422, 'Invalid target_utilization values')
    config = {name: Department(minutes.get(name, dept.minutes), minimums.get(name, dept.minimum), dept.wage,
                               utilizations.get(name, dept.utilization), dept.target_wait) for name, dept in DEFAULTS.items()}
    return scenario_summary(multiplier, config, forecast_mode, proxy_scale, factors)

class DemandHour(BaseModel):
    model_config = {'allow_inf_nan': False, 'extra': 'forbid'}
    hour: int = Field(ge=0, le=167)
    aircraft: float = Field(ge=0, le=1000)
    passengers: float = Field(ge=0, le=10000)
    fuel_requests: float = Field(ge=0, le=1000)


class SimulationInput(BaseModel):
    model_config = {'allow_inf_nan': False}
    scenario: str = 'Medium'
    multiplier: float = Field(1, ge=.1, le=3)
    seed: int = Field(42, ge=0)
    service_minutes: dict[str,float] = Field(default_factory=dict)
    service_wages: dict[str,float] = Field(default_factory=dict)
    staffing_minimums: dict[str,int] = Field(default_factory=dict)
    target_utilization: dict[str,float] = Field(default_factory=dict)
    target_wait_minutes: dict[str,float] = Field(default_factory=dict)
    custom: dict[str,int] | None = None
    forecast_mode: str = 'baseline'
    proxy_scale: float = Field(.25,ge=.01,le=1)
    scenario_multipliers: dict[str, float] = Field(default_factory=lambda: dict(SCENARIO_MULTIPLIERS))
    ordinary_demand: list[DemandHour] | None = Field(None, min_length=168, max_length=168)
    source_name: str = Field('Uploaded ordinary week', min_length=1, max_length=120)
    include_queue_options: bool = True

def calculate(body):
    if body.forecast_mode not in ('baseline','trained','real_proxy','uploaded'):
        raise HTTPException(422,'Unknown forecast mode')
    if body.forecast_mode == 'uploaded' and (body.ordinary_demand is None or
        {row.hour for row in body.ordinary_demand} != set(range(168))):
        raise HTTPException(422,'Upload exactly one row for every hour from 0 through 167')
    if body.ordinary_demand is not None and body.forecast_mode != 'uploaded':
        raise HTTPException(422,'Uploaded counts require uploaded forecast mode')
    if body.scenario not in ('Low','Medium','High'):
        raise HTTPException(422,'Unknown scenario')
    if set(body.scenario_multipliers) != set(SCENARIO_MULTIPLIERS) or any(
        not 1 <= value <= 3 for value in body.scenario_multipliers.values()):
        raise HTTPException(422,'Set low, medium, and high scenario multipliers between 1 and 3')
    if not body.scenario_multipliers['Low'] <= body.scenario_multipliers['Medium'] <= body.scenario_multipliers['High']:
        raise HTTPException(422,'Keep demand factors ordered: Low <= Medium <= High')
    if set(body.service_minutes)-set(DEFAULTS):
        raise HTTPException(422,'Unknown department')
    if set(body.service_wages)-set(DEFAULTS) or any(not 0 <= x <= 500 for x in body.service_wages.values()):
        raise HTTPException(422,'Hourly wages must be between 0 and 500 for known departments')
    if set(body.staffing_minimums)-set(DEFAULTS) or any(not 1 <= x <= 30 for x in body.staffing_minimums.values()):
        raise HTTPException(422,'Staffing minimums must be between 1 and 30 for known departments')
    if set(body.target_utilization)-set(DEFAULTS) or any(not .25 <= x <= 1 for x in body.target_utilization.values()):
        raise HTTPException(422,'Target utilization must be between .25 and 1')
    if set(body.target_wait_minutes)-set(DEFAULTS) or any(not 1 <= x <= 120 for x in body.target_wait_minutes.values()):
        raise HTTPException(422,'Wait targets must be between 1 and 120 minutes')
    if any(not .1 <= x <= 240 for x in body.service_minutes.values()):
        raise HTTPException(422,'Service duration must be between .1 and 240 minutes')
    if body.custom is not None and (set(body.custom)!=set(DEFAULTS) or any(
        not body.staffing_minimums.get(n,DEFAULTS[n].minimum)<=v<=100 for n,v in body.custom.items())):
        raise HTTPException(422,'Supply all departments with qualified staffing between minimum and 100')
    config = {n:Department(body.service_minutes.get(n,d.minutes),body.staffing_minimums.get(n,d.minimum),body.service_wages.get(n,d.wage),body.target_utilization.get(n,d.utilization),body.target_wait_minutes.get(n,d.target_wait)) for n,d in DEFAULTS.items()}
    try:
        return run(body.scenario,body.multiplier,body.seed,config,body.custom,body.forecast_mode,body.proxy_scale,body.scenario_multipliers,
                   [row.model_dump() for row in body.ordinary_demand] if body.ordinary_demand is not None else None,
                   body.include_queue_options)
    except FileNotFoundError:
        raise HTTPException(422,'Train the forecast first: python -m backend.training')

@app.post('/api/simulate')
def simulate(body: SimulationInput):
    return calculate(body)

class StaffingPlanInput(BaseModel):
    inputs: SimulationInput
    shift_hours: int = Field(8, ge=6, le=12)
    break_minutes: int = Field(30, ge=0, le=60)
    max_weekly_hours: int = Field(40, ge=6, le=84)
    minimum_rest_hours: int = Field(8, ge=0, le=24)
    absences: int = Field(2, ge=0, le=10)
    surge_percent: int = Field(50, ge=0, le=200)
    service_delay_percent: int = Field(25, ge=0, le=200)
    disruption_day: int = Field(5, ge=0, le=6)
    disruption_start: int = Field(15, ge=0, le=23)
    disruption_hours: int = Field(4, ge=1, le=8)
    worker_pool_size: int = Field(30, ge=1, le=100)

def build_staffing_plan(body: StaffingPlanInput):
    result = calculate(body.inputs)
    config = {name: Department(**rules) for name, rules in result['assumptions'].items()}
    try:
        plan = compare_staffing_plans(
            result['forecast'], result['ordinary_forecast'], result['requirements'], config,
            seed=body.inputs.seed, shift_hours=body.shift_hours,
            break_minutes=body.break_minutes, max_weekly_hours=body.max_weekly_hours,
            minimum_rest_hours=body.minimum_rest_hours, absences=body.absences,
            surge_percent=body.surge_percent,
            service_delay_percent=body.service_delay_percent,
            disruption_day=body.disruption_day, disruption_start=body.disruption_start,
            disruption_hours=body.disruption_hours, worker_pool_size=body.worker_pool_size)
        plan['simulation'] = result
        if body.inputs.forecast_mode == 'uploaded':
            plan['provenance'] = 'Uploaded ordinary-week counts with assumed event scaling; synthetic workers assumed available and qualified.'
        plan['scenario_summary'] = scenario_summary(
            body.inputs.multiplier, config, body.inputs.forecast_mode, body.inputs.proxy_scale,
            body.inputs.scenario_multipliers,
            [row.model_dump() for row in body.inputs.ordinary_demand] if body.inputs.ordinary_demand is not None else None)
        return plan
    except ValueError as exc:
        raise HTTPException(422, str(exc))

@app.post('/api/staffing-plan')
def staffing_plan(body: StaffingPlanInput):
    return build_staffing_plan(body)

class StaffingDecisionInput(StaffingPlanInput):
    manager: str = Field(min_length=1, max_length=100)
    notes: str = Field('', max_length=2000)
    approved: bool

@app.post('/api/staffing-decisions')
def decide_staffing_plan(body: StaffingDecisionInput):
    plan = build_staffing_plan(body)
    DATA.mkdir(exist_ok=True)
    record = dict(manager=body.manager, notes=body.notes, approved=body.approved,
                  timestamp=datetime.now(timezone.utc).isoformat(),
                  inputs=body.inputs.model_dump(),
                  assumptions=plan['assumptions'], baseline=plan['baseline'],
                  proposed=plan['proposed'], provenance=plan['provenance'],
                  scope='Local planning record only; no worker dispatch or operational changes')
    with sqlite3.connect(DATA/'decisions.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS staffing_decisions (id INTEGER PRIMARY KEY, record TEXT NOT NULL)')
        cursor = db.execute('INSERT INTO staffing_decisions(record) VALUES (?)', (json.dumps(record),))
        record['id'] = cursor.lastrowid
    return record

class ReplayInput(BaseModel):
    inputs: SimulationInput
    option: str = 'Balanced'

@app.post('/api/replay')
def replay(body: ReplayInput):
    result = calculate(body.inputs)
    option = next((o for o in result['options'] if o['name']==body.option),None)
    if option is None:
        raise HTTPException(422,'Unknown plan')
    config = {n:Department(**d) for n,d in result['assumptions'].items()}
    from .model import simulate as simulate_engine
    return dict(option=body.option, staffing=option['staffing'], forecast=result['forecast'],
        **simulate_engine(requests(result['forecast'],body.inputs.seed,config),option['staffing'],config,include_trace=True))

class Decision(BaseModel):
    inputs: SimulationInput
    option: str
    manager: str = Field(min_length=1,max_length=100)
    notes: str = Field('',max_length=2000)
    approved: bool

@app.post('/api/decisions')
def decide(body: Decision):
    result = calculate(body.inputs)
    option = next((o for o in result['options'] if o['name']==body.option),None)
    if option is None:
        raise HTTPException(422,'Unknown plan')
    DATA.mkdir(exist_ok=True)
    record = dict(manager=body.manager,notes=body.notes,approved=body.approved,
                  timestamp=datetime.now(timezone.utc).isoformat(),inputs=body.inputs.model_dump(),plan=option,
                  scope='Local planning record only; no operational changes')
    with sqlite3.connect(DATA/'decisions.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS decisions (id INTEGER PRIMARY KEY, record TEXT NOT NULL)')
        cursor=db.execute('INSERT INTO decisions(record) VALUES (?)',(json.dumps(record),))
        record['id']=cursor.lastrowid
    return record
