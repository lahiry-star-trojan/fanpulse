import requests
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

CENSUS_KEY = os.getenv('CENSUS_API_KEY')

US_CITIES = [
    ('06', '44000', 'Los Angeles'),
    ('36', '51000', 'New York/New Jersey'),
    ('12', '45000', 'Miami'),
    ('48', '19000', 'Dallas'),
    ('48', '35000', 'Houston'),
    ('53', '63000', 'Seattle'),
    ('13', '04000', 'Atlanta'),
    ('25', '07000', 'Boston'),
    ('42', '60000', 'Philadelphia'),
    ('29', '38000', 'Kansas City'),
    ('06', '67000', 'San Francisco'),
]

results = []

for state, place, city in US_CITIES:
    url = 'https://api.census.gov/data/2022/acs/acs5'
    params = {
        'get': 'B19013_001E,NAME',
        'for': f'place:{place}',
        'in': f'state:{state}',
        'key': CENSUS_KEY
    }
    r = requests.get(url, params=params)
    print(f'{city} — status: {r.status_code}')
    print(f'  response: {r.text[:150]}')
    if r.status_code == 200:
        try:
            data = r.json()
            income = int(data[1][0])
            print(f'  income: ${income:,}')
            results.append({
                'city': city,
                'median_income': income,
                'source': 'US Census ACS 2022'
            })
        except Exception as e:
            print(f'  PARSE ERROR: {e}')
    else:
        print(f'  FAILED')

international = [
    {'city': 'Toronto',     'median_income': 47580, 'source': 'Statistics Canada 2021'},
    {'city': 'Vancouver',   'median_income': 46620, 'source': 'Statistics Canada 2021'},
    {'city': 'Mexico City', 'median_income': 14200, 'source': 'INEGI Mexico 2020'},
    {'city': 'Guadalajara', 'median_income': 12800, 'source': 'INEGI Mexico 2020'},
    {'city': 'Monterrey',   'median_income': 16400, 'source': 'INEGI Mexico 2020'},
]
results.extend(international)

df = pd.DataFrame(results)
os.makedirs('data/raw', exist_ok=True)
df.to_csv('data/raw/city_incomes.csv', index=False)
print(f'\nSaved {len(df)} cities')
print(df.to_string())