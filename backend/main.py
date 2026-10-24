import json
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .model import DATA, DEFAULTS, Department, run, requests, scenario_summary
from .scheduling import compare_staffing_plans

app = FastAPI(title='Apron · FBO Staffing Lab')

@app.get('/api/dashboard')
def dashboard():
    return dict(scenario='Medium', **run())

@app.get('/api/scenario-summary')
def get_scenario_summary(multiplier: float = 1.0, forecast_mode: str = 'baseline',
                         proxy_scale: float = .25, service_minutes: str = '{}'):
    if not .1 <= multiplier <= 3:
        raise HTTPException(422, 'Demand multiplier must be between .1 and 3')
    if forecast_mode not in ('baseline', 'trained', 'real_proxy'):
        raise HTTPException(422, 'Unknown forecast mode')
    if not .01 <= proxy_scale <= 1:
        raise HTTPException(422, 'Proxy scale must be between .01 and 1')
    try:
        minutes = json.loads(service_minutes)
    except json.JSONDecodeError:
        raise HTTPException(422, 'service_minutes must be a JSON object')
    if not isinstance(minutes, dict) or set(minutes)-set(DEFAULTS) or any(
        not isinstance(value, (int, float)) or not .1 <= value <= 240 for value in minutes.values()):
        raise HTTPException(422, 'Invalid service_minutes values')
    config = {name: Department(minutes.get(name, dept.minutes), dept.minimum, dept.wage,
                               dept.utilization, dept.target_wait) for name, dept in DEFAULTS.items()}
    return scenario_summary(multiplier, config, forecast_mode, proxy_scale)

class SimulationInput(BaseModel):
    scenario: str = 'Medium'
    multiplier: float = Field(1, ge=.1, le=3)
    seed: int = Field(42, ge=0)
    service_minutes: dict[str,float] = Field(default_factory=dict)
    custom: dict[str,int] | None = None
    forecast_mode: str = 'baseline'
    proxy_scale: float = Field(.25,ge=.01,le=1)

def calculate(body):
    if body.forecast_mode not in ('baseline','trained','real_proxy'):
        raise HTTPException(422,'Unknown forecast mode')
    if body.scenario not in ('Low','Medium','High'):
        raise HTTPException(422,'Unknown scenario')
    if set(body.service_minutes)-set(DEFAULTS):
        raise HTTPException(422,'Unknown department')
    if any(not .1 <= x <= 240 for x in body.service_minutes.values()):
        raise HTTPException(422,'Service duration must be between .1 and 240 minutes')
    if body.custom is not None and (set(body.custom)!=set(DEFAULTS) or any(
        not DEFAULTS[n].minimum<=v<=100 for n,v in body.custom.items())):
        raise HTTPException(422,'Supply all departments with qualified staffing between minimum and 100')
    config = {n:Department(body.service_minutes.get(n,d.minutes),d.minimum,d.wage,d.utilization,d.target_wait) for n,d in DEFAULTS.items()}
    try:
        return run(body.scenario,body.multiplier,body.seed,config,body.custom,body.forecast_mode,body.proxy_scale)
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
            disruption_hours=body.disruption_hours)
        plan['simulation'] = result
        plan['scenario_summary'] = scenario_summary(
            body.inputs.multiplier, config, body.inputs.forecast_mode, body.inputs.proxy_scale)
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
                  proposed=plan['proposed'], impact=plan['impact'], provenance=plan['provenance'],
                  scope='Local planning record only; no worker dispatch or operational changes')
    with sqlite3.connect(DATA/'decisions.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS staffing_decisions (id INTEGER PRIMARY KEY, record TEXT NOT NULL)')
        cursor = db.execute('INSERT INTO staffing_decisions(record) VALUES (?)', (json.dumps(record),))
        record['id'] = cursor.lastrowid
    return record

@app.post('/api/schedule')
def schedule(body: SimulationInput):
    if body.scenario != 'Medium':
        raise HTTPException(422, 'The synthetic shift planner currently supports the Medium scenario only')
    result = calculate(body)
    from .scheduler import plan
    return plan(result['requirements'])

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
