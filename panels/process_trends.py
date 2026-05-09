import pandas as pd, os

df = pd.read_csv('data/raw/trends_serp.csv')

kw_cols = ['World Cup tickets','FIFA 2026','USMNT','Argentina soccer','Mexico soccer']
df['avg_interest'] = df[kw_cols].mean(axis=1)

# Use ALL rows per city (both time-series and summary)
city_scores = df.groupby('city')['avg_interest'].mean().reset_index()
city_scores.columns = ['city','demand_score']

min_s, max_s = city_scores['demand_score'].min(), city_scores['demand_score'].max()
city_scores['demand_score_norm'] = 100*(city_scores['demand_score']-min_s)/(max_s-min_s)

# WoW — only from rows with actual dates
dated = df[df['date'].notna()].copy()
try:
    dated['date'] = pd.to_datetime(dated['date'])
    recent = dated[dated['date'] >= dated['date'].max() - pd.Timedelta(days=7)]
    prior  = dated[(dated['date'] >= dated['date'].max()-pd.Timedelta(days=14)) &
                   (dated['date'] <  dated['date'].max()-pd.Timedelta(days=7))]
    wow = ((recent.groupby('city')['avg_interest'].mean() -
            prior.groupby('city')['avg_interest'].mean()) /
            prior.groupby('city')['avg_interest'].mean() * 100).reset_index()
    wow.columns = ['city','wow_change_pct']
    city_scores = city_scores.merge(wow, on='city', how='left')
except:
    city_scores['wow_change_pct'] = 0

city_scores['wow_change_pct'] = city_scores['wow_change_pct'].fillna(0).round(1)

os.makedirs('data/processed', exist_ok=True)
city_scores.to_csv('data/processed/trends_processed.csv', index=False)
print(city_scores.sort_values('demand_score_norm', ascending=False).to_string())