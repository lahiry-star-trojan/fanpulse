"""
build_pricing_scatter.py — final join for the pricing-mismatch scatter.

demand (national, both teams summed) x price (resale floor) per match.
Uses team_national_demand.csv (shared-scale national interest) so ANY match
with two known teams gets a demand score, maximizing plottable points.

Output: data/processed/pricing_scatter.csv
Run from repo root:  python panels/build_pricing_scatter.py
"""
import pandas as pd
import os, re

HERE = os.path.dirname(__file__); ROOT = os.path.dirname(HERE)
DEMAND = os.path.join(ROOT, 'data/processed/team_national_demand.csv')
PRICES = os.path.join(ROOT, 'data/raw/seatgeek_resale.csv')
OUT    = os.path.join(ROOT, 'data/processed/pricing_scatter.csv')

# map ticket team-name -> demand keyword
NAME_TO_TEAM = {
    'usa':'USMNT','mexico':'Mexico soccer','argentina':'Argentina soccer',
    'brazil':'Brazil soccer','morocco':'Morocco soccer','ecuador':'Ecuador soccer',
    'south korea':'South Korea soccer','spain':'Spain soccer','france':'France soccer',
    'germany':'Germany soccer','england':'England soccer','portugal':'Portugal soccer',
    'netherlands':'Netherlands soccer','belgium':'Belgium soccer','japan':'Japan soccer',
    'uruguay':'Uruguay soccer','colombia':'Colombia soccer','croatia':'Croatia soccer',
    'senegal':'Senegal soccer','switzerland':'Switzerland soccer','canada':'Canada soccer',
    'australia':'Australia soccer',
}

def teams_from_title(title):
    base = str(title).split(' - ')[0]
    if ' vs ' not in base: return None, None
    a, b = [x.strip().lower() for x in base.split(' vs ', 1)]
    return a, b

def main():
    dem = pd.read_csv(DEMAND).set_index('team')['national_interest'].to_dict()
    px = pd.read_csv(PRICES)

    BASELINE = 8.0   # unknown/minnow team — low but non-zero so match still plots

    rows = []
    for r in px.itertuples():
        a, b = teams_from_title(r.title)
        if not a: continue
        ka, kb = NAME_TO_TEAM.get(a), NAME_TO_TEAM.get(b)
        price = getattr(r, 'lowestPrice', None)
        if pd.isna(price): continue            # no price = can't plot, skip
        # known team uses its demand; unknown uses baseline (match still counts)
        da = dem.get(ka, BASELINE) if ka else BASELINE
        db = dem.get(kb, BASELINE) if kb else BASELINE
        demand = da + db
        # flag how much real demand signal the match has (2 = both known)
        known = int(ka is not None) + int(kb is not None)
        clean = str(r.title).split(' - ')[0].strip()
        rows.append({'match': clean, 'demand': round(demand,1),
                     'price': int(price), 'teams_known': known})

    df = pd.DataFrame(rows).drop_duplicates('match')
    # mismatch = demand rank - price rank (pct), + label
    df['demand_rank'] = df['demand'].rank(pct=True)
    df['price_rank'] = df['price'].rank(pct=True)
    df['mismatch'] = (df['demand_rank'] - df['price_rank']).round(3)
    def lab(m): return 'Underpriced' if m>=0.2 else 'Overpriced' if m<=-0.2 else 'Efficient'
    df['signal'] = df['mismatch'].apply(lab)
    df = df.sort_values('mismatch', ascending=False)
    df.to_csv(OUT, index=False)

    print(f'PLOTTABLE matches: {len(df)}\n')
    print(df[['match','demand','price','teams_known','signal']].to_string(index=False))
    print(f'\nwritten -> {OUT}')

if __name__ == '__main__':
    main()
