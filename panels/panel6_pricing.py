import streamlit as st
import pandas as pd
import plotly.graph_objects as go

SIGNAL_COLOR = {'Underpriced':'#1ABC9C', 'Overpriced':'#E94560', 'Efficient':'#7F8FA6'}

def show_panel6():
    st.subheader('💸 Demand vs. Resale Price — Where the Market Misprices')
    st.caption('US search demand (national, both teams) vs live SeatGeek resale '
               'floor, per match. Snapshot — resale prices move; demand = search interest, '
               'not ticket sales. Single point in time.')

    try:
        df = pd.read_csv('data/processed/pricing_scatter.csv')
    except FileNotFoundError:
        st.error('Run build_pricing_scatter.py first.'); return

    # drop pure-noise matches (neither team has a real demand read)
    df = df[df['teams_known'] >= 1].copy()
    if df.empty:
        st.warning('No matches with a demand read.'); return

    # ── the quadrant scatter ────────────────────────────────────────
    med_d = df['demand'].median()
    med_p = df['price'].median()

    fig = go.Figure()
    # quadrant guide lines (median split)
    fig.add_hline(y=med_p, line_dash='dot', line_color='rgba(255,255,255,0.2)')
    fig.add_vline(x=med_d, line_dash='dot', line_color='rgba(255,255,255,0.2)')

    for sig, g in df.groupby('signal'):
        fig.add_trace(go.Scatter(
            x=g['demand'], y=g['price'], mode='markers+text',
            text=g['match'].str.replace(' vs ', ' v '), textposition='top center',
            textfont=dict(size=9, color='rgba(255,255,255,0.55)'),
            marker=dict(
                size=[16 if k == 2 else 10 for k in g['teams_known']],
                color=SIGNAL_COLOR.get(sig, '#888'),
                opacity=[0.95 if k == 2 else 0.5 for k in g['teams_known']],
                line=dict(width=1, color='rgba(255,255,255,0.3)')),
            name=sig,
            hovertemplate='%{text}<br>demand %{x}<br>$%{y}<extra></extra>'))

    fig.update_layout(
        height=560, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(255,255,255,0.85)',
        xaxis=dict(title='US search demand (higher = more searched) →',
                   gridcolor='rgba(255,255,255,0.08)'),
        yaxis=dict(title='Resale floor price ($) →',
                   gridcolor='rgba(255,255,255,0.08)'),
        legend=dict(orientation='h', y=1.08, x=0))
    # quadrant labels
    fig.add_annotation(x=df['demand'].max(), y=df['price'].min(),
                       text='High demand · low price<br><b>UNDERPRICED</b>',
                       showarrow=False, font=dict(size=10, color='#1ABC9C'),
                       xanchor='right', yanchor='bottom')
    fig.add_annotation(x=df['demand'].min(), y=df['price'].max(),
                       text='Low demand · high price<br><b>OVERPRICED</b>',
                       showarrow=False, font=dict(size=10, color='#E94560'),
                       xanchor='left', yanchor='top')
    st.plotly_chart(fig, width='stretch')
    st.caption('Big dots = both teams have a real demand read; faded small dots = '
               'one team approximated (minnow opponent). Lines = median split. '
               'Diagonal logic: above the trend = market charging more than search '
               'demand suggests; below = potential value.')

    # ── ranked mispricing table ─────────────────────────────────────
    st.subheader('Most Mispriced Matches')
    show = df.sort_values('mismatch', ascending=False)[
        ['match','demand','price','signal']].copy()
    show.columns = ['Match','Demand','Resale floor ($)','Signal']
    show['Resale floor ($)'] = show['Resale floor ($)'].map('${:,}'.format)
    st.dataframe(show, width='stretch', hide_index=True)

    st.info('**Bottom line:** the resale market is mostly **efficient** — price '
            'tracks search demand for most fixtures. The signal is in the outliers: '
            'a few matches priced above what US search interest supports '
            '(overpriced), and a few value plays (underpriced). Demand here is search '
            'interest, a leading indicator — not a substitute for actual sales data.')

if __name__ == '__main__':
    show_panel6()
