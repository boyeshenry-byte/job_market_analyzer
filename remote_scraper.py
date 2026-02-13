# Import modules
import requests
import pandas as pd
import numpy as np
import time
from sqlalchemy import create_engine, text
from config import REMOTEOKURL, HEADERS, DB_URL



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
    salary_min : int
        the minimum salary posted for the position
    salary_max : int
        the maximum salary posted for the position
    tags : str
       the tags associated with the position
    data : datetime
       the date the listing was created
    url : str
        the url for the job posting
    """
    # Get data
    url = REMOTEOKURL
    headers = HEADERS
    time.sleep(1)
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except requests.exceptions.ConnectionError:
        print('Error: Cannot connect to the server')
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        print('Error: Request took too long')
        return pd.DataFrame()
    except ValueError:
        print("Response wasn't valid JSON")
        return pd.DataFrame()

    

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

    return df

def clean_data(df):
    """
    This function takes a DataFrame from fetch_jobs() and replaces 0 salaries
    with NaN, converts and standardizes dates, standardizes locations, converts tags,
    and adds the data source. It returns a cleaned DataFrame.
    
    :param df: A DataFrame from fetch_jobs()
    """

    # Replace 0's with NaN
    df.salary_min = df.salary_min.replace(0, np.nan)
    df.salary_max = df.salary_max.replace(0, np.nan)

    # Convert date to datetime
    df.date = pd.to_datetime(df.date)

    # Standardize empty and remote locations
    df.location = df.location.replace('', 'Remote')
    df.location = df.location.replace(['Remote - US', 'Remote, United States'], 'Remote')

    # Convert tags to comma separated for storage
    df['tags'] = df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    df['source'] = 'remoteok'

    # Set date to SQL compatible
    df['date'] = df['date'].astype(str)

    return df

def save_db(df):
    """
    This function takes a cleaned DataFrame and saves it as an SQL Database
    
    :param df: A cleaned DataFrame
    """
    # Create database and save
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
              conn.execute(text("""
                    INSERT INTO jobs
                   (title, company, location, salary_min, salary_max, tags, date, url, source)
                   VALUES (:title, :company, :location, :salary_min, :salary_max, :tags, :date, :url, :source) 
                    ON CONFLICT DO NOTHING
               """), dict(row))
            except Exception as e:
               print(f'Error: {e}')
        conn.commit()

    # Verify working
    saved = pd.read_sql('SELECT COUNT(*) as total FROM jobs', engine)
    print(f'Total jobs in DB: {saved['total'][0]}')

if __name__ == '__main__':
    print('Fetching jobs from RemoteOK...')
    df = fetch_jobs()
    if df.empty:
        print('No jobs fetched. Exiting.')
    else:
        print(f'Found {len(df)} jobs')
        df = clean_data(df)
        save_db(df)
        print('Done!')
