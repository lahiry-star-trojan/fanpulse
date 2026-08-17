import streamlit as st
import pandas as pd
import anthropic, os
from dotenv import load_dotenv
load_dotenv()

EMPLOYER_CONTEXTS = {
    'Nike — Sports Marketing': {
        'icon': '👟',
        'focus': 'brand activation, sponsorship ROI, fan engagement for marketing campaigns',
        'question': 'Where should Nike concentrate World Cup activation spend and which fan segments to target?',
    },
    'SeatGeek / StubHub — Ticketing': {
        'icon': '🎟️',
        'focus': 'secondary market pricing, inventory demand, ticket price movements',
        'question': 'Which matches are underpriced or overpriced? Where is demand outpacing supply?',
    },
    'FIFA / Host City Organizers': {
        'icon': '🏟️',
        'focus': 'fan attendance, city activation, marketing gaps, demand distribution',
        'question': 'Which host cities need more marketing investment and where is organic demand strongest?',
    },
    'Stats Perform / Opta — Data Vendors': {
        'icon': '📊',
        'focus': 'data product opportunities, fan behavior patterns, analytics methodology',
        'question': 'What fan behavior patterns exist and how could proprietary data improve these insights?',
    },
    'MLS / Sports Teams': {
        'icon': '⚽',
        'focus': 'fan development, market sizing, community engagement, local demand',
        'question': 'Which cities show untapped soccer fan potential and what drives local engagement?',
    },
}

@st.cache_data(ttl=3600)
def gen_briefing(ts, tks, ss, search_s, news_s, employer, focus, question):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    system = (
        f'You are a senior sports analytics advisor presenting to {employer}. '
        f'Your focus is {focus}. '
        f'Produce a concise, data-driven executive briefing that directly answers: {question} '
        f'Use specific numbers, city names, and team names from the data provided. '
        f'Structure:\n'
        f'1. KEY FINDING — one sharp insight in bold\n'
        f'2. MARKET INTELLIGENCE — 3 specific data points\n'
        f'3. DIGITAL SIGNALS — search trends + sentiment patterns\n'
        f'4. EMERGING SIGNAL — digital collectibles/NFT context for FIFA 2026\n'
        f'5. RECOMMENDATIONS — exactly 3 specific actions for {employer}\n'
        f'Max 280 words. Be direct. No filler.'
    )

    user = (
        f'Generate a tailored briefing for {employer}:\n\n'
        f'DEMAND DATA (Google Trends — 11 US cities):\n{ts}\n\n'
        f'TICKET PRICING (FIFA Official + Secondary Market):\n{tks}\n\n'
        f'SENTIMENT DATA (YouTube — 2,113 comments):\n{ss}\n\n'
        f'SEARCH KEYWORD DATA:\n{search_s}\n\n'
        f'LATEST NEWS CONTEXT:\n{news_s}\n\n'
        f'Answer this for {employer}: {question}\n\n'
        f'Include a brief note on FIFA digital collectibles/NFTs as an emerging fan engagement signal to watch.'
    )

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=800,
        system=system,
        messages=[{'role': 'user', 'content': user}]
    )
    return msg.content[0].text

@st.cache_data(ttl=3600)
def load_search_summary():
    try:
        trends = pd.read_csv('data/raw/trends_serp.csv')
        trends = trends[trends['date'].notna()]
        kw_cols = ['World Cup tickets','FIFA 2026','USMNT',
                   'Argentina soccer','Mexico soccer']
        avgs = trends[kw_cols].mean().sort_values(ascending=False)
        top_kw = avgs.index[0]
        top_city = trends.groupby('city')[kw_cols].mean().mean(axis=1).idxmax()
        return (
            f"Top searched keyword: '{top_kw}' (avg {avgs[top_kw]:.1f}/100). "
            f"City with highest search volume: {top_city}. "
            f"Keyword ranking: {', '.join([f'{k}={v:.1f}' for k,v in avgs.items()])}."
        )
    except:
        return "Search data unavailable"

@st.cache_data(ttl=3600)
def load_news_summary():
    try:
        import requests
        params = {
            'engine': 'google_news',
            'q': 'FIFA World Cup 2026',
            'api_key': os.getenv('SERPAPI_KEY'),
            'gl': 'us', 'hl': 'en', 'num': 5
        }
        resp = requests.get('https://serpapi.com/search', params=params)
        results = resp.json().get('news_results', [])
        headlines = [r.get('title','') for r in results[:5]
                     if r.get('title') not in ['Top news','Sports']]
        return 'Recent headlines: ' + ' | '.join(headlines[:4])
    except:
        return "News data unavailable"

def show_panel4():
    st.subheader('🤖 AI Briefing — Tailored by Stakeholder')
    st.caption('Select your audience. Get a briefing written for their specific business decisions.')

    # Employer selector
    st.markdown('### Who is this briefing for?')
    cols = st.columns(len(EMPLOYER_CONTEXTS))
    selected = st.session_state.get('selected_employer','Nike — Sports Marketing')

    for i, (employer, ctx) in enumerate(EMPLOYER_CONTEXTS.items()):
        with cols[i]:
            if st.button(
                f"{ctx['icon']} {employer.split('—')[0].strip()}",
                width='stretch',
                type='primary' if selected == employer else 'secondary'
            ):
                st.session_state['selected_employer'] = employer
                selected = employer

    ctx = EMPLOYER_CONTEXTS[selected]
    st.markdown(f"**Selected:** {ctx['icon']} {selected}")
    st.markdown(f"**Briefing answers:** _{ctx['question']}_")

    st.divider()

    # Load all data
    try:
        tr = pd.read_csv('data/processed/trends_processed.csv')
        tk = pd.read_csv('data/processed/tickets_processed.csv')

        top_city  = tr.loc[tr['demand_score_norm'].idxmax()]
        low_city  = tr.loc[tr['demand_score_norm'].idxmin()]
        top_match = tk.loc[tk['median_price'].idxmax()]
        hot_n     = len(tk[tk['tier']=='Hot'])

        ts = (
            f"Top demand city: {top_city['city']} ({top_city['demand_score_norm']:.0f}/100). "
            f"Lowest: {low_city['city']} ({low_city['demand_score_norm']:.0f}/100). "
            f"Houston leads overall. Miami fastest rising (+12.5% WoW). "
            f"11 US host cities tracked via Google Trends."
        )
        tks = (
            f"Most expensive match: {top_match['title']} avg ${top_match['median_price']:,.0f}. "
            f"Final ticket median $9,000, front row $32,179. "
            f"Hot matches (2x avg): {hot_n}. "
            f"Overall avg: ${tk['median_price'].mean():,.0f}. "
            f"Cheapest entry: $605 (Round of 32)."
        )
        ss = (
            "YouTube analysis — 2,113 comments: 57% positive, 29% neutral, 14% negative. "
            "Mexico highest search interest. Argentina strongest positive sentiment. "
            "USMNT high volume mixed sentiment. "
            "Miami + Houston strongest fan community activity."
        )

    except Exception as e:
        st.error(f'Data error: {e}')
        return

    search_s = load_search_summary()
    news_s   = load_news_summary()

    # Data preview
    st.markdown('### 📊 Data Feeding This Briefing')
    c1,c2,c3,c4 = st.columns(4)
    c1.info(f"**🗺️ Demand**\n\n{top_city['city']} leads\n{top_city['demand_score_norm']:.0f}/100")
    c2.info(f"**🎟️ Tickets**\n\nFinal: $9,000\nFront row: $32,179")
    c3.info(f"**💬 Sentiment**\n\n57% positive\n2,113 comments")
    c4.info(f"**🔍 Search**\n\nFIFA 2026 = top keyword\n11 cities tracked")

    st.divider()

    if st.button(
        f"Generate {ctx['icon']} Briefing for {selected.split('—')[0].strip()}",
        type='primary',
        width='stretch'
    ):
        with st.spinner(f"Generating briefing for {selected.split('—')[0].strip()}..."):
            txt = gen_briefing(ts, tks, ss, search_s, news_s,
                               selected, ctx['focus'], ctx['question'])

        st.markdown('---')
        col1, col2 = st.columns([3,1])

        with col1:
            st.markdown(f"### {ctx['icon']} Weekly Briefing — {selected}")
            st.markdown(txt)

        with col2:
            st.markdown('**Data Sources**')
            st.caption('📈 Google Trends via SerpAPI')
            st.caption('🎟️ FIFA Official Pricing')
            st.caption('💬 YouTube (2,113 comments)')
            st.caption('📰 Google News (live)')
            st.caption('🤖 Claude AI (Haiku)')
            st.divider()
            st.caption(f'Audience: {selected}')
            st.caption('Click button to regenerate')
        st.markdown('---')
    else:
        st.info(f'Click the button above to generate a briefing for {selected.split("—")[0].strip()}.')