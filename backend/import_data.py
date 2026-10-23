"""Validate a later hourly demand CSV. Never relabel imported data as observed."""
import argparse
from pathlib import Path
import pandas as pd

def validate(path):
    data = pd.read_csv(path)
    required = ['hour','aircraft','passengers','fuel_requests','provenance']
    missing = set(required)-set(data.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}; actual columns: {list(data.columns)}')
    if len(data)!=168 or list(data.hour)!=list(range(168)):
        raise ValueError('Expected exactly 168 ordered unique hourly rows numbered 0–167')
    for column in required[1:4]:
        values = pd.to_numeric(data[column],errors='raise')
        if values.isna().any() or not values.between(0,1e6).all():
            raise ValueError(f'Invalid nonnegative finite values in {column}')
    if data.provenance.isna().any() or data.provenance.str.strip().eq('').any():
        raise ValueError('Every row needs provenance')
    return data

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('csv',type=Path)
    args=parser.parse_args()
    data=validate(args.csv)
    print(f'Validated {len(data)} rows. Columns: {list(data.columns)}. No data overwritten.')
