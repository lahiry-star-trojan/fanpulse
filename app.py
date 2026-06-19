import streamlit as st
import pandas as pd
from panels.panel1_demand import show_panel1
from panels.panel2_tickets import show_panel2
from panels.panel3_sentiment import show_panel3
from panels.panel4_briefing import show_panel4
from panels.panel5_news import show_panel5
from panels.panel6_pricing import show_panel6

st.set_page_config(
    page_title='Fan Pulse | FIFA WC 2026',
    page_icon='⚽',
    layout='wide'
)

st.markdown("""
<style>
.stMetric{background:#1E2A3A;border-radius:8px;padding:12px}
/* force metric text light so it never goes dark-on-dark on any device/theme */
.stMetric label, .stMetric [data-testid='stMetricLabel'],
.stMetric [data-testid='stMetricLabel'] *{color:#AEB8C4 !important}
.stMetric [data-testid='stMetricValue']{color:#FFFFFF !important}
.stMetric [data-testid='stMetricDelta']{color:#1ABC9C !important}
.stTabs [data-baseweb='tab']{font-size:15px;font-weight:600}
h1,h2,h3{color:#FFFFFF}
/* body text + captions readable on dark bg */
.stMarkdown, .stCaption, p, span, li{color:#E8EaED}
[data-testid='stCaptionContainer']{color:#AEB8C4 !important}
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
t_demand, t_tickets, t_pricing, t_sentiment, t_brief, t_news = st.tabs([
    '🗺️ Demand Map',
    '🎟️ Ticket Prices',
    '💸 Price vs Demand',
    '💬 Social Sentiment',
    '🤖 AI Briefing',
    '📰 News Buzz'
])

with t_demand:
    show_panel1()

with t_tickets:
    show_panel2()

with t_pricing:
    show_panel6()

with t_sentiment:
    show_panel3()

with t_brief:
    show_panel4()

with t_news:
    show_panel5()