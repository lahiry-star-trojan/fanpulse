"""
probe_teams.py — TEST candidate fandom keywords WITHOUT touching the live set.

A team earns a heatmap column only if its US search DISCRIMINATES between
metros: high top value AND wide spread (signal points at specific cities).
Flat-but-present (like Portugal: top=38, all cities ~37) = noise, not signal.

Reuses pull_keyword + match logic from pull_trends_v2 so the numbers are
directly comparable to the live pull. Prints a verdict per team.
Does NOT write any CSV. Read-only probe.

Run from repo root:  python panels/probe_teams.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from pull_trends_v2 import pull_keyword  # reuse exact pull + city-match logic

# Candidates to test (NOT yet in the live set):
CANDIDATES = [
    'Ecuador soccer',
    'Morocco soccer',
    'South Korea soccer',
    'France soccer',
    'Sweden soccer',
    'Australia soccer',
]

# Benchmarks from the live pull, for context when reading verdicts:
#   Brazil  (PROMOTED): top metro 92, sharp  -> good
#   Portugal (CUT):     top metro 38, flat   -> noise


def spread_stats(city_vals):
    """Return (top_city, top_val, spread, n_meaningful)."""
    if not city_vals:
        return (None, 0, 0, 0)
    items = sorted(city_vals.items(), key=lambda kv: kv[1], reverse=True)
    vals = [v for _, v in items]
    top_city, top_val = items[0]
    spread = max(vals) - min(vals)
    # how many cities clear half the top value = is the signal concentrated?
    n_meaningful = sum(1 for v in vals if v >= top_val * 0.5)
    return (top_city, top_val, spread, n_meaningful, items[:3])


def verdict(top_val, spread):
    """Promote rule: needs real magnitude AND real spread."""
    if top_val >= 60 and spread >= 40:
        return 'PROMOTE  ✅  (strong + discriminating)'
    if top_val >= 45 and spread >= 30:
        return 'MAYBE    🟡  (decent — your call)'
    return 'CUT      ❌  (too flat / low, like Portugal)'


def main():
    print('Probing candidate teams (read-only, no CSV written)\n')
    print('Benchmark from live pull: Brazil top=92 sharp ✅ | Portugal top=38 flat ❌\n')
    print(f'{"keyword":22s} {"top metro":14s} {"top":>4s} {"spread":>7s}  verdict')
    print('-' * 78)
    rows = []
    for kw in CANDIDATES:
        try:
            city_vals, _ = pull_keyword(kw)
        except Exception as e:
            print(f'{kw:22s}  ! pull failed: {e}')
            continue
        top_city, top_val, spread, n_meaningful, top3 = spread_stats(city_vals)
        print(f'{kw:22s} {str(top_city):14s} {top_val:4.0f} {spread:7.0f}  '
              f'{verdict(top_val, spread)}')
        print(f'{"":22s}   top3: {[(c, int(v)) for c, v in top3]}')
        rows.append((kw, top_val, spread))
        time.sleep(1)  # be gentle on the API
    print('\nPromote the ✅ rows (and 🟡 if you want). Tell me which; '
          'I wire them into both files.')


if __name__ == '__main__':
    main()
