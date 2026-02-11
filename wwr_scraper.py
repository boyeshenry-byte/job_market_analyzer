# import modules
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

# Get data
url = 'https://weworkremotely.com/remote-jobs'
headers = {'User-Agent': 'job_market_analyzer'}
response = requests.get(url, headers=headers)

print(response.status_code)

soup = BeautifulSoup(response.text, 'lxml')
job_cards = soup.find_all('li', class_='new-listing-container')

print(f'Found {len(job_cards)} job cards')

jobs = []

for card in job_cards:
    title = card.find('h3', class_='new-listing__header__title')
    company = card.find('p', class_='new-listing__company-name')
    location = card.find('p', class_='new-listing__company-headquarters')
    categories = card.find_all('p', class_='new-listing__categories__category')

    job = {
        'title': title.text.strip() if title else None,
        'company': company.text.strip() if company else None,
        'location': location.text.strip() if location else None,
        'categories': [c.text.strip() for c in categories] if categories else []
    }
    jobs.append(job)

df = pd.DataFrame(jobs)

print(df.shape)
print(df.head())

# Get categories data
for job in jobs:
    cats = job['categories']
    job['job_type'] = None
    job['salary_range'] = None
    job['region'] = None

    for c in cats:
        if c in ['Full-Time', 'Contract', 'Part-Time', 'Freelance']:
            job['job_type'] = c
        elif '$' in c or 'USD' in c:
            job['salary_range'] = c
        elif c != 'Featured':
            job['region'] = c

# Rebuild DF
df = pd.DataFrame(jobs)
df.drop(columns=['categories'], inplace=True)

print(df.head(10))
print(f'\nNumber of jobs with salary data: {df.salary_range.notna().sum()}')

# Store data
df['source'] = 'weworkremotely'

engine = create_engine('sqlite:///data/jobs.db')
with engine.connect() as conn:
    for _, row in df.iterrows():
        try:
            conn.execute(text("""
                insert or ignore into jobs
                (title, company, location, salary_range, job_type, region, source)
                values (:title, :company, :location, :salary_range, :job_type, :region, :source)
            """), dict(row))
        except Exception as e:
            print(f'Error: {e}')
    conn.commit() 

saved = pd.read_sql('SELECT COUNT(*) as total FROM jobs', engine)
print(f'Total jobs in database: {saved['total'][0]}')

