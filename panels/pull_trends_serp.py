from serpapi.google_search import GoogleSearch
import pandas as pd
import time, os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SERPAPI_KEY')

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
all_rows = []

# Skip already pulled cities
existing_cities = []
if os.path.exists('data/raw/trends_raw.csv'):
    existing = pd.read_csv('data/raw/trends_raw.csv', index_col=0).reset_index()
    existing_cities = existing['city'].unique().tolist()
    print(f'Already have: {existing_cities}')

for city in cities:
    if city['city'] in existing_cities:
        print(f"Skipping {city['city']}")
        continue

    print(f"Pulling {city['city']}...")
    city_scores = {}

    for kw in keywords:
        try:
            params = {
                'engine': 'google_trends',
                'q': kw,
                'geo': city['geo'],
                'date': 'today 3-m',
                'api_key': API_KEY
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            timeline = results.get('interest_over_time', {}).get('timeline_data', [])
            if timeline:
                avg = sum(
                    int(t['values'][0]['extracted_value'])
                    for t in timeline
                ) / len(timeline)
                city_scores[kw] = avg
                print(f"  {kw}: {avg:.1f}")
            time.sleep(2)
        except Exception as e:
            print(f"  ERROR {kw}: {e}")
            city_scores[kw] = 0

    if city_scores:
        row = {'city': city['city']}
        row.update(city_scores)
        all_rows.append(row)

if all_rows:
    new_df = pd.DataFrame(all_rows)
    if existing_cities:
        old_df = pd.read_csv('data/raw/trends_raw.csv', index_col=0).reset_index()
        final = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final = new_df
    os.makedirs('data/raw', exist_ok=True)
    final.to_csv('data/raw/trends_serp.csv', index=False)
    print(f'SAVED {len(final)} rows')