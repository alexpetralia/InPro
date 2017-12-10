import numpy as np
import pandas as pd
import json
import os

def lazy_div(df):
    """Divide if possible, else return null"""
    try:
        return float(df['price']) / float(df['net_profit'])
    except (ValueError, ZeroDivisionError):
        return np.nan

def main():
    """Main"""
    PATH = '/home/alex/Desktop/InPro/scrape/lines.json'
    with open(path, 'r') as f:
        j = json.load()

    # Get data
    df = pd.DataFrame(j['data'])
    df['multiple'] = df.apply(lazy_div, axis=1)

    # Analyze 1
    groups = df.groupby(['niche', 'site_age'])['multiple']
    x = groups.agg({'avg_pe': np.mean, 'n': np.size})
    x = x[x['n'] >= 3]
    x = x.sort_values('avg_pe')

    # Analyze 2
    groups = df.groupby(['niche'])['multiple']
    y = groups.agg({'avg_pe': np.mean, 'n': np.size})
    y = y[y['n'] >= 3]
    y = y.sort_values('avg_pe')

if __name__ == '__main__':

    main()
