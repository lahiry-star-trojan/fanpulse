"""
Corrected demand pull for Fan Pulse.

WHY THIS REPLACES pull_trends_serp.py
-------------------------------------
The old pull queried each city separately with a STATE geo (US-CA, US-TX...),
and each (city, keyword) as its own time-series. Two fatal problems:
  1. State geo: 'Los Angeles' and 'San Francisco' were both US-CA -> identical
     data. The city map was partly state data wearing city names.
  2. Independent normalization: Google Trends scales every query to its own
     peak = 100, so values from different queries are NOT on a common scale.
     The cross-city ranking compared numbers that never shared an axis.

THE FIX
-------
For each keyword, ONE 'Interest by region' (GEO_MAP) query at geo=US with
region=DMA. Google returns every metro on a SINGLE 0-100 scale (100 = the
metro that over-indexes most on that term, relative to its own search base).
That is the legitimate version of "per capita": it already controls for how
big each metro's search activity is. No population division needed.

We then composite across keywords (each keyword map is comparable across
metros) and group keywords by INTENT so the output is actionable
(commercial / fandom / logistics) instead of "FIFA 2026 is biggest" (which
is tautological — it's the event's name).

NOTE: I could not run this against the live API. It follows SerpAPI's
documented GEO_MAP response shape and is defensive, but the first run is the
test. It PRINTS unmatched DMA names + raw structure so we can adjust the
city matchers or field names to whatever the API actually returns.

OUTPUT (new files — does NOT overwrite trends_processed.csv):
  data/raw/trends_geo_raw.csv        long: keyword, bucket, dma, city, value
  data/processed/trends_geo.csv      city-level: demand_score(+norm) + buckets
"""

from serpapi.google_search import GoogleSearch
import pandas as pd
import time, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('SERPAPI_KEY')

# ── INTENT-BUCKETED KEYWORDS ──────────────────────────────────────
# TUNE THESE. Grouped by what the search reveals about the searcher.
# Keep it tight: each keyword = 1 API call.
KEYWORDS = {
    # commercial now carries the secondary-market (resale) signal — the
    # two-sided-marketplace pricing spine, not just primary tickets.
    'commercial': ['World Cup tickets', 'World Cup resale tickets'],
    # fandom expanded to the teams that actually move US search 5 days in:
    # diaspora corridors (Mexico/Argentina/Brazil) + USMNT + Ronaldo effect.
    'fandom':     ['USMNT', 'Mexico soccer', 'Argentina soccer',
                   'Brazil soccer', 'Morocco soccer', 'Ecuador soccer',
                   'South Korea soccer'],
    # logistics tightened: schedule (spikes on match days) + stadiums
    # (discriminates by host city). Dropped host-cities (redundant w/ stadiums).
    'logistics':  ['World Cup schedule', 'World Cup stadiums'],
    # NEW: live bottom-of-funnel "I want in right now" intent.
    'watch':      ['World Cup tickets near me', 'how to watch World Cup'],
}
# Dropped 'FIFA 2026' on purpose — it's the event name, so it always wins and
# tells a strategist nothing. Re-add if you want a raw-awareness baseline.

# ── CITY ← DMA MATCHING ───────────────────────────────────────────
# DMA (metro) names from Google differ from our city labels. We match by
# substring so we don't have to guess exact DMA strings. LA and SF are now
# DIFFERENT DMAs, so the identical-data bug is gone.
CITY_MATCH = {
    'Los Angeles':   ['los angeles'],
    'San Francisco': ['san francisco'],
    'New York':      ['new york'],
    'Miami':         ['miami'],
    'Dallas':        ['dallas'],
    'Houston':       ['houston'],
    'Seattle':       ['seattle'],
    'Atlanta':       ['atlanta'],
    'Boston':        ['boston'],
    'Philadelphia':  ['philadelphia'],
    'Kansas City':   ['kansas city'],
}


def match_city(dma_name):
    low = str(dma_name).lower()
    for city, needles in CITY_MATCH.items():
        if any(n in low for n in needles):
            return city
    return None


def parse_region_value(item):
    """Pull the numeric value out of a GEO_MAP region row, defensively.
    SerpAPI returns extracted_value (preferred) or value, sometimes as a
    single-element list (one entry per compared query)."""
    ev = item.get('extracted_value', item.get('value'))
    if isinstance(ev, list):
        ev = ev[0] if ev else 0
    try:
        return float(ev)
    except (TypeError, ValueError):
        return 0.0


def pull_keyword(keyword):
    """One GEO_MAP query -> {city: value} on a common 0-100 scale."""
    params = {
        'engine':    'google_trends',
        'q':         keyword,
        'data_type': 'GEO_MAP_0',      # Interest by region, single term
        'geo':       'US',
        'region':    'DMA',            # metro granularity
        'date':      'today 3-m',
        'api_key':   API_KEY,
    }
    results = GoogleSearch(params).get_dict()
    regions = results.get('interest_by_region', [])
    if not regions:
        print(f"  ! no interest_by_region for '{keyword}'. "
              f"top-level keys: {list(results.keys())}")
        return {}, []

    city_vals, unmatched = {}, []
    for item in regions:
        dma  = item.get('location', '')
        city = match_city(dma)
        if city:
            city_vals[city] = parse_region_value(item)
        else:
            unmatched.append(dma)
    return city_vals, unmatched


def main():
    if not API_KEY:
        raise SystemExit('SERPAPI_KEY not found in environment / .env')

    rows, all_unmatched = [], set()
    for bucket, kws in KEYWORDS.items():
        for kw in kws:
            print(f"Pulling [{bucket}] {kw} ...")
            try:
                city_vals, unmatched = pull_keyword(kw)
                all_unmatched.update(unmatched)
                for city, val in city_vals.items():
                    rows.append({'keyword': kw, 'bucket': bucket,
                                 'city': city, 'value': val})
                print(f"  matched {len(city_vals)}/{len(CITY_MATCH)} cities")
            except Exception as e:
                print(f"  ERROR on '{kw}': {e}")
            time.sleep(2)

    if not rows:
        raise SystemExit('No data pulled — check API key / response shape above.')

    long = pd.DataFrame(rows)
    os.makedirs('data/raw', exist_ok=True)
    long.to_csv('data/raw/trends_geo_raw.csv', index=False)

    # city x keyword (missing metro for a term => 0 interest)
    wide = long.pivot_table(index='city', columns='keyword',
                            values='value', fill_value=0)

    # per-bucket composite (mean of that bucket's keywords)
    out = pd.DataFrame(index=wide.index)
    for bucket, kws in KEYWORDS.items():
        cols = [k for k in kws if k in wide.columns]
        out[bucket] = wide[cols].mean(axis=1) if cols else 0.0

    # overall demand = mean across all keywords (all on comparable 0-100 maps)
    out['demand_score'] = wide.mean(axis=1)
    lo, hi = out['demand_score'].min(), out['demand_score'].max()
    out['demand_score_norm'] = (100 * (out['demand_score'] - lo) / (hi - lo)
                                if hi > lo else 0.0)
    # placeholder so the (not-yet-rewritten) panel1 still loads; real WoW
    # needs a separate time-series pull, handled when we rewrite the panel.
    out['wow_change_pct'] = pd.NA

    out = out.reset_index().round(2)
    os.makedirs('data/processed', exist_ok=True)
    out.to_csv('data/processed/trends_geo.csv', index=False)

    # ── verification print ───────────────────────────────────────
    print("\n=== DEMAND (corrected, cross-city comparable) ===")
    print(out.sort_values('demand_score_norm', ascending=False).to_string(index=False))
    print(f"\nCities found: {out['city'].nunique()}/{len(CITY_MATCH)}")
    if all_unmatched:
        print("Unmatched DMA names (extend CITY_MATCH if a host city is here):")
        for u in sorted(all_unmatched):
            print(f"  - {u}")


if __name__ == '__main__':
    main()
