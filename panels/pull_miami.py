from pytrends.request import TrendReq
import pandas as pd
import time

pytrends = TrendReq(hl='en-US', tz=360)
keywords = ['World Cup tickets','FIFA 2026','USMNT','Argentina soccer','Mexico soccer']

print('Pulling Miami...')
time.sleep(30)
pytrends.build_payload(keywords, timeframe='today 3-m', geo='US-FL')
time.sleep(65)
df = pytrends.interest_over_time()

if not df.empty:
    df['city'] = 'Miami'
    # Append to existing trends_raw.csv
    existing = pd.read_csv('data/raw/trends_raw.csv', index_col=0)
    combined = pd.concat([existing, df])
    combined.to_csv('data/raw/trends_raw.csv')
    print(f'Miami added. Total rows: {len(combined)}')
else:
    print('Still empty — wait 5 mins and retry')