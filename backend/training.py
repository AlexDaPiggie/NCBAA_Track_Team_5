"""Reproducible supervised ridge regression on explicitly synthetic hourly history."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent / 'data'
TARGETS = ['aircraft', 'passengers', 'fuel_requests']

def features(hour, weekday, event):
    hour, weekday, event = np.broadcast_arrays(hour, weekday, event)
    morning = np.exp(-((hour-11)/3)**2)
    evening = np.exp(-((hour-18)/3)**2)
    return np.column_stack([np.ones(hour.size), morning.ravel(), evening.ravel(),
        np.sin(2*np.pi*weekday/7).ravel(), np.cos(2*np.pi*weekday/7).ravel(),
        event.ravel(), (event*morning).ravel(), (event*evening).ravel()])

def generate_history(seed=2026):
    rng = np.random.default_rng(seed)
    dates = pd.date_range('2025-01-06', periods=180*24, freq='h')
    day = np.arange(len(dates))//24
    event = np.where(day%28 >= 21, np.take([0,.1,.2,.4,.8,1,.5],day%7), 0.)
    rate = (1.2+4*np.exp(-((dates.hour.to_numpy()-11)/3)**2)
            +5*np.exp(-((dates.hour.to_numpy()-18)/3)**2))*(1+event)
    aircraft = rng.poisson(rate)
    return pd.DataFrame(dict(timestamp=dates.astype(str), hour=dates.hour,
        weekday=dates.day_of_week, event_index=event, aircraft=aircraft,
        passengers=rng.poisson(aircraft*4.5), fuel_requests=rng.binomial(aircraft,.65),
        provenance='synthetic generated training history; not observed aviation data'))

def train(path=None, output=ROOT):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    if path is None:
        frame = generate_history()
        frame.to_csv(output/'synthetic_training_history.csv',index=False)
    else:
        frame = pd.read_csv(path)
    required = ['timestamp','hour','weekday','event_index',*TARGETS,'provenance']
    if set(required)-set(frame.columns):
        raise ValueError(f'Required columns: {required}; found {list(frame.columns)}')
    frame['timestamp'] = pd.to_datetime(frame.timestamp, errors='raise')
    frame = frame.sort_values('timestamp').reset_index(drop=True)
    if len(frame)<24*60 or frame.timestamp.duplicated().any():
        raise ValueError('Need at least 60 days of unique hourly history')
    numeric = frame[['hour','weekday','event_index',*TARGETS]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (numeric<0).any() or (frame.hour>23).any() or (frame.weekday>6).any():
        raise ValueError('Invalid numeric values')
    if frame.provenance.isna().any() or frame.provenance.str.strip().eq('').any():
        raise ValueError('Provenance is required for every row')
    x = features(frame.hour.to_numpy(),frame.weekday.to_numpy(),frame.event_index.to_numpy())
    y = frame[TARGETS].to_numpy(dtype=float)
    split = int(len(frame)*.8)
    penalty = np.eye(x.shape[1])*.1
    penalty[0,0] = 0
    def fit(a,b): return np.linalg.solve(a.T@a+penalty,a.T@b)
    evaluation_coefficients = fit(x[:split],y[:split])
    prediction = np.maximum(0,x[split:]@evaluation_coefficients)
    # Training-only hour-of-day means are a simple, leakage-free comparator.
    means = frame.iloc[:split].groupby('hour')[TARGETS].mean()
    baseline = means.loc[frame.hour.iloc[split:]].to_numpy()
    metrics = {name:dict(mae=float(np.mean(abs(prediction[:,i]-y[split:,i]))),
                         baseline_mae=float(np.mean(abs(baseline[:,i]-y[split:,i]))),
                         rmse=float(np.sqrt(np.mean((prediction[:,i]-y[split:,i])**2))))
               for i,name in enumerate(TARGETS)}
    report = dict(model='Ridge regression, alpha=0.1; eight calendar/event features',
        dataset_provenance=sorted(frame.provenance.unique().tolist()),
        real_world_validated=False, rows=len(frame), train_rows=split,test_rows=len(frame)-split,
        train_end=str(frame.timestamp.iloc[split-1]),test_start=str(frame.timestamp.iloc[split]),
        split='chronological first 80% train / final 20% holdout; then refit on all rows for inference',
        metrics=metrics,feature_names=['intercept','morning','evening','weekday_sin','weekday_cos','event','event_morning','event_evening'])
    artifact = dict(coefficients=fit(x,y).tolist(),report=report)
    (output/'trained_forecast.json').write_text(json.dumps(artifact,indent=2),encoding='utf-8')
    return report

def predict(rows):
    artifact = json.loads((ROOT/'trained_forecast.json').read_text(encoding='utf-8'))
    hours = np.array([r['clock'] for r in rows])
    weekdays = np.array([r['day']-1 for r in rows])
    event = np.take([0,.1,.2,.4,.8,1,.5],weekdays)
    values = np.maximum(0,features(hours,weekdays,event)@np.array(artifact['coefficients']))
    return values, artifact['report']

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv',type=Path,help='Optional inspected hourly history with documented provenance')
    args=parser.parse_args()
    print(json.dumps(train(args.csv),indent=2))
