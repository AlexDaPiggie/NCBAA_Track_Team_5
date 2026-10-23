import json
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.real_training import aggregate,train

def test_departure_rollover_and_missing_records():
    frame=pd.DataFrame(dict(year=[2013]*3,month=[1]*3,day=[1]*3,origin=['JFK']*3,
        dep_time=[10,1010,np.nan],sched_dep_time=[2350,1000,1000],dep_delay=[20,10,np.nan]))
    hourly,audit=aggregate(frame)
    assert hourly.loc[hourly.timestamp.eq('2013-01-02 00:00:00'),'aircraft'].item()==1
    assert hourly.aircraft.sum()==2
    assert audit['excluded_missing_departures']==1
    assert len(hourly)==8760

def test_real_proxy_api_and_scale():
    client=TestClient(app)
    low=client.post('/api/simulate',json={'forecast_mode':'real_proxy','proxy_scale':.1})
    high=client.post('/api/simulate',json={'forecast_mode':'real_proxy','proxy_scale':.2})
    assert low.status_code==high.status_code==200
    assert low.json()['training_report']['audit']['source_rows']==336776
    assert low.json()['training_report']['real_world_validated'] is False
    assert 'departure' in low.json()['provenance'].lower()
    assert abs(sum(r['aircraft'] for r in high.json()['forecast'])-2*sum(r['aircraft'] for r in low.json()['forecast']))<2
    assert client.post('/api/simulate',json={'proxy_scale':0}).status_code==422

def test_real_holdout_does_not_leak_target_labels(tmp_path):
    # Deliberately generated fixture, not real observations.
    dates=pd.date_range('2013-01-01',periods=365,freq='D')
    frame=pd.DataFrame(dict(year=dates.year,month=dates.month,day=dates.day,
        origin='JFK',dep_time=1000,sched_dep_time=1000,dep_delay=0))
    raw=tmp_path/'fixture.csv';frame.to_csv(raw,index=False)
    report=train(raw,tmp_path)
    before=pd.read_csv(tmp_path/'real_forecast_holdout.csv').model_prediction
    pd.concat([frame,frame.tail(20)],ignore_index=True).to_csv(raw,index=False)
    train(raw,tmp_path)
    after=pd.read_csv(tmp_path/'real_forecast_holdout.csv').model_prediction
    np.testing.assert_allclose(before,after)
    assert pd.Timestamp(report['train_end'])<pd.Timestamp(report['test_start'])
