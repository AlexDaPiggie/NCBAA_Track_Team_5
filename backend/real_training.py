"""Real airline activity proxy. Never represent departures as FBO arrivals."""
import hashlib
import json
from pathlib import Path
import urllib.request
import numpy as np
import pandas as pd

ROOT=Path(__file__).parent/'data'
URL='https://vincentarelbundock.github.io/Rdatasets/csv/nycflights13/flights.csv'
DOC='https://nycflights13.tidyverse.org/reference/flights.html'

def features(dates):
    dates=pd.DatetimeIndex(dates)
    hour=dates.hour.to_numpy()
    weekday=dates.day_of_week.to_numpy()
    return np.column_stack([np.ones(len(dates)), np.eye(24)[hour],np.eye(7)[weekday],
        np.sin(2*np.pi*dates.day_of_year.to_numpy()/365),
        np.cos(2*np.pi*dates.day_of_year.to_numpy()/365),
        (weekday>=5)[:,None]*np.eye(24)[hour]])

def aggregate(frame,origin='JFK'):
    required={'year','month','day','origin','dep_time','sched_dep_time','dep_delay'}
    if required-set(frame.columns):
        raise ValueError(f'Missing flight columns: {sorted(required-set(frame.columns))}')
    selected=frame[frame.origin.eq(origin)].copy()
    if selected.empty: raise ValueError('No records for selected airport')
    dates=pd.to_datetime(selected[['year','month','day']])
    scheduled=pd.to_numeric(selected.sched_dep_time,errors='raise')
    valid=selected.dep_time.notna()&selected.dep_delay.notna()
    # Departure date is a schedule date. Add actual delay to recover midnight rollover.
    actual=dates+pd.to_timedelta(scheduled//100*60+scheduled%100+selected.dep_delay,unit='m')
    if ((scheduled%100)>=60).any(): raise ValueError('Invalid HHMM values')
    counts=actual[valid].dt.floor('h').value_counts()
    index=pd.date_range('2013-01-01','2013-12-31 23:00:00',freq='h')
    result=pd.DataFrame({'timestamp':index,'aircraft':counts.reindex(index,fill_value=0).to_numpy(),
        'provenance':'observed JFK airline departures; not FBO arrivals'})
    return result,dict(airport=origin,source_rows=len(frame),airport_rows=len(selected),
        excluded_missing_departures=int((~valid).sum()),
        excluded_outside_2013=int((valid&~actual.between(index[0],index[-1]+pd.Timedelta(minutes=59))).sum()),
        observed_departures=int(result.aircraft.sum()),actual_columns=list(frame.columns))

def train(raw=None,output=ROOT,download=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    path=Path(raw) if raw else ROOT/'raw'/'nycflights13_flights.csv'
    if not path.exists():
        if not download: raise FileNotFoundError('Run python -m backend.real_training --download')
        path.parent.mkdir(parents=True,exist_ok=True)
        urllib.request.urlretrieve(URL,path)
    frame=pd.read_csv(path)
    hourly,audit=aggregate(frame)
    hourly.to_csv(output/'real_jfk_hourly_departures.csv',index=False)
    x=features(hourly.timestamp)
    y=hourly.aircraft.to_numpy(dtype=float)
    split=int(len(y)*.8)
    regularizer=np.eye(x.shape[1])*10
    regularizer[0,0]=0
    def fit(a,b):return np.linalg.solve(a.T@a+regularizer,a.T@b)
    predicted=np.maximum(0,x[split:]@fit(x[:split],y[:split]))
    means=hourly.iloc[:split].groupby(hourly.timestamp.iloc[:split].dt.hour).aircraft.mean()
    baseline=means.loc[hourly.timestamp.iloc[split:].dt.hour].to_numpy()
    report=dict(model='Calendar ridge regression, alpha=10',dataset_provenance=['real nycflights13 airline departures; JFK activity proxy'],
        real_world_validated=False,domain='airline departures, not private aviation or FBO arrivals',
        rows=len(hourly),train_rows=split,test_rows=len(y)-split,train_end=str(hourly.timestamp.iloc[split-1]),
        test_start=str(hourly.timestamp.iloc[split]),test_end=str(hourly.timestamp.iloc[-1]),
        metrics={'aircraft':dict(mae=float(abs(predicted-y[split:]).mean()),
            baseline_mae=float(abs(baseline-y[split:]).mean()),rmse=float(np.sqrt(((predicted-y[split:])**2).mean())))},
        source_url=URL,documentation_url=DOC,license='CC0 (nycflights13 package DESCRIPTION)',
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),audit=audit,
        limitations=['2013 JFK commercial departures only; old and different from FBO operations',
            'Observed airline holdout evaluation is not FBO validation',
            'FBO scale, event surge, passenger ratios, fueling ratios and service times remain assumptions'],
        inference_reference='2013-02-04 through 2013-02-10 calendar profile; illustrative replay, not future prediction')
    (output/'real_forecast.json').write_text(json.dumps(dict(coefficients=fit(x,y).tolist(),report=report),indent=2),encoding='utf-8')
    evaluation=hourly.iloc[split:].copy()
    evaluation['model_prediction']=predicted;evaluation['baseline_prediction']=baseline
    evaluation.to_csv(output/'real_forecast_holdout.csv',index=False)
    return report

def predict():
    artifact=json.loads((ROOT/'real_forecast.json').read_text(encoding='utf-8'))
    dates=pd.date_range('2013-02-04',periods=168,freq='h')
    return np.maximum(0,features(dates)@np.array(artifact['coefficients'])),artifact['report']

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    print(json.dumps(train(download=args.download),indent=2))
