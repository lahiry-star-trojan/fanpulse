import pandas as pd, os

df = pd.read_csv('data/raw/seatgeek_raw.csv')

for col in ['lowest_price','avg_price','median_price']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['median_price'])

# Match-level summary (avg across categories)
match_summary = df.groupby(['title','city','date','stage']).agg(
    lowest_price=('lowest_price','min'),
    median_price=('median_price','mean'),
    avg_price=('avg_price','mean'),
    listings=('listings','sum')
).reset_index()

overall_avg = match_summary['median_price'].mean()
match_summary['price_premium'] = match_summary['median_price'] / overall_avg
match_summary['tier'] = match_summary['price_premium'].apply(
    lambda x: 'Hot' if x>=2 else ('Above Avg' if x>=1.2 else 'Standard')
)
match_summary = match_summary.sort_values('median_price', ascending=False)

os.makedirs('data/processed', exist_ok=True)
match_summary.to_csv('data/processed/tickets_processed.csv', index=False)

# Also save category-level for detailed view
df.to_csv('data/processed/tickets_by_category.csv', index=False)

print(f'Overall avg: ${overall_avg:.0f}')
print(match_summary[['title','city','median_price','tier']].head(10))