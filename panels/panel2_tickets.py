import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

STAGE_ORDER = {
    'Group Stage':1,'Round of 32':2,'Round of 16':3,
    'Quarterfinals':4,'Semifinals':5,'Third Place Playoff':6,'Final':7
}

def load_city_incomes():
    try:
        df = pd.read_csv('data/raw/city_incomes.csv')
        return dict(zip(df['city'], df['median_income']))
    except:
        return {
            'Los Angeles':76244,'New York/New Jersey':76607,
            'Miami':54858,'Dallas':63985,'Houston':60440,
            'Seattle':116068,'Atlanta':77655,'Boston':89212,
            'Philadelphia':57537,'Kansas City':65256,
            'San Francisco':136689,'Toronto':47580,
            'Vancouver':46620,'Mexico City':14200,
            'Guadalajara':12800,'Monterrey':16400
        }

def show_panel2():
    df     = pd.read_csv('data/processed/tickets_processed.csv')
    df_cat = pd.read_csv('data/processed/tickets_by_category.csv')
    CITY_INCOME = load_city_incomes()

    df['stage_order'] = df['stage'].map(STAGE_ORDER).fillna(0)

    st.subheader('Ticket Price Intelligence')
    st.caption('Official FIFA pricing across 104 matches — what it costs, what it means, who can afford it')

    group    = df[df['stage']=='Group Stage']['median_price'].mean()
    final    = df[df['stage']=='Final']['median_price'].max()
    cheapest = df['lowest_price'].min()
    multi    = round(final / cheapest)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Cheapest Entry',  f'${cheapest:,.0f}', 'Group Stage Cat 3')
    c2.metric('Final Avg Price', f'${final:,.0f}',    'New York')
    c3.metric('Avg Group Stage', f'${group:,.0f}',    'per ticket')
    c4.metric('Price Multiplier',f'{multi}x',         'Group to Final')

    st.divider()

    st.subheader('Price Escalation Through the Tournament')
    st.caption('Follow your team from group stage to the final')

    stage_avg = df.groupby(['stage','stage_order']).agg(
        median_price=('median_price','mean'),
        lowest_price=('lowest_price','min')
    ).reset_index().sort_values('stage_order')

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=stage_avg['stage'], y=stage_avg['median_price'],
        name='Median Price', mode='lines+markers',
        line=dict(color='#E94560', width=3),
        marker=dict(size=10)
    ))
    fig1.add_trace(go.Scatter(
        x=stage_avg['stage'], y=stage_avg['lowest_price'],
        name='Cheapest Ticket', mode='lines+markers',
        line=dict(color='#3498DB', width=2, dash='dot'),
        marker=dict(size=8)
    ))
    fig1.update_layout(
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        yaxis=dict(title='Price ($)', tickprefix='$'),
        xaxis=dict(title='Tournament Stage'),
        legend=dict(x=0.02, y=0.98)
    )
    st.plotly_chart(fig1, use_container_width=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.info('Buy group stage now — prices jump 3-4x in knockouts')
    col_b.warning('R32 = best value knockout ticket')
    col_c.error('Final = $14K avg. Only 1 match.')

    st.divider()

    st.subheader('Who Can Actually Afford This?')
    st.caption('Days of work at US median wage ($74,580/yr) to buy one ticket')

    us_income = 74580
    tiers = [
        {'label':'Group Stage (cheapest)',  'price':605},
        {'label':'Group Stage (Cat 3)',      'price':1120},
        {'label':'Group Stage (Cat 2)',      'price':1940},
        {'label':'Group Stage (Cat 1)',      'price':2735},
        {'label':'Round of 32',             'price':790},
        {'label':'Round of 16',             'price':745},
        {'label':'Quarterfinal',            'price':1120},
        {'label':'Semifinal',               'price':2705},
        {'label':'Final (Cat 1)',           'price':8000},
        {'label':'Final (Front Row)',       'price':32179},
    ]
    aff = pd.DataFrame(tiers)
    aff['days_of_work'] = (aff['price'] / (us_income/365)).round(1)
    aff['affordability'] = aff['price'].apply(
        lambda x: 'Accessible' if x<1000 else
                 ('Stretch'    if x<3000 else
                 ('Premium'    if x<10000 else 'Ultra'))
    )
    color_map = {
        'Accessible':'#27AE60','Stretch':'#F39C12',
        'Premium':'#E74C3C','Ultra':'#8E44AD'
    }
    fig2 = px.bar(
        aff, x='label', y='days_of_work',
        color='affordability', color_discrete_map=color_map,
        text='days_of_work',
        title='Days of Work at US Median Wage to Buy One Ticket',
        labels={'label':'Ticket Type','days_of_work':'Days of Work','affordability':''}
    )
    fig2.update_traces(texttemplate='%{text:.1f}d', textposition='outside')
    fig2.update_layout(
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis_tickangle=-30,
        yaxis=dict(title='Days of Work'),
        showlegend=True
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader('Host City Affordability Gap')
    st.caption('Source: US Census ACS 2022, Statistics Canada 2021, INEGI Mexico 2020')

    city_avg = df.groupby('city')['median_price'].mean().reset_index()
    city_avg.columns = ['city','avg_ticket']
    city_avg['median_income'] = city_avg['city'].map(CITY_INCOME)
    city_avg = city_avg.dropna()
    city_avg['burden_pct'] = (city_avg['avg_ticket'] / city_avg['median_income'] * 100).round(1)
    city_avg['burden_label'] = city_avg['burden_pct'].apply(
        lambda x: 'High Burden' if x>4 else ('Medium Burden' if x>2.5 else 'Lower Burden')
    )
    city_avg['match_count'] = city_avg['city'].map(df.groupby('city')['title'].nunique())

    fig3 = px.scatter(
        city_avg,
        x='median_income', y='avg_ticket',
        size='match_count',
        color='burden_label',
        text='city',
        color_discrete_map={
            'High Burden':'#E74C3C',
            'Medium Burden':'#F39C12',
            'Lower Burden':'#27AE60'
        },
        title='City Median Income vs Avg Ticket Price (bubble = matches hosted)',
        labels={
            'median_income':'City Median Household Income ($)',
            'avg_ticket':'Avg Ticket Price ($)',
            'burden_label':'Affordability Burden'
        }
    )
    fig3.update_traces(textposition='top center', textfont_size=10, marker=dict(opacity=0.85))
    fig3.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(tickprefix='$', tickformat=','),
        yaxis=dict(tickprefix='$', tickformat=',')
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption('Mexican cities face highest burden — global ticket prices vs local wages.')

    st.divider()

    st.subheader('Browse All 104 Matches')
    col1, col2 = st.columns(2)
    with col1:
        cities   = ['All Cities'] + sorted(df['city'].dropna().unique().tolist())
        sel_city = st.selectbox('Filter by city:', cities)
    with col2:
        stages    = ['All Stages'] + sorted(df['stage'].dropna().unique().tolist(), key=lambda x: STAGE_ORDER.get(x,0))
        sel_stage = st.selectbox('Filter by stage:', stages)

    plot_df = df.copy()
    if sel_city  != 'All Cities':  plot_df = plot_df[plot_df['city']==sel_city]
    if sel_stage != 'All Stages':  plot_df = plot_df[plot_df['stage']==sel_stage]
    plot_df = plot_df.sort_values('median_price', ascending=False).head(20)

    cmap = {'Hot':'#E74C3C','Above Avg':'#F39C12','Standard':'#3498DB'}
    fig4 = px.bar(
        plot_df,
        x='median_price', y='title',
        color='tier', color_discrete_map=cmap,
        orientation='h', text='median_price',
        labels={'median_price':'Median Price ($)','title':'Match','tier':'Tier'}
    )
    fig4.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig4.update_layout(
        height=550, margin=dict(r=120),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader('Seat Category Breakdown')
    matches_list = sorted(df_cat['title'].unique().tolist())
    sel_match    = st.selectbox('Select match:', matches_list)
    match_df     = df_cat[df_cat['title']==sel_match].sort_values('median_price')

    fig5 = px.bar(
        match_df, x='category', y='median_price',
        color='category', text='median_price',
        labels={'category':'Seat Category','median_price':'Price ($)'}
    )
    fig5.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig5.update_layout(
        height=350, showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    st.plotly_chart(fig5, use_container_width=True)
