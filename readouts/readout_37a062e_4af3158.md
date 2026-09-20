# Fan Pulse period readout

**Mid-tournament demand has surged +66% overall, but the comparison is structurally compromised — 3 keywords were dropped and 7 new ones added, making raw delta inflation the primary story, not organic growth.**

- Periods compared: `37a062e` to `4af3158`
- Confidence: **low**
- Comparison valid as measured: **no**
- Model: `claude-sonnet-4-6`

## Readout

**Period: May 22, 2026 (37a062e) → June 15, 2026 (4af3158)**

**Structural Warning First**
This is not a clean apples-to-apples comparison. The keyword instrument was substantially overhauled between the two snapshots. Three keywords were dropped (World Cup hospitality, World Cup host cities, World Cup packages) and seven were added (Brazil soccer, Ecuador soccer, Morocco soccer, South Korea soccer, World Cup resale tickets, World Cup tickets near me, how to watch World Cup). A new "watch" bucket was created. The fandom bucket went from 3 to 7 keywords. Any aggregate delta is heavily contaminated by this redesign. Treat everything below as signal-with-noise, not clean measurement.

---

**What is real and actionable across both periods (6 keywords in common)**

| Keyword | May 22 | Jun 15 | Change |
|---|---|---|---|
| World Cup schedule | 28.8 | 73.1 | **+153.6%** |
| World Cup stadiums | 15.5 | 48.4 | **+211.1%** |
| USMNT | 54.9 | 67.7 | +23.3% |
| World Cup tickets | 77.0 | 84.5 | +9.8% |
| Mexico soccer | 24.6 | 22.5 | -8.5% |
| Argentina soccer | 14.8 | 13.9 | -6.1% |

The logistics signals — *schedule* and *stadiums* — have exploded. This is consistent with tournament onset: fans are now past the "can I go?" phase and into "where do I go, when, and how do I get there?" The ticket signal is already high and still climbing. USMNT interest is elevated and growing. Mexico and Argentina fandom search interest is flat-to-slightly-down — possibly a reflection of how those teams are performing mid-tournament, or dilution from new diaspora keywords.

**World Cup tickets** raw values confirm this is real demand: New York hit 100 (index peak), Dallas 94, Kansas City 91 — all up meaningfully from the prior snapshot. Philadelphia remains the softest market at 60, though it is improving.

**City Rankings (with caveats)**
Boston (+102.5%), New York (+89.6%), and Philadelphia (+91.5%) show the largest city-level apparent swings, but much of this is driven by the new keywords' contribution. The one clean signal: Kansas City gained only +12.6% — the smallest of any city — despite being a host city. Its earlier snapshot was already missing one keyword, so even this understates the issue.

**New Signals Worth Watching (no prior baseline)**
- *how to watch World Cup* and *World Cup tickets near me* are new to the instrument — these are high-intent, late-funnel signals that should be tracked going forward.
- Morocco, Ecuador, and South Korea diaspora searches are now being captured. No prior data to compare, but their inclusion reflects smart targeting of underrepresented fan communities.

**Bottom line on the aggregate +66%:** Do not report this as demand growth. It is primarily an artifact of adding 7 higher-interest keywords to the instrument mid-stream.

## Recommendation

1. **Do not publish the +66% aggregate figure** in any stakeholder report without a heavy caveat — it will mislead. If pressed, cite only the 6 like-for-like keywords, which show a real and significant +9% to +211% range depending on keyword type.

2. **Act on the logistics surge.** World Cup schedule (+154%) and stadiums (+211%) signal fans are actively trip-planning right now. This is the window to push hospitality packages, transit bundles, and venue guides — particularly in Boston, New York, and Los Angeles where both the logistics surge and baseline demand are strongest.

3. **World Cup tickets is near saturation in top markets** (NYC at 100, Dallas at 94). Shift commercial messaging in those cities toward upsell (premium seating, packages) rather than acquisition. Philadelphia (60) still has headroom for acquisition pushes.

4. **Freeze the keyword instrument immediately** for the remainder of the tournament. Every mid-stream change makes trend analysis harder. If new keywords are added, they must be tracked in a parallel instrument, not spliced into the main series.

5. **Backfill or flag Kansas City's missing row** in 37a062e before using that city's trend in any model — the data gap makes its trajectory unreliable.

## Data quality concerns

- Instrument was significantly redesigned between snapshots: 3 keywords dropped (World Cup hospitality, World Cup host cities, World Cup packages) and 7 new keywords added (Brazil soccer, Ecuador soccer, Morocco soccer, South Korea soccer, World Cup resale tickets, World Cup tickets near me, how to watch World Cup). The two instruments do not measure the same thing.
- A new 'watch' bucket was introduced in 4af3158, which did not exist in 37a062e. This inflates apparent category-level demand.
- The fandom bucket grew from 3 keywords to 7 keywords — 31.2% apparent increase is almost entirely explained by adding 4 new fandom keywords, not by organic growth in measured terms.
- The logistics bucket shrank from 3 keywords to 2 (losing 'World Cup host cities') while showing a +222% delta — the removed keyword likely suppressed the earlier mean, making this delta unreliable.
- Kansas City had only 8 rows in 37a062e vs. 13 in 4af3158 — it was missing at least one keyword in the earlier snapshot, understating its earlier baseline and overstating its apparent growth (+12.6%, the lowest city — likely the floor).
- Overall mean comparison (26.92 → 44.62, +65.7%) should not be quoted to stakeholders as organic demand growth; it is primarily a function of keyword substitution.

## How it got here

9 tool calls before submitting:

- `list_snapshots` {}
- `describe_instrument` {"ref": "37a062e"}
- `describe_instrument` {"ref": "4af3158"}
- `compute_deltas` {"ref_a": "37a062e", "ref_b": "4af3158", "group_by": "city"}
- `compute_deltas` {"ref_a": "37a062e", "ref_b": "4af3158", "group_by": "bucket"}
- `compute_deltas` {"ref_a": "37a062e", "ref_b": "4af3158", "group_by": "keyword"}
- `get_values` {"ref": "37a062e", "keyword": "World Cup tickets"}
- `get_values` {"ref": "4af3158", "keyword": "World Cup tickets"}
- `get_values` {"ref": "37a062e", "city": "Kansas City"}
- `submit_readout`
