# Import modules
import requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Get data
url = 'https://remoteok.com/api'
headers = {'User-Agent': "job_market_analyzer"}
response = requests.get(url, headers=headers)

print(response.status_code)

data = response.json()
print(type(data))
print(len(data))

print(data[1])

jobs = []

for post in data[1:]:
    job = {
        'title': post.get('position', ''),
        'company': post.get('company', ''),
        'location': post.get('location', ''),
        'salary_min': post.get('salary_min', None),
        'salary_max': post.get('salary_max', None),
        'tags': post.get('tags', []),
        'date': post.get('date', ''),
        'url': post.get('url', '')
    }
    jobs.append(job)
df = pd.DataFrame(jobs)


# Check what we're working with
print(df.columns.tolist())
print(df.shape)
print(df.dtypes)

print(df.salary_min.describe())
print(df.date.head())
print(df.location.value_counts().head(10))

# Replace 0's with NaN
df.salary_min = df.salary_min.replace(0, np.nan)
df.salary_max = df.salary_max.replace(0, np.nan)

# Convert date to datetime
df.date = pd.to_datetime(df.date)

# Standardize empty and remote locations
df.location = df.location.replace('', 'Remote')
df.location = df.location.replace(['Remote - US', 'Remote, United States'], 'Remote')

print(df.salary_min.describe())
print(df.location.value_counts().head(10))

# Convert tags to comma separated for storage
df['tags'] = df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
df['source'] = 'remoteok'

# Set date to SQL compatible
df['date'] = df['date'].astype(str)

# Create database and save
engine = create_engine('sqlite:///data/jobs.db')
with engine.connect() as conn:
    for _, row in df.iterrows():
        try:
            conn.execute(text("""
                INSERT OR IGNORE INTO jobs
                (title, company, location, salary_min, salary_max, tags, date, url, source)
                VALUES (:title, :company, :location, :salary_min, :salary_max, :tags, :date, :url, :source)
            """), dict(row))
        except Exception as e:
            print(f'Error: {e}')
    conn.commit()

# Verify working
saved = pd.read_sql('SELECT COUNT(*) as total FROM jobs', engine)
print(f'Total jobs in DB: {saved['total'][0]}')