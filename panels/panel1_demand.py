import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COORDS = {
    'Los Angeles':(34.0522,-118.2437),'New York':(40.7128,-74.0060),
    'Miami':(25.7617,-80.1918),'Dallas':(32.7767,-96.7970),
    'Houston':(29.7604,-95.3698),'San Francisco':(37.7749,-122.4194),
    'Seattle':(47.6062,-122.3321),'Atlanta':(33.7490,-84.3880),
    'Boston':(42.3601,-71.0589),'Philadelphia':(39.9526,-75.1652),
    'Kansas City':(39.0997,-94.5786),
}
TEXT_POS = {
    'Los Angeles':'middle left','San Francisco':'top left','Seattle':'top center',
    'Dallas':'bottom left','Houston':'bottom right','Kansas City':'top center',
    'Atlanta':'top right','Miami':'bottom right','New York':'top right',
    'Boston':'top right','Philadelphia':'bottom left',
}
# keywords shown in the heatmap (sparse ones dropped), grouped by intent
KW_SHOW  = ['Mexico soccer','Argentina soccer','USMNT',
            'World Cup tickets','World Cup host cities','World Cup stadiums',
            'World Cup schedule']
KW_SHORT = {'Mexico soccer':'Mexico','Argentina soccer':'Argentina','USMNT':'USMNT',
            'World Cup tickets':'Tickets','World Cup host cities':'Host cities',
            'World Cup stadiums':'Stadiums','World Cup schedule':'Schedule'}
KW_GROUP = {'Mexico':'fandom','Argentina':'fandom','USMNT':'fandom',
            'Tickets':'commercial','Host cities':'logistics',
            'Stadiums':'logistics','Schedule':'logistics'}

# ── qualitative cleaning ──────────────────────────────────────────
JUNK = ['frontend','node.js','node js',' iot ','internet of things','deep learning',
        'lidl','framework','tutorial','backend','machine learning']
OTHER_SPORT = ['fiba','fei ','baseball',' wbc','nhl','nba ',"women's",'womens','women ',
               'u17','u-17','u 17','basketball','equestrian','rugby','cricket','t20',
               'hockey','volleyball']
COLLECT = ['panini','sticker','album','collection']
STAGE_LABEL = {'commercial':'Buying intent','fandom':'Fandom & players',
               'logistics':'Logistics & schedule','collectibles':'Collectibles'}
STAGE_COLOR = {'Buying intent':'#E94560','Fandom & players':'#F39C12',
               'Logistics & schedule':'#3498DB','Collectibles':'#9B59B6'}


def is_real_wc(q):
    s = ' ' + str(q).lower() + ' '
    return not (any(j in s for j in JUNK) or any(o in s for o in OTHER_SPORT))


def classify_q(q):
    s = str(q).lower()
    if any(c in s for c in COLLECT): return 'collectibles'
    if any(k in s for k in ['ticket','price','buy','resale','seatgeek','vivid',
                            'gametime','sale','hospitality','package']): return 'commercial'
    if any(k in s for k in ['ronaldo','messi','usmnt','roster','jersey','musah',
                            'pochettino','goalkeeper','argentina fc','vs ',
                            'national football','squad','player']): return 'fandom'
    if any(k in s for k in ['schedule','fixture','stadium','venue','qualifier',
                            'draw','group','host','dates']): return 'logistics'
    return 'awareness'


def show_panel1():
    df = pd.read_csv('data/processed/trends_geo.csv')
    df['demand_score_norm'] = df['demand_score_norm'].round(1)
    df['lat'] = df['city'].map(lambda x: COORDS.get(x,(0,0))[0])
    df['lon'] = df['city'].map(lambda x: COORDS.get(x,(0,0))[1])
    order = df.sort_values('demand_score_norm', ascending=False)['city'].tolist()

    # full keyword x city matrix
    kw = None
    try:
        raw = pd.read_csv('data/raw/trends_geo_raw.csv')
        kw = (raw.pivot_table(index='city', columns='keyword', values='value',
                              fill_value=0)
                 .reindex([c for c in order])
                 [[k for k in KW_SHOW if k in raw['keyword'].unique()]]
                 .rename(columns=KW_SHORT))
    except Exception:
        kw = None

    st.subheader('🗺️ US Fan Demand by Host City')
    st.caption(
        'An early read on **US search interest** — one demand proxy (no '
        'ticket-sales / travel / social data). The overall level is fairly flat '
        'across metros; the real signal is **what each market searches for**, '
        'shown in the keyword map below.')

    # KPIs: overall + fanbase strongholds
    top = df.loc[df['demand_score_norm'].idxmax()]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('🏆 Strongest Interest', top['city'], f"{top['demand_score_norm']:.0f}/100")
    if kw is not None and not kw.empty:
        for col,(label,k) in zip([c2,c3,c4],
                [('🇲🇽 Mexico stronghold','Mexico'),
                 ('🇦🇷 Argentina stronghold','Argentina'),
                 ('🇺🇸 USMNT stronghold','USMNT')]):
            if k in kw.columns:
                col.metric(label, kw[k].idxmax(), 'over-indexes here')

    # bottom line (driver story, computed)
    if kw is not None and not kw.empty:
        def tp(c, n=1): return kw[c].sort_values(ascending=False).head(n).index.tolist()
        mex = ', '.join(tp('Mexico',3)) if 'Mexico' in kw else ''
        arg = tp('Argentina')[0] if 'Argentina' in kw else ''
        usm = ', '.join(tp('USMNT',2)) if 'USMNT' in kw else ''
        tix = tp('Tickets')[0] if 'Tickets' in kw else ''
        st.info(
            f"**Bottom line:** {top['city']} leads overall, but markets differ by "
            f"*driver*. **Mexico** fandom powers **{mex}** (diaspora corridor); "
            f"**Argentina** peaks in **{arg}**; **USMNT** in **{usm}** (MLS cities). "
            f"**{tix}** tops ticket + host-city search — an *attendance* market "
            f"figuring out how to go. Activate each for what's actually driving it.")
    st.divider()

    # ── MAP (overall geography) ───────────────────────────────────
    fig = go.Figure()
    for _, r in df.iterrows():
        size  = max(r['demand_score_norm']*0.5, 10)
        color = ('#E94560' if r['demand_score_norm']>=90 else
                 '#F39C12' if r['demand_score_norm']>=50 else '#3498DB')
        fig.add_trace(go.Scattergeo(
            lat=[r['lat']], lon=[r['lon']], mode='markers+text',
            marker=dict(size=size, color=color, opacity=0.8,
                        line=dict(color='white', width=1)),
            text=f"{r['city']}  {r['demand_score_norm']:.0f}",
            textposition=TEXT_POS.get(r['city'],'top center'),
            textfont=dict(size=10, color='white'),
            hovertemplate=f"<b>{r['city']}</b><br>Overall interest {r['demand_score_norm']:.0f}/100<extra></extra>",
            name=r['city']))
    fig.update_layout(
        geo=dict(scope='usa', showland=True, landcolor='#1E2A3A', showocean=True,
                 oceancolor='#0F1923', showlakes=True, lakecolor='#0F1923',
                 showcoastlines=True, coastlinecolor='#444', showsubunits=True,
                 subunitcolor='#333', bgcolor='#0F1923', projection_type='albers usa'),
        paper_bgcolor='#0F1923', showlegend=False, height=460,
        margin=dict(l=0,r=0,t=30,b=0),
        title=dict(text='🔴 Strong  🟡 Medium  🔵 Lower (overall interest)',
                   x=0.5, font=dict(color='white', size=11)))
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # ── KEYWORD-BY-CITY HEATMAP (the centerpiece) ─────────────────
    st.subheader("🎯 What's Driving Each Host City")
    if kw is not None and not kw.empty:
        teams = list(kw.columns)
        z_raw = kw.astype(float)
        z_col = z_raw.copy()
        for t in teams:                       # scale each keyword to its own hottest metro
            lo, hi = z_col[t].min(), z_col[t].max()
            z_col[t] = (z_col[t]-lo)/(hi-lo) if hi > lo else 0.0
        heat = go.Figure(go.Heatmap(
            z=z_col.values, x=teams, y=list(z_raw.index),
            text=z_raw.values, texttemplate='%{text:.0f}',
            colorscale='Blues', showscale=False,
            hovertemplate='%{y} — %{x}: %{text:.0f}/100<extra></extra>'))
        heat.update_layout(height=470, margin=dict(l=0,r=0,t=10,b=40),
                           yaxis=dict(autorange='reversed'),
                           xaxis=dict(side='top'),
                           paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(heat, use_container_width=True)
        st.caption(
            'Rows = cities (top = strongest overall). Columns = keywords, grouped '
            '**Fandom** (Mexico/Argentina/USMNT) · **Buying** (Tickets) · '
            '**Logistics** (Host cities/Stadiums/Schedule). Each column is shaded '
            'against its own hottest metro, so a dark cell = that city '
            '**over-indexes** on that search. Numbers are 0–100 interest. '
            'Read across a city to see what drives it.')
        with st.expander('📊 Show raw keyword scores (all cities × keywords)'):
            st.dataframe(kw.reset_index().round(0), use_container_width=True,
                         hide_index=True)
    else:
        st.info('Keyword breakdown needs data/raw/trends_geo_raw.csv — re-run the pull.')
    st.divider()

    # ── QUALITATIVE: rising queries as a treemap ──────────────────
    st.subheader('🔍 What People Are Actually Searching (rising queries, national)')
    try:
        rq = pd.read_csv('data/raw/related_queries_raw.csv')
        rising = rq[rq['kind'] == 'rising'].copy()
        rising = rising[rising['query'].apply(is_real_wc)]
        rising['stage'] = rising['query'].apply(classify_q)
        rising = rising[rising['stage'] != 'awareness'].drop_duplicates('query')

        n = rising['stage'].value_counts()
        st.info(
            f"**Bottom line:** US World Cup search is **early-stage**. Live signal "
            f"is **buying** ({n.get('commercial',0)} rising queries — resale + "
            f"specific matchups) and **fandom** ({n.get('fandom',0)} — roster/player "
            f"chatter), plus a **Panini collectibles** surge "
            f"({n.get('collectibles',0)}). Almost no schedule/venue search "
            f"({n.get('logistics',0)}) — the market hasn't hit trip-planning mode.")

        # composition bar — magnitude = real count (no fake sizing)
        order_stages = ['commercial','fandom','collectibles','logistics']
        comp = go.Figure()
        for stg in order_stages:
            c = int((rising['stage'] == stg).sum())
            if c == 0:
                continue
            lbl = STAGE_LABEL[stg]
            comp.add_trace(go.Bar(
                x=[c], y=['Rising'], orientation='h', name=lbl,
                marker_color=STAGE_COLOR[lbl],
                text=f'{lbl} · {c}', textposition='inside',
                insidetextanchor='middle',
                hovertemplate=f'{lbl}: {c} rising queries<extra></extra>'))
        comp.update_layout(barmode='stack', height=110,
                           margin=dict(l=0, r=0, t=4, b=0), showlegend=False,
                           xaxis=dict(visible=False), yaxis=dict(visible=False),
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(color='white', size=13))
        st.plotly_chart(comp, use_container_width=True)

        # readable chips, grouped + colored by stage
        html = []
        for stg in order_stages:
            qs = rising[rising['stage'] == stg]['query'].tolist()
            if not qs:
                continue
            lbl, col = STAGE_LABEL[stg], STAGE_COLOR[STAGE_LABEL[stg]]
            chips = ''.join(
                f'<span style="display:inline-block;background:{col}22;'
                f'border:1px solid {col};color:#e8e8e8;border-radius:12px;'
                f'padding:2px 10px;margin:3px;font-size:13px">{q}</span>'
                for q in qs)
            html.append(
                f'<div style="margin:12px 0 2px"><span style="color:{col};'
                f'font-weight:600;font-size:15px">{lbl} ({len(qs)})</span></div>'
                f'<div style="line-height:2.1">{chips}</div>')
        st.markdown('\n'.join(html), unsafe_allow_html=True)
        st.caption('Bar = share of rising searches by stage (size = real count). '
                   'Established "top" searches are generic and set aside; '
                   'other-sport "world cups" and junk auto-filtered.')
    except Exception as e:
        st.info(f'Related-queries data unavailable: {e}')

    st.caption(
        '⚠️ Single source (Google Trends), national qualitative (per-city query '
        'data isn\'t reliable from Trends). Real demand would triangulate sales, '
        'travel, social — phase 2. Week-on-week momentum pending its own pull.')
