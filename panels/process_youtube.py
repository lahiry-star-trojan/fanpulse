import pandas as pd
import os
import re
from collections import Counter

df = pd.read_csv('data/raw/youtube_raw.csv')

# Tag by team
team_kw = {
    'Mexico':    ['mexico','el tri','chicharito'],
    'Argentina': ['argentina','messi','albiceleste'],
    'USMNT':     ['usmnt','usa soccer','pulisic','us soccer','american'],
    'Brazil':    ['brazil','brasil','neymar'],
    'England':   ['england','three lions','kane'],
}

city_kw = {
    'Miami':         ['miami'],
    'Los Angeles':   ['los angeles',' la ','sofi'],
    'Dallas':        ['dallas'],
    'New York':      ['new york','metlife','nyc'],
    'Houston':       ['houston'],
    'San Francisco': ['san francisco','levi'],
}

def tag(text, kw_dict):
    text = str(text).lower()
    return [k for k, kws in kw_dict.items()
            if any(w in text for w in kws)]

full = df['text'].fillna('')
df['teams']  = full.apply(lambda t: tag(t, team_kw))
df['cities'] = full.apply(lambda t: tag(t, city_kw))

os.makedirs('data/processed', exist_ok=True)
df.to_csv('data/processed/youtube_tagged.csv', index=False)
print(f'Tagged {len(df)} comments')
print(df['sentiment'].value_counts())