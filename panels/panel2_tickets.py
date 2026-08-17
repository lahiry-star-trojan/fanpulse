import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

STAGE_ORDER = {'Group Stage':1,'Round of 32':2,'Round of 16':3,'Quarterfinals':4,
               'Semifinals':5,'Third Place Playoff':6,'Final':7}
STAGE_SHORT = {'Group Stage':'Group','Round of 32':'R32','Round of 16':'R16',
               'Quarterfinals':'QF','Semifinals':'SF','Third Place Playoff':'3rd',
               'Final':'Final'}
# the 4 seat categories ARE the price tiers Stefan named
TIER_MAP   = {'Category 3':'Accessible','Category 2':'Stretch',
              'Category 1':'Premium','Front Category':'Ultra'}
TIER_ORDER = ['Accessible','Stretch','Premium','Ultra']
TIER_COLOR = {'Accessible':'#27AE60','Stretch':'#F39C12',
              'Premium':'#E74C3C','Ultra':'#8E44AD'}
US_INCOME, WORK_DAYS = 74580, 260


def load_city_incomes():
    try:
        d = pd.read_csv('data/raw/city_incomes.csv')
        return dict(zip(d['city'], d['median_income']))
    except Exception:
        return {}


def show_panel2():
    df  = pd.read_csv('data/processed/tickets_processed.csv')
    cat = pd.read_csv('data/processed/tickets_by_category.csv')
    CITY_INCOME = load_city_incomes()
    cat['tier'] = cat['category'].map(TIER_MAP)

    st.subheader('🎟️ Ticket Price Tiers — What It Costs to Get In')
    st.caption('Official FIFA pricing across 104 matches, by seat tier '
               '(Accessible → Ultra) and stage. The story isn\'t the $32K '
               'front-row Final — it\'s how much faster the top tier escalates '
               'than the entry tier.')

    # tier × stage median matrix on the main Group→Final path (drop 3rd-place side match)
    main = [s for s in STAGE_ORDER if s != 'Third Place Playoff' and s in cat['stage'].unique()]
    main = sorted(main, key=lambda s: STAGE_ORDER[s])
    piv = (cat.pivot_table(index='tier', columns='stage', values='median_price',
                           aggfunc='median')
              .reindex(TIER_ORDER)[main])

    acc_g  = piv.loc['Accessible','Group Stage']
    acc_pk = piv.loc['Accessible'].max()
    ult_g  = piv.loc['Ultra','Group Stage']
    ult_f  = piv.loc['Ultra','Final']
    cheap  = cat['lowest_price'].min()
    acc_esc, ult_esc = acc_pk/acc_g, ult_f/ult_g

    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Cheapest Entry',         f'${cheap:,.0f}',   'Accessible · Group')
    c2.metric('Entry-tier escalation',  f'{acc_esc:.1f}x',  'Group → top knockout')
    c3.metric('Top-tier escalation',    f'{ult_esc:.0f}x',  'Group → Final')
    c4.metric('Tiers tracked',          '4',                'Accessible → Ultra')

    st.info(
        f"**Bottom line:** the entry **Accessible** tier rises ~{acc_esc:.1f}x from "
        f"group stage to its deepest knockout, but the **Ultra** tier explodes "
        f"~{ult_esc:.0f}x to ${ult_f:,.0f} at the Final — the top end prices fans "
        f"out ~{ult_esc/acc_esc:.0f}x faster. And there's **no Accessible seat at "
        f"the Final at all**: the cheapest Final tier is Stretch "
        f"(${piv.loc['Stretch','Final']:,.0f}).")
    st.divider()

    # ── CENTERPIECE: how fast each tier escalates (indexed, linear) ─
    st.subheader('How Fast Each Tier Escalates')
    idx = piv.div(piv['Group Stage'], axis=0)   # multiple of each tier's own group price
    fig = go.Figure()
    fig.add_hline(y=1, line_dash='dot', line_color='rgba(255,255,255,0.25)',
                  annotation_text='group-stage price', annotation_position='top left',
                  annotation_font_color='rgba(255,255,255,0.5)')
    for tier in TIER_ORDER:
        mult    = [idx.loc[tier, s] for s in main]
        dollars = [piv.loc[tier, s] for s in main]
        fig.add_trace(go.Scatter(
            x=[STAGE_SHORT[s] for s in main], y=mult, name=tier,
            mode='lines+markers', connectgaps=False, customdata=dollars,
            line=dict(color=TIER_COLOR[tier], width=3), marker=dict(size=9),
            hovertemplate=f'{tier} · %{{x}}: %{{y:.1f}}× group ($%{{customdata:,.0f}})<extra></extra>'))
    fig.update_layout(height=440, paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                      yaxis=dict(title='× its own group-stage price', ticksuffix='×'),
                      xaxis=dict(title='Tournament Stage'),
                      legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig, width='stretch')
    st.caption(f'Each tier indexed to its own group-stage price (1×). Ultra climbs to '
               f'~{idx.loc["Ultra","Final"]:.0f}× by the Final while the lower tiers '
               f'stay near 3–4× — the top end escalates far faster, the same money '
               f'doesn\'t buy "up" a round. (Accessible has no Final seat; '
               f'third-place playoff omitted.)')
    st.divider()

    # ── AFFORDABILITY (data-driven; replaces the old hardcoded bar) ─
    st.subheader('Who Can Afford Each Tier?')
    st.caption(f'Work-days at the US median wage (${US_INCOME:,}/yr ÷ {WORK_DAYS} '
               'work-days) to buy one ticket — computed from the real prices above.')
    days = piv / (US_INCOME / WORK_DAYS)
    txt = [[('' if pd.isna(v) else f'{v:.0f}d') for v in row] for row in days.values]
    heat = go.Figure(go.Heatmap(
        z=days.values, x=[STAGE_SHORT[s] for s in main], y=TIER_ORDER,
        text=txt, texttemplate='%{text}', colorscale='OrRd',
        colorbar=dict(title='work-days'),
        hovertemplate='%{y} · %{x}: %{text}<extra></extra>'))
    heat.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                       yaxis=dict(autorange='reversed'),
                       paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(heat, width='stretch')
    acc_days, ult_days = days.loc['Accessible','Group Stage'], days.loc['Ultra','Final']
    st.caption(f'Darker = less affordable. Accessible group seat ≈ {acc_days:.0f} '
               f'work-days; Ultra Final seat ≈ {ult_days:.0f} — about '
               f'{ult_days/WORK_DAYS*12:.0f} months of full-time pay.')
    st.divider()

    # ── CITY AFFORDABILITY GAP (kept — already data-driven) ───────
    st.subheader('Host City Affordability Gap')
    st.caption('Avg ticket price vs local median income. '
               'Source: US Census ACS 2022, StatCan 2021, INEGI 2020')
    city = df.groupby('city')['median_price'].mean().reset_index()
    city.columns = ['city','avg_ticket']
    city['median_income'] = city['city'].map(CITY_INCOME)
    city = city.dropna()
    if not city.empty:
        city['burden_pct'] = (city['avg_ticket']/city['median_income']*100).round(1)
        city['burden'] = city['burden_pct'].apply(
            lambda x: 'High' if x>4 else ('Medium' if x>2.5 else 'Lower'))
        city['matches'] = city['city'].map(df.groupby('city')['title'].nunique())
        fig3 = px.scatter(city, x='median_income', y='avg_ticket', size='matches',
                          color='burden', text='city',
                          color_discrete_map={'High':'#E74C3C','Medium':'#F39C12','Lower':'#27AE60'},
                          labels={'median_income':'City Median Income ($)',
                                  'avg_ticket':'Avg Ticket ($)','burden':'Burden'},
                          title='Income vs Ticket Price (bubble = matches hosted)')
        fig3.update_traces(textposition='top center', textfont_size=10,
                           marker=dict(opacity=0.85))
        fig3.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                           xaxis=dict(tickprefix='$', tickformat=','),
                           yaxis=dict(tickprefix='$', tickformat=','))
        st.plotly_chart(fig3, width='stretch')
        st.caption('Mexican host cities carry the highest burden — global prices '
                   'against local wages.')
    st.divider()

    # ── BROWSE (filterable table — lookup is a table's job) ───────
    st.subheader('Browse Matches')
    col1, col2 = st.columns(2)
    with col1:
        cities = ['All Cities'] + sorted(df['city'].dropna().unique().tolist())
        sel_city = st.selectbox('City:', cities)
    with col2:
        stg = ['All Stages'] + sorted(df['stage'].dropna().unique().tolist(),
                                      key=lambda x: STAGE_ORDER.get(x,0))
        sel_stage = st.selectbox('Stage:', stg)
    pdf = df.copy()
    if sel_city  != 'All Cities':  pdf = pdf[pdf['city']==sel_city]
    if sel_stage != 'All Stages':  pdf = pdf[pdf['stage']==sel_stage]
    pdf = pdf.sort_values('median_price', ascending=False)
    tbl = pdf[['city','stage','title','lowest_price','median_price','listings']].copy()
    tbl.columns = ['City','Stage','Match','Lowest','Median','Listings']
    st.dataframe(
        tbl, width='stretch', hide_index=True,
        column_config={
            'Lowest': st.column_config.NumberColumn(format='$%d'),
            'Median': st.column_config.NumberColumn(format='$%d'),
        })
    st.caption('Match codes (e.g. "W101 vs W102") are FIFA bracket placeholders — '
               'teams are set after the December draw. Filter by city/stage; '
               'sorted high → low.')

    st.divider()
    st.subheader('Seat Tier Breakdown by Match')
    matches = sorted(cat['title'].unique().tolist())
    sel = st.selectbox('Match:', matches)
    mdf = cat[cat['title']==sel].copy()
    mdf['tier'] = pd.Categorical(mdf['tier'], categories=TIER_ORDER, ordered=True)
    mdf = mdf.sort_values('tier')
    fig5 = px.bar(mdf, x='tier', y='median_price', color='tier', text='median_price',
                  color_discrete_map=TIER_COLOR,
                  labels={'tier':'Seat Tier','median_price':'Price ($)'})
    fig5.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', cliponaxis=False)
    fig5.update_layout(height=360, showlegend=False, margin=dict(t=40),
                       yaxis=dict(range=[0, mdf['median_price'].max()*1.18]),
                       paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig5, width='stretch')
