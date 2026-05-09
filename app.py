import streamlit as st
import pandas as pd
from panels.panel1_demand import show_panel1
from panels.panel2_tickets import show_panel2
from panels.panel3_sentiment import show_panel3
from panels.panel4_briefing import show_panel4
from panels.panel5_news import show_panel5

st.set_page_config(
    page_title='Fan Pulse | FIFA WC 2026',
    page_icon='⚽',
    layout='wide'
)

st.markdown("""
<style>
.stMetric{background:#1E2A3A;border-radius:8px;padding:12px}
.stTabs [data-baseweb='tab']{font-size:15px;font-weight:600}
h1,h2,h3{color:#FFFFFF}
.stButton>button{background:#E94560;color:white;border-radius:6px;border:none}
.stButton>button:hover{background:#C0392B}
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────
col_logo, col_title, col_img = st.columns([1,3,1])

with col_logo:
    st.image('assets/fifa_logo.webp', width=120)

with col_title:
    st.markdown("# ⚽ Fan Pulse: FIFA World Cup 2026")
    st.caption('US fan demand · ticket intelligence · social sentiment · AI briefings across 11 host cities')

with col_img:
    st.image('assets/fifa_teams.webp', width=150)

# ── BANNER ───────────────────────────────────────────────────
st.image('assets/fifa_players1.jpg', use_column_width=True)

st.divider()

# ── KPI CARDS ────────────────────────────────────────────────
try:
    tr = pd.read_csv('data/processed/trends_processed.csv')
    tk = pd.read_csv('data/processed/tickets_processed.csv')
    yt = pd.read_csv('data/processed/youtube_tagged.csv')

    top_city  = tr.loc[tr['demand_score_norm'].idxmax(), 'city']
    top_score = tr['demand_score_norm'].max()
    top_price = tk['median_price'].max()
    hot_n     = len(tk[tk['tier']=='Hot'])
    pos_pct   = round(len(yt[yt['sentiment']=='Positive']) / len(yt) * 100)

    col1,col2,col3,col4 = st.columns(4)
    col1.metric('🏙️ Top Demand City',    top_city,            f"{top_score:.0f}/100")
    col2.metric('💸 Priciest Ticket',    f'${top_price:,.0f}', 'secondary market')
    col3.metric('😊 Positive Sentiment', f'{pos_pct}%',        '2,113 comments')
    col4.metric('🔥 Hot Matches 2x+',    hot_n,               'above avg price')
except Exception as e:
    st.warning(f'KPI error: {e}')

st.divider()

# ── TABS ─────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    '🗺️ Demand Map',
    '🎟️ Ticket Prices',
    '💬 Social Sentiment',
    '🤖 AI Briefing',
    '📰 News Buzz'
])

with tab1:
    show_panel1()

with tab2:
    show_panel2()

with tab3:
    show_panel3()

with tab4:
    show_panel4()

with tab5:
    show_panel5()