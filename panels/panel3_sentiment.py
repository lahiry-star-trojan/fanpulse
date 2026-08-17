import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast, re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

STOPWORDS = {
    'the','a','an','and','or','in','is','it','to','of','for','that',
    'this','with','on','at','be','was','are','have','i','you','we',
    'they','not','but','so','world','cup','soccer','football','game',
    'going','just','like','will','would','think','know','get','their',
    'from','been','has','had','can','all','more','also','about','when',
    'what','them','your','dont','cant','wont','its','very','really'
}

# Minimum comments for a team/city to appear in COMPARATIVE charts.
# n>=30 is the standard rule-of-thumb for treating a sample mean as
# reliable; below it an "average sentiment" is noise (Mexico had only 4
# comments). Low-sample groups are excluded from rankings and flagged
# transparently rather than silently compared.
MIN_SAMPLE = 30

def safe_list(x):
    try:
        val = ast.literal_eval(x) if isinstance(x, str) else x
        return val if isinstance(val, list) else []
    except:
        return []


# ── UNCERTAINTY HELPERS ──────────────────────────────────────────
# A mean of 4 comments is not on a different SCALE from a mean of 200 —
# it is on the same -1..+1 axis but far less CERTAIN. No rescaling fixes
# that; only showing the uncertainty does. We bootstrap a 95% CI per group
# so a tiny sample renders as a wide whisker = visibly unreliable.

def mean_ci(vals, n_boot=2000, ci=95, seed=42):
    """Bootstrap mean + (lo, hi) CI. Handles small n honestly (wide interval).
    Returns (mean, mean, mean) when n<2 (no interval estimable)."""
    vals = np.asarray(vals, dtype=float)
    m = float(vals.mean())
    if len(vals) < 2:
        return m, m, m
    rng  = np.random.default_rng(seed)
    boot = rng.choice(vals, size=(n_boot, len(vals)), replace=True).mean(axis=1)
    lo = float(np.percentile(boot, (100 - ci) / 2))
    hi = float(np.percentile(boot, 100 - (100 - ci) / 2))
    return m, lo, hi


def sent_color(v):
    return '#E74C3C' if v < 0 else ('#F39C12' if v < 0.2 else '#27AE60')


def ci_table(frame, key, min_n=3):
    """Per-group mean + 95% CI + n. Drops groups with n<min_n (no CI possible)."""
    rows = []
    for name, grp in frame.groupby(key):
        n = len(grp)
        if n < min_n:
            continue
        m, lo, hi = mean_ci(grp['compound'].values)
        rows.append({key: name, 'avg': m, 'lo': lo, 'hi': hi, 'n': n})
    return pd.DataFrame(rows)


def ci_bar(tbl, key, title):
    """Horizontal bar of mean sentiment with asymmetric 95% CI whiskers.
    Low-sample groups (n<MIN_SAMPLE) are faded + flagged, not hidden."""
    tbl    = tbl.sort_values('avg', ascending=True)
    labels = [f"{r[key]}  (n={int(r.n)})" + ("  ⚠" if r.n < MIN_SAMPLE else "")
              for _, r in tbl.iterrows()]
    colors = [sent_color(v) for v in tbl['avg']]
    opac   = [0.45 if n < MIN_SAMPLE else 0.95 for n in tbl['n']]
    fig = go.Figure(go.Bar(
        x=tbl['avg'], y=labels, orientation='h',
        marker=dict(color=colors, opacity=opac,
                    line=dict(color='rgba(255,255,255,0.25)', width=1)),
        error_x=dict(type='data', symmetric=False,
                     array=(tbl['hi'] - tbl['avg']).tolist(),
                     arrayminus=(tbl['avg'] - tbl['lo']).tolist(),
                     color='rgba(255,255,255,0.7)', thickness=1.5, width=5),
        hovertemplate='%{y}<br>avg sentiment %{x:.3f}<extra></extra>'
    ))
    fig.add_vline(x=0, line_dash='dot', line_color='rgba(255,255,255,0.3)')
    fig.update_layout(
        title=title, height=350,
        margin=dict(l=0, r=40, t=40, b=0),
        xaxis_title='Sentiment Score (−1 to +1)',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    return fig


def takeaway(tbl, key, label):
    """One plain-English sentence so a non-analytical reader gets the point
    without decoding the whiskers. Computed from the data, not hardcoded."""
    lean = lambda v: 'positive' if v >= 0.05 else ('negative' if v <= -0.05 else 'mixed')
    reliable = tbl[tbl['n'] >= MIN_SAMPLE].sort_values('avg', ascending=False)
    small    = tbl[tbl['n'] <  MIN_SAMPLE]
    if reliable.empty:
        return (f'**Bottom line:** no {label} has enough comments yet to call — '
                'treat every bar here as a rough hint, not a finding.')
    parts = [f'{r[key]} (leans {lean(r.avg)})' for _, r in reliable.iterrows()]
    joined = ' and '.join(parts) if len(parts) <= 2 else ', '.join(parts)
    verb = 'has' if len(parts) == 1 else 'have'
    msg = f'**Bottom line:** only {joined} {verb} enough comments to trust.'
    if not small.empty:
        msg += f' The faded {label}s are too small to rank — ignore their order.'
    return msg

def show_panel3():
    df = pd.read_csv('data/processed/youtube_tagged.csv')
    df['teams']  = df['teams'].apply(safe_list)
    df['cities'] = df['cities'].apply(safe_list)

    exploded = df.explode('teams')
    exploded = exploded[exploded['teams'].astype(str).str.len() > 1]

    st.subheader('💬 Social Sentiment — YouTube Fan Analysis')
    st.caption('2,100+ YouTube comments analyzed across FIFA World Cup 2026 content · '
               'snapshot from pre-tournament window (not live match reactions)')

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
        team_tbl = ci_table(exploded, 'teams', min_n=3)
        if not team_tbl.empty:
            st.plotly_chart(
                ci_bar(team_tbl, 'teams',
                       'Average Sentiment by Team (with confidence range)'),
                width='stretch'
            )
            st.info(takeaway(team_tbl, 'teams', 'team'))
            st.caption(
                'The line through each bar = how sure we can be. '
                'A long line means too few comments to trust the score. '
                f'Faded bars (⚠) have under {MIN_SAMPLE} comments.'
            )
            tiny    = exploded.groupby('teams').size()
            dropped = sorted([t for t, c in tiny.items()
                              if c < 3 and len(str(t)) > 1])
            if dropped:
                st.caption(f'Not shown — under 3 comments: {", ".join(dropped)}')
        else:
            st.info('Not enough tagged comments for a team comparison.')

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
        st.plotly_chart(fig2, width='stretch')

    st.divider()

    # ── ROW 2: TEAM DEEP DIVE ─────────────────────────────────────
    st.subheader('Team Deep Dive')
    st.caption('Pick a team below — the keywords, breakdown, and comments all '
               'update to that team. (Defaults to Argentina.)')
    team_counts   = exploded['teams'].value_counts().to_dict()
    teams_list    = sorted(exploded['teams'].dropna().unique().tolist())
    selected_team = st.selectbox(
        'Select a team:',
        teams_list,
        format_func=lambda t: f'{t}  (n={team_counts.get(t, 0)})'
    )
    team_df       = exploded[exploded['teams'] == selected_team]

    if team_counts.get(selected_team, 0) < MIN_SAMPLE:
        st.warning(
            f'Low sample: only {team_counts.get(selected_team, 0)} comments for '
            f'{selected_team}. Treat the breakdown below as directional, not reliable.'
        )

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
        st.plotly_chart(fig3, width='stretch')

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

    city_tbl = (ci_table(city_exp, 'cities', min_n=3)
                if not city_exp.empty else pd.DataFrame())

    if len(city_tbl) >= 3:
        st.plotly_chart(
            ci_bar(city_tbl, 'cities',
                   'Average Sentiment by Host City (with confidence range)'),
            width='stretch'
        )
        st.info(takeaway(city_tbl, 'cities', 'city'))
        st.caption(
            'Same idea as teams: a long line through a bar means too few '
            f'comments to trust. Faded bars have under {MIN_SAMPLE} comments.'
        )
    else:
        n_ok = len(city_tbl)
        st.info(
            'Not enough city-tagged comments yet to compare host cities fairly, '
            f'so this view is held back (only {n_ok} '
            f'{"city clears" if n_ok == 1 else "cities clear"} the minimum). '
            'Only ~85 of 2,119 comments name a host city — it unlocks as '
            'city-tagging improves.'
        )

    st.divider()
    st.caption('Search-interest and keyword trends now live in the Demand tab.')