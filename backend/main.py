import json
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .model import DATA, DEFAULTS, Department, run, requests

app = FastAPI(title='Apron · FBO Staffing Lab')

@app.get('/api/dashboard')
def dashboard():
    return dict(scenario='Medium', **run())

class SimulationInput(BaseModel):
    scenario: str = 'Medium'
    multiplier: float = Field(1, ge=.1, le=3)
    seed: int = Field(42, ge=0)
    service_minutes: dict[str,float] = Field(default_factory=dict)
    custom: dict[str,int] | None = None
    forecast_mode: str = 'baseline'

def calculate(body):
    if body.forecast_mode not in ('baseline','trained','historical'):
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
        return run(body.scenario,body.multiplier,body.seed,config,body.custom,body.forecast_mode)
    except FileNotFoundError:
        if body.forecast_mode == 'historical':
            raise HTTPException(422,'Historical flight data is missing: backend/data/lax_super_bowl_week.csv')
        raise HTTPException(422,'Train the forecast first: python -m backend.training')

@app.post('/api/simulate')
def simulate(body: SimulationInput):
    return calculate(body)

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
    return dict(option=body.option, staffing=option['staffing'],
        shift_staffing=option['shift_staffing'], forecast=result['forecast'],
        **simulate_engine(requests(result['forecast'],body.inputs.seed,config),
                          option['shift_staffing'],config,include_trace=True))

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
