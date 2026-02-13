# import modules
import requests
import pandas as pd
import numpy as np
import time
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from config import WWR_URL, HEADERS, DB_URL

def fetch_jobs():
    """
    This function fetches jobs and returns them in a DataFrame

    This function takes no arguments and returns a DataFrame of job postings

    : attributes :

    title : str
      the title of the position listed
    company : str
        the company the position is with
    location : str
        the location of the position
    categories : str
        relevant information to the job
    
    """

    # Get data
    url = WWR_URL
    headers = HEADERS
    time.sleep(1)
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        print('Error: Cannot connect to the server')
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        print('Error: Request took too long')
        return pd.DataFrame()
    except ValueError:
        print("Response wasn't valid JSON")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, 'lxml')
    job_cards = soup.find_all('li', class_='new-listing-container')

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
    return df

def clean_data(df):
    """
    This function takes a DataFrame from fetch_jobs() and divides the categories into
    job_type (full-time, contract, part-time, freelance), salary_range, and region. 
    It returns a cleaned DataFrame.
    
    :param df: A DataFrame from fetch_jobs()
    """
    
    # Storage variables
    job_type = []
    salary_range = []
    region = []

    for _, row in df.iterrows():
        cats = row['categories']
        jt, sr, rg = None, None, None
        for c in cats:
            if c in ['Full-Time', 'Contract', 'Part-Time', 'Freelance']:
                jt = c
            elif '$' in c or 'USD' in c:
                sr = c
            elif c != 'Featured':
                rg = c
        job_type.append(jt)
        salary_range.append(sr)
        region.append(rg)

    # Rebuild DF
    df['job_type'] = job_type
    df['salary_range'] = salary_range
    df['region'] = region
    df.drop(columns=['categories'], inplace=True)

    # Store data
    df['source'] = 'weworkremotely'

    return df

def save_db(df):
    """
    This function takes a cleaned DataFrame and saves it as an SQL Database
    
    :param df: A cleaned DataFrame
    """

    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(text("""
                    insert into jobs
                    (title, company, location, salary_range, job_type, region, source)
                    values (:title, :company, :location, :salary_range, :job_type, :region, :source)
                    on conflict do nothing
                """), dict(row))
            except Exception as e:
                print(f'Error: {e}')
        conn.commit() 

    saved = pd.read_sql('SELECT COUNT(*) as total FROM jobs', engine)
    print(f'Total jobs in database: {saved['total'][0]}')

if __name__ == '__main__':
    print('Fetching jobs from We Work Remotely')
    df = fetch_jobs()
    if df.empty:
        print('No jobs fetched. Exiting.')
    else:
        print(f'Found {len(df)} jobs')
        df = clean_data(df)
        save_db(df)
        print('Done!')