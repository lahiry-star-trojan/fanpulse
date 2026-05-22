# ⚽ Fan Pulse — Fan Intelligence for Major Events

**Live:** https://fanpulse-wc2026.streamlit.app

A fan-intelligence MVP built on public data. It answers a question sponsors, host cities, and ticketing platforms don't have a clean read on: **who is the American soccer fan, where are they, and what are they actually doing?** FIFA World Cup 2026 is the first event; the design is event-agnostic (LA28 is the next candidate).

> This is a portfolio project, not a commercial tool. The data is a **mid-May 2026 snapshot**, not live-refreshing (auto-refresh is on the roadmap). It runs entirely on free/public APIs.

---

## What's in it (5 panels)

**🗺️ Demand by host city.** Google Trends *interest by metro* for World Cup search terms, on one comparable scale, grouped by intent (fandom / buying / logistics). The headline number is fairly flat across big metros — so the panel leads with **what each market searches for**: a keyword-by-city heatmap and a national "rising searches" view.

**🎟️ Ticket price tiers.** Official FIFA pricing across 104 matches, by seat tier (Accessible → Ultra) and stage. Shows how fast each tier escalates Group → Final, plus an affordability heatmap (work-days at the US median wage to buy one seat) and a host-city income-vs-price gap.

**💬 Social sentiment.** ~2,100 YouTube comments scored with VADER. Team-level sentiment shown with **95% bootstrap confidence intervals** — so a thin sample reads as a wide band, not a false-precise number — plus per-team word clouds and top comments.

**🤖 AI briefing.** Pick a stakeholder (Nike, SeatGeek, FIFA, etc.) and Claude (Haiku) writes a short executive briefing from the panel data.

**📰 News buzz.** Live Google News headlines for WC2026, filtered by topic.

---

## How I pressure-tested it (the part that matters)

v1 looked clean but had real analytical gaps. A BI/analytics lead at an NHL club reviewed it and flagged the demand map. Digging into that feedback surfaced more than the original issue — and in one case showed his suggested fix was itself wrong for this data:

- **Per-capita normalization — proposed, then rejected with reason.** The suggestion was to divide search by city population. But the underlying data is Google Trends *interest*, which is already a share of each region's searches — i.e. already population-relative. Dividing again double-normalizes; tested on the real data it crowned tiny Kansas City #1, a pure population artifact. The right fix wasn't per-capita — it was fixing how the data was pulled.
- **State vs metro.** The original pull queried Trends at state level, so Los Angeles and San Francisco returned *identical* numbers (both "California"). Re-pulled at metro (DMA) level — now distinct and real.
- **Cross-city comparability.** Each keyword had been pulled in its own Trends query, and Trends scales every query to its own peak, so the city numbers were never on a shared axis. Switched to interest-by-region so cross-city comparison is actually valid.
- **The headline flipped.** "Houston #1" was an artifact of the broken pull. Corrected, overall interest is close across metros — and the real signal is *which fanbase* each market over-indexes on: **Mexico** in LA / Houston / Dallas (diaspora corridor), **Argentina** in Miami, **USMNT** in Atlanta / Seattle (MLS cities).
- **Sentiment honesty.** A 4-comment average (Mexico) was being compared next to a 221-comment one (Argentina) as if equally reliable. Added bootstrap confidence intervals so sample size is visible, not hidden.
- **Ticket data integrity.** The affordability view had been running on hardcoded numbers. Rebuilt it from the actual 104-match category prices, and reframed from "the $32K front-row final" to how fast each tier escalates: the Ultra tier reaches ~12× its group-stage price by the Final, the entry tier only ~4.5×.

The point of the project isn't the dashboard. It's being willing to find your own analysis wrong and fix it.

---

## Data sources

| Source | Powers | Cost |
|---|---|---|
| Google Trends (via SerpAPI) | Demand, keyword/diaspora, rising queries | Free tier |
| FIFA official pricing | Ticket tiers | Public |
| YouTube Data API v3 | Sentiment | Free tier |
| US Census ACS / StatCan / INEGI | City income (affordability) | Public |
| Google News (via SerpAPI) | News buzz | Free tier |
| Anthropic Claude (Haiku) | AI briefing | ~$0.01/call |

No proprietary data, no paid subscriptions.

---

## Tech stack

Streamlit · Plotly · Python / pandas / numpy · VADER (sentiment) · SerpAPI (Trends + News) · YouTube Data API v3 · Anthropic Claude API (Haiku) · Streamlit Cloud.

## Run it locally

```bash
git clone https://github.com/lahiry-star-trojan/fanpulse.git
cd fanpulse
pip install -r requirements.txt
# add your keys to a .env file:
#   SERPAPI_KEY=...  ANTHROPIC_API_KEY=...  YOUTUBE_API_KEY=...  CENSUS_API_KEY=...
streamlit run app.py
```

The dashboard reads pre-pulled snapshots in `data/`. To refresh, run the `pull_*.py` scripts in `panels/` (they read keys from `.env`).

---

## Honest limitations

- **Single source for demand.** Google Trends is *relative* search interest, not absolute volume or sales. A real demand read would triangulate ticket sales, travel, and social data — that's phase 2, not here.
- **Snapshot, not live.** Data was pulled mid-May 2026. No week-on-week trend yet; auto-refresh is on the roadmap.
- **Per-city qualitative is national.** Trends related-queries by metro aren't reliable, so the "what people search" view is national; per-city is keyword *interest* only.
- **Fanbase lens = 3 teams** (Mexico, Argentina, USMNT). More teams would enrich it.
- **Sentiment is YouTube-only**, and city-tagging is sparse (~85 of ~2,100 comments name a host city) — so city-level sentiment is held back until tagging improves rather than shown on thin data.

## Roadmap

- Automatic data refresh (replace the manual snapshot)
- Team filter across panels
- More national teams in the fanbase lens; expand to all 16 host cities (Canada / Mexico)
- Multi-source demand (sales / travel / social)
- LA28 as the next event — the platform is built to be event-agnostic

---

## Built by

**Shounak Lahiry** — USC Marshall MBA (Sports Analytics). 10 years in product and data (Mu Sigma → Ola).
[LinkedIn](https://linkedin.com/in/shounaklahiry)

*Portfolio project, May 2026.*
