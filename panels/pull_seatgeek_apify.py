"""
pull_seatgeek_apify.py — real World Cup RESALE prices via the Apify SeatGeek
actor (bypasses DataDome, scrapes the actual site where prices live — the
public SeatGeek API returns empty stats for WC events).

Needs APIFY_TOKEN in .env (free account, Settings -> Integrations).
Actor: ai_solutionist/seatgeek-data-api (~$10/1000 events; ~16 matches = trivial).

Run from repo root:  python panels/pull_seatgeek_apify.py
Output: data/raw/seatgeek_resale.csv  (+ prints raw fields first so we map them)
"""
import requests, os, json, sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('APIFY_TOKEN')
ACTOR = 'ai_solutionist~seatgeek-data-api'
WC_URL = 'https://seatgeek.com/fifa-world-cup-tickets'

# the actor's input — start from the WC tickets page so it pulls all matches.
# (field names per actor README; if it rejects, we adjust from the error.)
ACTOR_INPUT = {
    'startUrls': [{'url': WC_URL}],
    'maxItems': 60,           # comfortably covers ~46 group-stage matches
    'includePricing': True,
}


def main():
    if not TOKEN:
        print('NO APIFY_TOKEN in .env — add it from Apify Console -> Settings '
              '-> Integrations. Aborting.')
        return

    url = (f'https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items'
           f'?token={TOKEN}')
    print(f'Running actor {ACTOR} on {WC_URL} ...')
    print('(this can take 30-90s — it spins a real browser)\n')

    try:
        resp = requests.post(url, json=ACTOR_INPUT, timeout=300)
    except Exception as e:
        print('request error:', e); return

    print('Status:', resp.status_code)
    if resp.status_code not in (200, 201):
        print('body:', resp.text[:500])
        print('\nIf 400: input field names are off — paste this and I will fix.')
        print('If 402: out of Apify credit. If 401: bad token.')
        return

    items = resp.json()
    if not items:
        print('Actor ran but returned 0 items. The startUrl or input may need '
              'adjusting — paste this output.')
        return

    # FIRST: show the raw shape so we map fields correctly (don't guess)
    print(f'Got {len(items)} items. Raw fields on first item:')
    print(json.dumps(items[0], indent=2)[:1200])
    print('\n--- full keys:', list(items[0].keys()))

    # save raw json for safety
    os.makedirs('data/raw', exist_ok=True)
    with open('data/raw/seatgeek_apify_raw.json', 'w') as f:
        json.dump(items, f, indent=2)

    # best-effort normalize — adjust keys after seeing the dump above
    df = pd.json_normalize(items)
    df.to_csv('data/raw/seatgeek_resale.csv', index=False)
    print(f'\nsaved {len(df)} rows -> data/raw/seatgeek_resale.csv')
    print('saved raw -> data/raw/seatgeek_apify_raw.json')
    # show any price-ish columns
    pricecols = [c for c in df.columns if any(k in c.lower()
                 for k in ['price','low','min','cost','amount'])]
    print('price-like columns found:', pricecols)
    if pricecols:
        titlecol = next((c for c in df.columns if 'title' in c.lower()
                         or 'name' in c.lower() or 'event' in c.lower()), df.columns[0])
        print(df[[titlecol]+pricecols].head(15).to_string(index=False))


if __name__ == '__main__':
    main()
