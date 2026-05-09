import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast, re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

STOPWORDS = {
    'the','a','an','and','or','in','is','it','to','of','for','that',
    'this','with','on','at','be','was','are','have','i','you','we',
    'they','not','but','so','world','cup','soccer','football','game',
    'going','just','like','will','would','think','know','get','their',
    'from','been','has','had','can','all','more','also','about','when',
    'what','them','your','dont','cant','wont','its','very','really'
}

def safe_list(x):
    try:
        val = ast.literal_eval(x) if isinstance(x, str) else x
        return val if isinstance(val, list) else []
    except:
        return []

def show_panel3():
    df = pd.read_csv('data/processed/youtube_tagged.csv')
    df['teams']  = df['teams'].apply(safe_list)
    df['cities'] = df['cities'].apply(safe_list)

    exploded = df.explode('teams')
    exploded = exploded[exploded['teams'].astype(str).str.len() > 1]

    st.subheader('💬 Social Sentiment — YouTube Fan Analysis')
    st.caption('2,100+ YouTube comments analyzed across FIFA World Cup 2026 content')

    # ── KPI ROW ──────────────────────────────────────────────────
    total   = len(df)
    pos_pct = round(len(df[df['sentiment']=='Positive']) / total * 100)
    neg_pct = round(len(df[df['sentiment']=='Negative']) / total * 100)
    teams_n = exploded['teams'].nunique()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric('Total Comments', f'{total:,}')
    k2.metric('Positive',       f'{pos_pct}%')
    k3.metric('Negative',       f'{neg_pct}%')
    k4.metric('Teams Tracked',  teams_n)

    st.divider()

    # ── ROW 1: SENTIMENT BAR + DONUT ─────────────────────────────
    col1, col2 = st.columns([2,1])

    with col1:
        team_agg = exploded.groupby('teams').agg(
            avg_sent=('compound','mean'),
            comments=('compound','count')
        ).reset_index().sort_values('avg_sent', ascending=True)

        fig = px.bar(
            team_agg, x='avg_sent', y='teams',
            orientation='h',
            color='avg_sent',
            text='comments',
            color_continuous_scale=['#E74C3C','#F39C12','#27AE60'],
            title='Average Sentiment Score by Team',
            labels={'avg_sent':'Sentiment Score','teams':'','comments':'Comments'}
        )
        fig.update_traces(texttemplate='%{text} comments', textposition='outside')
        fig.update_layout(
            height=350, coloraxis_showscale=False,
            margin=dict(l=0,r=80,t=40,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sent_counts = df['sentiment'].value_counts().reset_index()
        sent_counts.columns = ['Sentiment','Count']
        fig2 = px.pie(
            sent_counts, names='Sentiment', values='Count',
            hole=0.5,
            color='Sentiment',
            color_discrete_map={
                'Positive':'#27AE60',
                'Neutral':'#F39C12',
                'Negative':'#E74C3C'
            },
            title='Overall Split'
        )
        fig2.update_layout(
            height=350, margin=dict(l=0,r=0,t=40,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── ROW 2: TEAM DEEP DIVE ─────────────────────────────────────
    st.subheader('Team Deep Dive')
    teams_list    = sorted(exploded['teams'].dropna().unique().tolist())
    selected_team = st.selectbox('Select a team:', teams_list)
    team_df       = exploded[exploded['teams'] == selected_team]

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(f'**Top Keywords — {selected_team} fans**')
        all_words   = ' '.join(team_df['text'].fillna('').tolist()).lower()
        clean_words = ' '.join([
            w for w in re.findall(r'\b[a-z]{4,}\b', all_words)
            if w not in STOPWORDS
        ])
        if clean_words:
            wc = WordCloud(
                width=600, height=300,
                background_color='#0F1923',
                colormap='Blues',
                max_words=50
            ).generate(clean_words)
            fig_wc, ax = plt.subplots(figsize=(6,3))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            fig_wc.patch.set_facecolor('#0F1923')
            st.pyplot(fig_wc)
            plt.close()
        else:
            st.info('Not enough text data')

    with col4:
        st.markdown(f'**Sentiment Breakdown — {selected_team}**')
        team_sent = team_df['sentiment'].value_counts().reset_index()
        team_sent.columns = ['Sentiment','Count']
        fig3 = px.bar(
            team_sent, x='Sentiment', y='Count',
            color='Sentiment',
            color_discrete_map={
                'Positive':'#27AE60',
                'Neutral':'#F39C12',
                'Negative':'#E74C3C'
            },
            title=f'{selected_team} Comment Sentiment'
        )
        fig3.update_layout(
            height=300, showlegend=False,
            margin=dict(l=0,r=0,t=40,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # ── ROW 3: TOP COMMENTS ───────────────────────────────────────
    st.subheader(f'Top Fan Comments — {selected_team}')
    tab_pos, tab_neg = st.tabs(['👍 Most Positive','👎 Most Negative'])

    with tab_pos:
        top_pos = (team_df[team_df['sentiment']=='Positive']
                   .sort_values('compound', ascending=False).head(5))
        for _, row in top_pos.iterrows():
            st.markdown(f'> {row["text"][:300]}')
            st.caption(f'Score: {row["compound"]:.3f} | Likes: {int(row.get("likes",0))}')
            st.divider()

    with tab_neg:
        top_neg = (team_df[team_df['sentiment']=='Negative']
                   .sort_values('compound', ascending=True).head(5))
        for _, row in top_neg.iterrows():
            st.markdown(f'> {row["text"][:300]}')
            st.caption(f'Score: {row["compound"]:.3f} | Likes: {int(row.get("likes",0))}')
            st.divider()

    st.divider()

    # ── ROW 4: CITY BREAKDOWN ─────────────────────────────────────
    st.subheader('Fan Activity by City')
    city_exp = df.explode('cities')
    city_exp = city_exp[city_exp['cities'].astype(str).str.len() > 1]

    if not city_exp.empty:
        city_agg = city_exp.groupby('cities').agg(
            avg_sent=('compound','mean'),
            comments=('compound','count')
        ).reset_index()
        fig4 = px.bar(
            city_agg.sort_values('comments', ascending=False),
            x='cities', y='comments',
            color='avg_sent',
            color_continuous_scale=['#E74C3C','#F39C12','#27AE60'],
            title='Comment Volume + Sentiment by Host City',
            labels={'cities':'City','comments':'# Comments','avg_sent':'Avg Sentiment'}
        )
        fig4.update_layout(
            height=350, margin=dict(l=0,r=0,t=40,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info('Not enough city-tagged comments yet')

    st.divider()

    # ── ROW 5: WHAT FANS ACTUALLY SEARCH ─────────────────────────
    st.subheader('🔍 What Are Fans Actually Searching For?')
    st.caption('Google Trends search volume across FIFA World Cup 2026 keywords')

    try:
        trends = pd.read_csv('data/raw/trends_serp.csv')
        trends = trends[trends['date'].notna()].copy()
        trends['date'] = pd.to_datetime(trends['date'])

        kw_cols = ['World Cup tickets','FIFA 2026','USMNT',
                   'Argentina soccer','Mexico soccer']

        # Chart 1: keyword totals
        kw_totals = trends[kw_cols].mean().reset_index()
        kw_totals.columns = ['Keyword','Avg Search Volume']
        kw_totals = kw_totals.sort_values('Avg Search Volume', ascending=True)

        fig_kw = px.bar(
            kw_totals,
            x='Avg Search Volume', y='Keyword',
            orientation='h',
            color='Avg Search Volume',
            color_continuous_scale='Blues',
            title='Top Searched Keywords — FIFA World Cup 2026 (US)',
            text='Avg Search Volume'
        )
        fig_kw.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_kw.update_layout(
            height=320, coloraxis_showscale=False,
            margin=dict(l=0,r=80,t=40,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_kw, use_container_width=True)
        st.caption('💡 FIFA 2026 = highest awareness. World Cup tickets = commercial intent. Team searches = fan engagement.')

        st.divider()

        # Chart 2: search over time
        st.markdown('**Search Interest Over Time — All Keywords**')
        city_opts = ['All Cities'] + sorted(trends['city'].unique().tolist())
        sel_city  = st.selectbox('Filter by city:', city_opts, key='trend_city')

        if sel_city == 'All Cities':
            trend_df = trends.groupby('date')[kw_cols].mean().reset_index()
        else:
            trend_df = trends[trends['city']==sel_city][['date']+kw_cols].copy()

        melted = trend_df.melt(
            id_vars='date',
            value_vars=kw_cols,
            var_name='Keyword',
            value_name='Search Interest'
        )

        fig_time = px.line(
            melted, x='date', y='Search Interest',
            color='Keyword',
            title=f'Search Volume Over Time — {sel_city}',
            labels={'date':'Date','Search Interest':'Search Volume (0-100)'}
        )
        fig_time.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_time, use_container_width=True)
        st.caption('💡 Rising lines = growing interest. Flat = market needs activation.')

        st.divider()

        # Chart 3: city vs keyword heatmap
        st.markdown('**Which Cities Search Which Keywords Most?**')
        city_kw = trends.groupby('city')[kw_cols].mean().round(1)

        fig_heat = px.imshow(
            city_kw,
            color_continuous_scale='Blues',
            title='Search Interest Heatmap — City vs Keyword',
            labels=dict(x='Keyword', y='City', color='Interest'),
            aspect='auto',
            text_auto=True
        )
        fig_heat.update_layout(
            height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption('💡 Dark blue = high interest. Shows which cities need which message.')

    except Exception as e:
        st.info(f'Search trends unavailable: {e}')