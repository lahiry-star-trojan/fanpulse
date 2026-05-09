import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COORDS = {
    'Los Angeles':   (34.0522, -118.2437),
    'New York':      (40.7128, -74.0060),
    'Miami':         (25.7617, -80.1918),
    'Dallas':        (32.7767, -96.7970),
    'Houston':       (29.7604, -95.3698),
    'San Francisco': (37.7749, -122.4194),
    'Seattle':       (47.6062, -122.3321),
    'Atlanta':       (33.7490, -84.3880),
    'Boston':        (42.3601, -71.0589),
    'Philadelphia':  (39.9526, -75.1652),
    'Kansas City':   (39.0997, -94.5786),
}

TEXT_POS = {
    'Los Angeles':   'middle left',
    'San Francisco': 'top left',
    'Seattle':       'top center',
    'Dallas':        'bottom left',
    'Houston':       'bottom right',
    'Kansas City':   'top center',
    'Atlanta':       'top right',
    'Miami':         'bottom right',
    'New York':      'top right',
    'Boston':        'top right',
    'Philadelphia':  'bottom left',
}

def show_panel1():
    df = pd.read_csv('data/processed/trends_processed.csv')
    df['lat'] = df['city'].map(lambda x: COORDS.get(x,(0,0))[0])
    df['lon'] = df['city'].map(lambda x: COORDS.get(x,(0,0))[1])
    df['wow_change_pct'] = df['wow_change_pct'].fillna(0).round(1)
    df['demand_score_norm'] = df['demand_score_norm'].round(1)

    st.subheader('🗺️ US Fan Demand by Host City')
    st.caption('Google Trends search volume for FIFA World Cup 2026 keywords')

    top     = df.loc[df['demand_score_norm'].idxmax()]
    bottom  = df.loc[df['demand_score_norm'].idxmin()]
    rising  = df.loc[df['wow_change_pct'].idxmax()]
    avg     = df['demand_score_norm'].mean()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric('🏆 Highest Demand',   top['city'],    f"{top['demand_score_norm']:.0f}/100")
    c2.metric('📉 Needs Activation', bottom['city'], f"{bottom['demand_score_norm']:.0f}/100")
    c3.metric('📈 Fastest Rising',   rising['city'], f"+{rising['wow_change_pct']:.1f}% WoW")
    c4.metric('📊 Avg Score',        f"{avg:.0f}/100", f"{len(df)} cities")

    st.divider()

    fig = go.Figure()

    for _, row in df.iterrows():
        size  = max(row['demand_score_norm'] * 0.5, 10)
        color = '#E94560' if row['demand_score_norm'] >= 90 else (
                '#F39C12' if row['demand_score_norm'] >= 50 else '#3498DB')

        fig.add_trace(go.Scattergeo(
            lat=[row['lat']],
            lon=[row['lon']],
            mode='markers+text',
            marker=dict(size=size, color=color, opacity=0.8,
                       line=dict(color='white', width=1)),
            text=f"{row['city']}  {row['demand_score_norm']:.0f}/100",
            textposition=TEXT_POS.get(row['city'], 'top center'),
            textfont=dict(size=10, color='white'),
            hovertemplate=(
                f"<b>{row['city']}</b><br>"
                f"Demand Score: {row['demand_score_norm']:.1f}/100<br>"
                f"WoW Change: {row['wow_change_pct']:+.1f}%<br>"
                "<extra></extra>"
            ),
            name=row['city']
        ))

    fig.update_layout(
        geo=dict(
            scope='usa',
            showland=True,      landcolor='#1E2A3A',
            showocean=True,     oceancolor='#0F1923',
            showlakes=True,     lakecolor='#0F1923',
            showcoastlines=True, coastlinecolor='#444',
            showsubunits=True,  subunitcolor='#333',
            bgcolor='#0F1923',
            projection_type='albers usa'
        ),
        paper_bgcolor='#0F1923',
        showlegend=False,
        height=520,
        margin=dict(l=0,r=0,t=30,b=0),
        title=dict(
            text='🔴 High Demand  🟡 Medium  🔵 Low',
            font=dict(color='white', size=11),
            x=0.5
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('City Rankings')
        show = df[['city','demand_score_norm','wow_change_pct']].copy()
        show.columns = ['City','Score (0-100)','WoW Change (%)']
        show = show.sort_values('Score (0-100)', ascending=False)
        show['WoW Change (%)'] = show['WoW Change (%)'].apply(
            lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%")
        st.dataframe(show, use_container_width=True, hide_index=True)

    with col2:
        st.subheader('Demand Score Comparison')
        fig2 = px.bar(
            df.sort_values('demand_score_norm', ascending=True),
            x='demand_score_norm', y='city',
            orientation='h',
            color='demand_score_norm',
            color_continuous_scale=['#3498DB','#F39C12','#E94560'],
            text='demand_score_norm',
            labels={'demand_score_norm':'Score','city':''},
        )
        fig2.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig2.update_layout(
            height=350,
            coloraxis_showscale=False,
            margin=dict(l=0,r=60,t=10,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader('🔍 Search Interest Over Time')
    try:
        raw = pd.read_csv('data/raw/trends_serp.csv')
        raw = raw[raw['date'].notna()]
        raw['date'] = pd.to_datetime(raw['date'])
        kw_cols = ['World Cup tickets','FIFA 2026','USMNT','Argentina soccer','Mexico soccer']
        city_pick = st.selectbox('Select city:', sorted(raw['city'].unique()))
        city_data = raw[raw['city']==city_pick]
        melted = city_data.melt(id_vars='date', value_vars=kw_cols,
                                var_name='Keyword', value_name='Interest')
        fig3 = px.line(melted, x='date', y='Interest', color='Keyword',
                       title=f'What are {city_pick} fans searching for?')
        fig3.update_layout(height=350,
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(color='white'))
        st.plotly_chart(fig3, use_container_width=True)
        st.caption('💡 Rising keywords = growing fan interest. Flat = market needs activation.')
    except Exception as e:
        st.info(f'Trend line error: {e}')