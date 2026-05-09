from pytrends.request import TrendReq
import pandas as pd
import time, os

pytrends = TrendReq(hl='en-US', tz=360)

cities = [
    {'city':'Los Angeles','geo':'US-CA'},
    {'city':'San Francisco','geo':'US-CA'},
    {'city':'Seattle','geo':'US-WA'},
    {'city':'Dallas','geo':'US-TX'},
    {'city':'Houston','geo':'US-TX'},
    {'city':'Kansas City','geo':'US-MO'},
    {'city':'Atlanta','geo':'US-GA'},
    {'city':'Miami','geo':'US-FL'},
    {'city':'New York','geo':'US-NY'},
    {'city':'Boston','geo':'US-MA'},
    {'city':'Philadelphia','geo':'US-PA'},
]

keywords = ['World Cup tickets','FIFA 2026','USMNT','Argentina soccer','Mexico soccer']
all_data = []

# Load existing data to skip already-pulled cities
existing_cities = []
if os.path.exists('data/raw/trends_raw.csv'):
    existing = pd.read_csv('data/raw/trends_raw.csv', index_col=0).reset_index()
    existing_cities = existing['city'].unique().tolist()
    all_data.append(existing)
    print(f'Already have: {existing_cities}')

for city in cities:
    if city['city'] in existing_cities:
        print(f"Skipping {city['city']} — already pulled")
        continue

    print(f"Pulling {city['city']}...")
    try:
        pytrends.build_payload(keywords, timeframe='today 3-m', geo=city['geo'])
        time.sleep(65)
        df = pytrends.interest_over_time()
        if not df.empty:
            df['city'] = city['city']
            all_data.append(df)
            print(f"  OK: {len(df)} rows")
            # Save after every city in case it crashes
            combined = pd.concat(all_data)
            combined.to_csv('data/raw/trends_raw.csv')
            print(f"  Saved progress")
        else:
            print(f"  Empty response — skipping")
    except Exception as e:
        print(f"  ERROR: {e} — waiting 120s")
        time.sleep(120)

print('DONE — trends_raw.csv updated')