"""
Qualitative keyword pull for Fan Pulse — the "what are people actually
searching?" layer that the flat volume scores can't give.

WHY
---
GEO_MAP volumes barely vary across major metros (everyone ~30), so they tell
you WHERE demand is but not WHAT it is. RELATED_QUERIES returns the real search
phrases, split into:
  - top    = established searches (mostly generic awareness)
  - rising = fastest-growing searches = the actual emerging-demand signal

We tag each phrase into a funnel stage so a flat number becomes a story:
  awareness -> fandom/engagement -> logistics -> commercial(buying)

SCOPE / HONEST LIMITS
---------------------
- National (geo=US). Per-metro related queries via Trends/DMA are unreliable,
  so we keep qualitative = national, quantitative (GEO_MAP) = per-city.
- Could NOT run against the live API here. Built to SerpAPI's RELATED_QUERIES
  shape, defensive, and PRINTS what it gets so we can adjust tagging after we
  see the real phrases. Rising 'value' can be "Breakout" (a string) — handled.

OUTPUT:
  data/raw/related_queries_raw.csv   seed, kind(top|rising), query, value, stage
"""

from serpapi.google_search import GoogleSearch
import pandas as pd
import time, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('SERPAPI_KEY')

# Seeds chosen to span the funnel — tune freely.
SEEDS = [
    'FIFA World Cup 2026',     # awareness anchor
    'World Cup 2026 tickets',  # commercial anchor
    'World Cup 2026 schedule', # logistics anchor
    'USMNT',                   # fandom anchor
]

# First matching rule wins; otherwise 'awareness'. Crude on purpose — we
# refine these once we see the real phrases the API returns.
STAGE_RULES = [
    ('commercial', ['ticket', 'price', 'cost', 'buy', 'how much', 'hospitality',
                    'package', 'hotel', 'seat', 'resale', 'sale', 'presale',
                    'lottery', 'visa']),
    ('logistics',  ['schedule', 'fixture', 'stadium', 'venue', 'date', 'group',
                    'draw', 'host', 'location', 'where', 'when', 'calendar',
                    'match', 'final', 'opening', 'city', 'cities']),
    ('fandom',     ['messi', 'ronaldo', 'usmnt', 'usa', 'argentina', 'mexico',
                    'brazil', 'england', 'france', 'team', 'squad', 'roster',
                    'player', 'jersey', 'kit', 'qualify', 'qualified']),
]


def stage_of(query):
    q = str(query).lower()
    for stage, kws in STAGE_RULES:
        if any(k in q for k in kws):
            return stage
    return 'awareness'


def num(item):
    """extracted_value (number) if present, else value (may be 'Breakout')."""
    ev = item.get('extracted_value')
    if ev is not None:
        return ev
    return item.get('value', '')


def pull_related(seed):
    params = {
        'engine':    'google_trends',
        'q':         seed,
        'data_type': 'RELATED_QUERIES',
        'geo':       'US',
        'date':      'today 3-m',
        'api_key':   API_KEY,
    }
    results = GoogleSearch(params).get_dict()
    rq = results.get('related_queries')
    if not rq:
        print(f"  ! no related_queries for '{seed}'. "
              f"top-level keys: {list(results.keys())}")
        return []
    rows = []
    for kind in ('top', 'rising'):
        for item in rq.get(kind, []) or []:
            query = item.get('query', '')
            rows.append({'seed': seed, 'kind': kind, 'query': query,
                         'value': num(item), 'stage': stage_of(query)})
    return rows


def main():
    if not API_KEY:
        raise SystemExit('SERPAPI_KEY not found in environment / .env')

    all_rows = []
    for seed in SEEDS:
        print(f"Pulling related queries for: {seed} ...")
        try:
            rows = pull_related(seed)
            all_rows.extend(rows)
            n_top  = sum(r['kind'] == 'top' for r in rows)
            n_rise = sum(r['kind'] == 'rising' for r in rows)
            print(f"  top={n_top}  rising={n_rise}")
        except Exception as e:
            print(f"  ERROR on '{seed}': {e}")
        time.sleep(2)

    if not all_rows:
        raise SystemExit('No related queries pulled — check key / shape above.')

    df = pd.DataFrame(all_rows)
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/related_queries_raw.csv', index=False)

    # ── verification print ───────────────────────────────────────
    print("\n=== RISING queries (the demand signal), by stage ===")
    rising = df[df['kind'] == 'rising']
    for stage in ['commercial', 'logistics', 'fandom', 'awareness']:
        qs = rising[rising['stage'] == stage]['query'].tolist()
        if qs:
            print(f"\n[{stage}]")
            for q in qs[:12]:
                print(f"  - {q}")

    print("\n=== stage mix (rising only) ===")
    print(rising['stage'].value_counts().to_string())
    print(f"\nSaved {len(df)} rows -> data/raw/related_queries_raw.csv")


if __name__ == '__main__':
    main()
