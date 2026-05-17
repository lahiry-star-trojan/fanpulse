import streamlit as st
import requests, os, anthropic
from dotenv import load_dotenv
load_dotenv()

@st.cache_data(ttl=3600)
def get_all_news():
    queries = [
        'FIFA World Cup 2026 USA',
    'FIFA World Cup 2026 tickets prices',
    'USMNT World Cup 2026',
    'FIFA World Cup 2026 host cities fans',
    'FIFA World Cup 2026 Argentina Mexico',
    'FIFA World Cup 2026 opening ceremony',
    'FIFA World Cup 2026 squads roster',
    'FIFA World Cup 2026 schedule groups',
    'World Cup 2026 fan experience',
    'FIFA 2026 broadcast TV streaming',
    ]
    all_news = []
    seen_titles = set()

    for q in queries:
        params = {
            'engine': 'google_news',
            'q': q,
            'api_key': os.getenv('SERPAPI_KEY'),
            'gl': 'us',
            'hl': 'en',
            'num': 5
        }
        try:
            resp = requests.get('https://serpapi.com/search', params=params)
            results = resp.json().get('news_results', [])
            for r in results:
                title = r.get('title', '')
                if not title or title in ['Top news', 'News about Sports', 'Sports', 'Soccer']:
                    continue
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                source = r.get('source', '')
                if isinstance(source, dict):
                    source = source.get('name', '')
                all_news.append({
                    'title':     title,
                    'source':    source,
                    'date':      r.get('date', ''),
                    'link':      r.get('link', ''),
                    'snippet':   r.get('snippet', ''),
                    'thumbnail': r.get('thumbnail', ''),
                    'topic':     q
                })
        except Exception as e:
            print(f'Error: {e}')

    return all_news

@st.cache_data(ttl=3600)
def get_summary(title):
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=60,
            messages=[{
                'role': 'user',
                'content': f'In one sentence, what is this FIFA World Cup 2026 news story likely about: "{title}"'
            }]
        )
        return msg.content[0].text
    except:
        return 'Click headline to read full story'

def show_panel5():
    st.subheader('📰 FIFA World Cup 2026 — Live News & Buzz')
    st.caption('Google News headlines updated hourly | Click any headline to read full article')

    with st.spinner('Fetching latest FIFA 2026 news...'):
        news = get_all_news()

    if not news:
        st.error('No news fetched — check SERPAPI_KEY in .env')
        return

    c1, c2, c3 = st.columns(3)
    c1.metric('Stories Tracked', len(news))
    sources = list(set([n['source'] for n in news if n['source']]))
    c2.metric('News Sources', len(sources))
    c3.metric('Refresh Rate', 'Every Hour')

    st.divider()

    topics = [
        '🌍 All Topics',
        '🎟️ Tickets & Prices',
        '🇺🇸 USMNT',
        '🏟️ Host Cities & Fans',
        '⭐ Teams & Players',
    ]
    topic_map = {
        '🎟️ Tickets & Prices':   'FIFA World Cup 2026 tickets prices',
        '🇺🇸 USMNT':              'USMNT World Cup 2026',
        '🏟️ Host Cities & Fans': 'FIFA World Cup 2026 host cities fans',
        '⭐ Teams & Players':     'FIFA World Cup 2026 Argentina Mexico',
    }

    selected = st.selectbox('Filter by topic:', topics)
    filtered = news if selected == '🌍 All Topics' else [
        n for n in news if n['topic'] == topic_map.get(selected, '')
    ]

    st.markdown(f"**{len(filtered)} stories**")
    st.divider()

    for item in filtered:
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"### [{item['title']}]({item['link']})")
                if item.get('snippet'):
                    st.markdown(item['snippet'])
                else:
                    summary = get_summary(item['title'])
                    st.caption(summary)
                source_str = f"**{item['source']}**" if item['source'] else ''
                date_str = f"· {item['date']}" if item['date'] else ''
                st.caption(f"{source_str} {date_str}")
            with col2:
                if item.get('thumbnail'):
                    st.image(item['thumbnail'], width=120)
            st.divider()