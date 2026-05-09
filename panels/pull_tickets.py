import requests, pandas as pd, time, os

all_events = []

queries = [
    'FIFA World Cup 2026 Miami',
    'FIFA World Cup 2026 Dallas',
    'FIFA World Cup 2026 Los Angeles',
    'FIFA World Cup 2026 New York',
    'FIFA World Cup 2026 Houston',
    'FIFA World Cup 2026 San Francisco',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

for query in queries:
    print(f'Searching: {query}')
    params = {
        'q': query,
        'per_page': 10,
    }
    resp = requests.get(
        'https://api.seatgeek.com/2/events',
        params=params,
        headers=headers
    )
    print(f'  Status: {resp.status_code}')
    if resp.status_code == 200:
        events = resp.json().get('events', [])
        print(f'  Found: {len(events)} events')
        for e in events:
            all_events.append({
                'title':        e.get('title'),
                'venue':        e.get('venue', {}).get('name'),
                'city':         e.get('venue', {}).get('city'),
                'date':         e.get('datetime_utc'),
                'lowest_price': e.get('stats', {}).get('lowest_price'),
                'avg_price':    e.get('stats', {}).get('average_price'),
                'median_price': e.get('stats', {}).get('median_price'),
                'listings':     e.get('stats', {}).get('listing_count'),
            })
    time.sleep(3)

if all_events:
    df = pd.DataFrame(all_events)
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/seatgeek_raw.csv', index=False)
    print(f'SAVED {len(df)} events')
else:
    print('NO DATA — will use manual fallback')