# ⚽ Fan Pulse — FIFA World Cup 2026 Fan Intelligence Dashboard

**Live Dashboard:** https://fanpulse-wc2026.streamlit.app

---

## What Is This?

Fan Pulse is a fan intelligence product built to answer a question that sponsors, host cities, and ticketing platforms don't have a clean answer to:

*Who is the American soccer fan, where are they, and how do you reach them?*

It tracks US fan demand, ticket pricing, social sentiment, and news buzz across 11 FIFA World Cup 2026 host cities — updated daily, with an AI briefing layer that translates data into decisions.

---

## Why It Was Built

The FIFA World Cup 2026 is the largest sporting event ever hosted in the US. 11 host cities. 48 nations. An estimated $5B+ in economic impact.

Yet most fan engagement decisions — where to activate a sponsorship, which markets to prioritize, which matchups to push — are made on instinct, not data.

Fan Pulse is a first attempt at changing that with public data. The goal was to build something an analyst at Nike, SeatGeek, or a host city organizing committee could open on a Monday morning and immediately act on.

---

## 5 Panels

**🗺️ Demand Map**
Google Trends search volume for FIFA 2026 keywords across 11 host cities. Scored 0-100. Shows which cities are organically engaged and which need marketing activation.

**🎟️ Ticket Price Intelligence**
Official FIFA pricing + secondary market data across match types — group stage through final. Category-level breakdown. Price premium analysis. $605 cheapest entry. $32,179 front row final.

**💬 Social Sentiment**
2,100+ YouTube comments analyzed with VADER sentiment model. Team-level sentiment scores, fan community word clouds, most positive and negative comments, and a Google Trends keyword heatmap showing what fans actually search for by city.

**🤖 AI Briefing — Tailored by Stakeholder**
The differentiator. Select your audience (Nike, SeatGeek, FIFA, Stats Perform, MLS) and Claude AI generates a 250-word executive briefing answering that stakeholder's specific business question using live data from all panels.

**📰 News Buzz**
Live Google News headlines for FIFA 2026 filtered by topic. AI-generated summaries for articles without previews.

---

## Data Sources

| Source | What It Powers | Cost |
|--------|---------------|------|
| Google Trends via SerpAPI | Demand Map | Free tier |
| FIFA Official Website | Ticket pricing | Public |
| YouTube Data API v3 | Sentiment analysis | Free tier |
| Google News via SerpAPI | News Buzz panel | Free tier |
| Claude API (Haiku) | AI Briefing | ~$0.01/call |

No proprietary data. No paid subscriptions. Built entirely on public APIs.

---

## Tech Stack

- **Frontend:** Streamlit
- **Visualizations:** Plotly
- **Data Processing:** Python, pandas
- **Sentiment Analysis:** VADER
- **Search Trends:** SerpAPI (Google Trends + News)
- **Social Data:** YouTube Data API v3
- **AI Layer:** Anthropic Claude API (Haiku)
- **Hosting:** Streamlit Cloud

---

## Current Limitations (v1)

- Sentiment data is YouTube-only — Reddit API access was restricted during build
- Ticket prices are FIFA official + estimated secondary market (SeatGeek listings not yet active for WC2026)
- Google Trends data limited to 11 cities due to API rate limits
- No historical trend comparison yet (first data pull was May 2026)

---

## What v2 Looks Like

- Live secondary market ticket prices (SeatGeek/StubHub API when WC2026 listings go live)
- Reddit sentiment layer once API access is resolved
- Real-time match-day demand spikes
- Mobile-optimized layout for decision makers on the go
- Expanded to all 16 host cities including Canadian and Mexican venues
- Fan demographic profiling using Census + MLS attendance data

---

## Who This Is For

- **Sports sponsors** (Nike, Adidas, Budweiser) — activation market prioritization
- **Ticketing platforms** (SeatGeek, StubHub, Viagogo) — demand vs pricing intelligence
- **Host city organizers** — identifying underserved markets
- **Data vendors** (Stats Perform, Opta) — fan behavior product layer
- **MLS / soccer organizations** — market sizing and fan development

---

## Built By

Shounak Lahiry — USC Marshall MBA (Sports Analytics concentration)
10 years in product and data (Mu Sigma → Ola)
[LinkedIn](https://linkedin.com/in/shounaklahiry)

*Built in 5 days as a portfolio project. May 2026.*