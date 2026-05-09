from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

youtube = build('youtube', 'v3',
                developerKey=os.getenv('YOUTUBE_API_KEY'))

analyzer = SentimentIntensityAnalyzer()

# Search queries — one per team/topic
QUERIES = [
    'FIFA World Cup 2026',
    'USMNT World Cup 2026',
    'Argentina World Cup 2026',
    'Mexico World Cup 2026',
    'Brazil World Cup 2026',
    'England World Cup 2026',
    'World Cup Miami 2026',
    'World Cup Los Angeles 2026',
    'World Cup Dallas 2026',
]

all_comments = []

for query in QUERIES:
    print(f'Searching: {query}...')

    # Step 1: find top videos for this query
    search_resp = youtube.search().list(
        q=query,
        part='id,snippet',
        type='video',
        maxResults=5,
        order='viewCount',
        relevanceLanguage='en',
        regionCode='US'
    ).execute()

    video_ids = [item['id']['videoId']
                 for item in search_resp.get('items', [])]

    # Step 2: get comments from each video
    for vid_id in video_ids:
        try:
            comments_resp = youtube.commentThreads().list(
                part='snippet',
                videoId=vid_id,
                maxResults=50,
                order='relevance',
                textFormat='plainText'
            ).execute()

            for item in comments_resp.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                text = comment.get('textDisplay', '')
                likes = comment.get('likeCount', 0)

                # Only keep comments with some engagement
                if len(text) > 10:
                    score = analyzer.polarity_scores(text)
                    all_comments.append({
                        'query': query,
                        'video_id': vid_id,
                        'text': text[:500],
                        'likes': likes,
                        'pos': score['pos'],
                        'neg': score['neg'],
                        'neu': score['neu'],
                        'compound': score['compound'],
                        'sentiment': ('Positive' if score['compound'] > 0.05
                                      else 'Negative' if score['compound'] < -0.05
                                      else 'Neutral')
                    })
        except Exception as e:
            print(f'  Skipped video {vid_id}: {e}')
            continue

    print(f'  Total so far: {len(all_comments)} comments')

df = pd.DataFrame(all_comments)
os.makedirs('data/raw', exist_ok=True)
df.to_csv('data/raw/youtube_raw.csv', index=False)
print(f'\nSAVED {len(df)} comments to data/raw/youtube_raw.csv')
print(df['sentiment'].value_counts())
