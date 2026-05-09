import streamlit as st
import pandas as pd
import plotly.express as px

def show_panel2():
    df = pd.read_csv('data/processed/tickets_processed.csv')
    df_cat = pd.read_csv('data/processed/tickets_by_category.csv')

    st.subheader('🎟️ Ticket Price Intelligence')
    st.caption('Official FIFA pricing across match types and seat categories')

    # KPI row
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Avg Match Price', f"${df['median_price'].mean():,.0f}")
    c2.metric('Final Ticket (Front)', '$32,179')
    c3.metric('Cheapest Entry', f"${df['lowest_price'].min():,.0f}")
    c4.metric('Hot Matches 2x+', len(df[df['tier']=='Hot']))

    st.divider()

    # Tab view
    t1, t2 = st.tabs(['📊 Match Comparison', '🪑 By Seat Category'])

    with t1:
        cities = ['All Cities'] + sorted(df['city'].dropna().unique().tolist())
        sel = st.selectbox('Filter by city:', cities)
        plot_df = df if sel == 'All Cities' else df[df['city']==sel]

        cmap = {'Hot':'#E74C3C','Above Avg':'#F39C12','Standard':'#3498DB'}
        fig = px.bar(
            plot_df.sort_values('median_price'),
            x='median_price', y='title',
            color='tier', color_discrete_map=cmap,
            orientation='h', text='median_price',
            title='Average Ticket Price by Match',
            labels={'median_price':'Avg Price ($)','title':'Match','tier':'Tier'}
        )
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig.update_layout(height=500, margin=dict(r=120))
        st.plotly_chart(fig, use_container_width=True)

        # Price range scatter
        st.subheader('Price Range by Match (Min → Max)')
        fig2 = px.scatter(
            df, x='title', y='median_price',
            size='listings', color='tier',
            color_discrete_map=cmap,
            title='Median Price + Listing Volume by Match',
            labels={'title':'Match','median_price':'Median Price ($)','listings':'# Listings'}
        )
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    with t2:
        matches = sorted(df_cat['title'].unique().tolist())
        sel_match = st.selectbox('Select match:', matches)
        match_df = df_cat[df_cat['title']==sel_match].sort_values('median_price')

        fig3 = px.bar(
            match_df,
            x='category', y='median_price',
            color='category',
            text='median_price',
            title=f'Seat Category Prices — {sel_match}',
            labels={'category':'Seat Category','median_price':'Price ($)'}
        )
        fig3.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig3.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(
            match_df[['category','lowest_price','median_price','listings']],
            use_container_width=True, hide_index=True
        )