import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.model import Department, simulate
from backend.training import generate_history, train

def test_trace_matches_waits_and_has_no_seat_overlap():
    result=simulate({'test':[(0,10),(0,10),(0,10),(1,10)]},{'test':2},{'test':Department(10,1,20)},True)
    events=result['traces']['test']
    assert len(events)==4
    assert np.mean([e['start']-e['arrival'] for e in events])==result['average_wait']
    for seat in range(2):
        assigned=sorted([e for e in events if e['seat']==seat],key=lambda e:e['start'])
        assert all(a['end']<=b['start'] for a,b in zip(assigned,assigned[1:]))

def test_training_is_reproducible_and_chronological(tmp_path):
    report=train(output=tmp_path)
    assert report==train(output=tmp_path)
    assert report['rows']==4320
    assert pd.Timestamp(report['train_end'])<pd.Timestamp(report['test_start'])
    assert report['real_world_validated'] is False
    assert all(m['mae']>=0 and m['baseline_mae']>=0 for m in report['metrics'].values())
    frame=pd.read_csv(tmp_path/'synthetic_training_history.csv')
    assert 'synthetic' in frame.provenance.iloc[0]

def test_heldout_labels_do_not_change_evaluation_fit(tmp_path):
    original=generate_history()
    path=tmp_path/'history.csv'
    original.to_csv(path,index=False)
    report=train(path,tmp_path)
    original.loc[int(len(original)*.8):,'aircraft']+=10
    original.to_csv(path,index=False)
    changed=train(path,tmp_path)
    assert changed['metrics']['aircraft']['mae']>report['metrics']['aircraft']['mae']

def test_replay_metrics_equal_selected_plan():
    client=TestClient(app)
    inputs={'scenario':'Low','seed':42,'forecast_mode':'trained'}
    comparison=client.post('/api/simulate',json=inputs)
    assert comparison.status_code==200
    response=client.post('/api/replay',json={'inputs':inputs,'option':'Balanced'})
    assert response.status_code==200
    replay=response.json()
    balanced=comparison.json()['options'][1]
    assert replay['departments']==balanced['departments']
    assert len(replay['traces']['Passenger Services'])==balanced['departments'][0]['requests']
