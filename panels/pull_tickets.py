"""
pull_tickets.py — pull World Cup event resale stats from the SeatGeek API.

Requires a SeatGeek client ID (free, from https://seatgeek.com/account/develop).
Put it in .env as:  SEATGEEK_CLIENT_ID=xxxxx

Pulls per-event lowest_price / average_price / listing_count — i.e. live
secondary-market stats that (unlike FIFA's flat face-value card) should vary
by match. Saves to data/raw/seatgeek_raw.csv with source='SeatGeek'.

Run from repo root:  python panels/pull_tickets.py
"""
import requests, pandas as pd, time, os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('SEATGEEK_CLIENT_ID')

queries = [
    'FIFA World Cup', 'World Cup 2026',
    'World Cup Los Angeles', 'World Cup New York', 'World Cup Dallas',
    'World Cup Miami', 'World Cup Seattle', 'World Cup Atlanta',
    'World Cup Boston', 'World Cup Houston', 'World Cup Kansas City',
    'World Cup Philadelphia', 'World Cup San Francisco',
]

def main():
    if not CLIENT_ID:
        print('NO SEATGEEK_CLIENT_ID in .env — register at '
              'https://seatgeek.com/account/develop and add it. Aborting.')
        return

    all_events, seen = [], set()
    for query in queries:
        print(f'Searching: {query}')
        params = {
            'client_id': CLIENT_ID,      # <-- the missing auth
            'q': query,
            'per_page': 25,
            'type': 'soccer_match',      # narrow to matches where possible
        }
        try:
            resp = requests.get('https://api.seatgeek.com/2/events', params=params, timeout=20)
        except Exception as e:
            print(f'  request error: {e}'); continue
        print(f'  Status: {resp.status_code}')
        if resp.status_code != 200:
            # surface the body once — tells us if it's auth vs quota vs empty
            print('  body:', resp.text[:200]); 
            time.sleep(2); continue
        events = resp.json().get('events', [])
        print(f'  Found: {len(events)} events')
        for e in events:
            eid = e.get('id')
            if eid in seen:
                continue
            seen.add(eid)
            title = e.get('title', '')
            # keep only things that look like WC matches
            if 'world cup' not in title.lower() and 'fifa' not in title.lower():
                continue
            st = e.get('stats', {}) or {}
            all_events.append({
                'title':        title,
                'venue':        (e.get('venue') or {}).get('name'),
                'city':         (e.get('venue') or {}).get('city'),
                'date':         e.get('datetime_utc'),
                'lowest_price': st.get('lowest_price'),
                'avg_price':    st.get('average_price'),
                'median_price': st.get('median_price'),
                'listings':     st.get('listing_count'),
                'source':       'SeatGeek',
            })
        time.sleep(2)

    if not all_events:
        print('\nNO WC EVENTS RETURNED. Either SeatGeek has no WC inventory, '
              'or the query/type filter is too narrow. Pivot to FIFA teardown.')
        return

    df = pd.DataFrame(all_events)
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/seatgeek_live.csv', index=False)   # NEW file, don't clobber FIFA card
    print(f'\nSAVED {len(df)} WC events -> data/raw/seatgeek_live.csv')
    # THE decisive check: does price vary by match?
    priced = df.dropna(subset=['lowest_price'])
    print(f'events with a real lowest_price: {len(priced)}')
    if len(priced):
        print(f'distinct lowest_price values: {priced["lowest_price"].nunique()}')
        print(priced[['title','city','lowest_price','listings']]
              .sort_values('lowest_price', ascending=False).head(15).to_string(index=False))

if __name__ == '__main__':
    main()
