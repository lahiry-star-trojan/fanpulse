"""
build_match_demand.py — per-match DEMAND signal from team search interest.

Joins the ticket table's fixtures (title = "TeamA vs TeamB") to the demand
data (trends_geo_raw) so each match gets a 0-100 demand number. This is the
DEMAND side of the demand-vs-price mismatch; price/supply comes from the
ticket table itself in the panel.

Two demand definitions, switch with SIGNAL:
  'national'  = each team's mean interest across all metros (one number/team)
  'hostcity'  = each team's interest IN the match's host city (ties to venue)

Untracked teams (Austria, Jordan...) get BASELINE — we only track 7 teams,
so a match of two untracked teams scores low, which is honest (we have no
demand read on them) not a bug.

Run from repo root:  python panels/build_match_demand.py
Output: data/processed/match_demand.csv
"""
import pandas as pd
import os

SIGNAL = 'hostcity'     # data showed this ties demand to venue (on-spine) and
                        # avoids the national-mean distortion (Argentina problem)
BASELINE = 15           # demand for teams we don't track (low, honest)

# placeholder "fixtures" that aren't real matchups yet — filter these out
def is_placeholder(title):
    s = str(title)
    if ' vs ' not in s:
        return True
    if any(tok in s for tok in ['Winner', 'Playoff']):
        return True
    for part in s.split(' vs '):
        p = part.strip()
        if p.lstrip('WRU').isdigit():   # "W95", "RU101", "W100"
            return True
    return False

# bridge: ticket-title team name -> demand keyword in trends_geo_raw
NAME_TO_KW = {
    'Argentina': 'Argentina soccer',
    'Brazil':    'Brazil soccer',
    'Mexico':    'Mexico soccer',
    'Morocco':   'Morocco soccer',
    'Ecuador':   'Ecuador soccer',
    'South Korea':'South Korea soccer',
    'USA':       'USMNT',
}

# map ticket venue-city names to the metro names used in trends_geo_raw.
# Mexican/Canadian host cities aren't in our US-metro demand data -> baseline.
CITY_NORM = {
    'New York/New Jersey': 'New York',
    'San Francisco Bay Area': 'San Francisco',
    'Bay Area': 'San Francisco',
}

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
TICKETS = os.path.join(ROOT, 'data/processed/tickets_by_category.csv')
TRENDS  = os.path.join(ROOT, 'data/raw/trends_geo_raw.csv')
OUT     = os.path.join(ROOT, 'data/processed/match_demand.csv')


def load_demand_lookups(trends):
    """Return (national_mean_by_kw, hostcity_value_by_(kw,city))."""
    national = trends.groupby('keyword')['value'].mean().to_dict()
    hostcity = {(r.keyword, r.city): r.value for r in trends.itertuples()}
    return national, hostcity


def team_demand(team, city, national, hostcity):
    """Demand for one team in one match. Untracked -> BASELINE."""
    kw = NAME_TO_KW.get(team)
    if kw is None:
        return BASELINE, False  # not tracked
    if SIGNAL == 'hostcity':
        c = CITY_NORM.get(str(city), str(city))   # normalize venue -> trends metro
        v = hostcity.get((kw, c))
        return (float(v) if v is not None else BASELINE), True
    return float(national.get(kw, BASELINE)), True


def main():
    tickets = pd.read_csv(TICKETS)
    trends  = pd.read_csv(TRENDS)
    national, hostcity = load_demand_lookups(trends)

    # one row per unique fixture (title), keep its city/date/stage,
    # drop placeholder/not-yet-determined matchups
    fixtures = (tickets[['title', 'city', 'date', 'stage']]
                .dropna(subset=['title']).drop_duplicates('title'))
    fixtures = fixtures[~fixtures['title'].apply(is_placeholder)]

    rows = []
    for f in fixtures.itertuples():
        if ' vs ' not in f.title:
            continue
        a, b = [s.strip() for s in f.title.split(' vs ', 1)]
        da, ta = team_demand(a, f.city, national, hostcity)
        db, tb = team_demand(b, f.city, national, hostcity)
        rows.append({
            'title': f.title, 'city': f.city, 'date': f.date, 'stage': f.stage,
            'team_a': a, 'team_b': b,
            'demand_a': round(da, 1), 'demand_b': round(db, 1),
            'demand_score': round(da + db, 1),      # match demand = sum
            'tracked_teams': int(ta) + int(tb),     # 0,1,2 — how much we actually know
        })

    out = pd.DataFrame(rows).sort_values('demand_score', ascending=False)
    out.to_csv(OUT, index=False)

    # console verification — eyeball before trusting the join
    print(f"SIGNAL = {SIGNAL}  | {len(out)} fixtures\n")
    print("TOP 8 by demand:")
    print(out[['title','city','demand_score','tracked_teams']].head(8).to_string(index=False))
    print("\nBOTTOM 5 by demand:")
    print(out[['title','city','demand_score','tracked_teams']].tail(5).to_string(index=False))
    print(f"\nfixtures with >=1 tracked team: {(out.tracked_teams>0).sum()} / {len(out)}")
    print(f"written -> {OUT}")


if __name__ == '__main__':
    main()
