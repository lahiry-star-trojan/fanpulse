"""
pull_team_national.py — national US search interest per team, on ONE shared
scale, for the pricing-scatter demand axis.

Google Trends compares <=5 terms on a shared 0-100 scale per query. To put
MANY teams on one scale, every batch includes a constant ANCHOR team
(Brazil); we then rescale each batch by the anchor so all teams are
comparable across batches.

Output: data/processed/team_national_demand.csv  (team, national_interest)

Run from repo root:  python panels/pull_team_national.py
"""
from serpapi.google_search import GoogleSearch
import pandas as pd
import time, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('SERPAPI_KEY')

ANCHOR = 'Brazil soccer'
# teams worth plotting: tracked + big-search nations that have resale prices.
# minnows (Uzbekistan, Cape Verde, DR Congo, Curacao...) dropped — they'd sit
# at ~0 and add noise, not signal.
TEAMS = [
    'Mexico soccer','Argentina soccer','USMNT','Morocco soccer','Ecuador soccer',
    'South Korea soccer','Spain soccer','France soccer','Germany soccer',
    'England soccer','Portugal soccer','Netherlands soccer','Belgium soccer',
    'Japan soccer','Uruguay soccer','Colombia soccer','Croatia soccer',
    'Senegal soccer','Switzerland soccer','Canada soccer','Australia soccer',
]

def batch_interest(terms):
    """National US interest (mean over 3mo) for up to 5 terms, shared scale."""
    params = {
        'engine':'google_trends','q':','.join(terms),
        'data_type':'TIMESERIES','geo':'US','date':'today 3-m','api_key':API_KEY,
    }
    data = GoogleSearch(params).get_dict()
    series = data.get('interest_over_time', {}).get('timeline_data', [])
    sums = {t:0.0 for t in terms}; n=0
    for point in series:
        for v in point.get('values', []):
            q = v.get('query'); val = v.get('extracted_value', 0)
            if q in sums: sums[q]+=val
        n+=1
    return {t:(sums[t]/n if n else 0) for t in terms}

def main():
    others = [t for t in TEAMS if t != ANCHOR]
    rows = {}
    # batches of 4 others + anchor = 5 terms each
    for i in range(0, len(others), 4):
        chunk = others[i:i+4]
        terms = [ANCHOR] + chunk
        print(f'batch: {terms}')
        vals = batch_interest(terms)
        anchor_val = vals.get(ANCHOR, 0) or 1
        for t in chunk:
            # rescale by anchor so batches share a scale (anchor=100 ref)
            rows[t] = round(100 * vals[t] / anchor_val, 1)
        time.sleep(2)
    rows[ANCHOR] = 100.0  # anchor is the reference

    df = (pd.DataFrame([{'team':k,'national_interest':v} for k,v in rows.items()])
          .sort_values('national_interest', ascending=False))
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/team_national_demand.csv', index=False)
    print('\n'+df.to_string(index=False))
    print(f'\nwritten -> data/processed/team_national_demand.csv')

if __name__ == '__main__':
    main()
