import requests
import pandas as pd
import numpy as np
import time
import html
from sqlalchemy import create_engine, text
from config import HN_URL, DB_URL

def fetch_jobs():
    """
    This function scrapes jobs from Hacker Network's who's hiring job board.

    : attributes : 

    role : str
        the position title
    company : str
        the company posting the position
    location : str
        the location of the position
    remote : str
        whether the position is remote or onsite
    """

    url = HN_URL
    time.sleep(1)
    try:
        response = requests.get(url)
        data = response.json()
        thread_title = data.get('title', '')
        # "Ask HN: Who is hiring? (January 2025)" → "January 2025"
        date = thread_title.split('(')[-1].replace(')', '').strip()
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

    comment_ids = data['kids']

    for cid in comment_ids:
        time.sleep(1)
        try:
            comment_url = f"https://hacker-news.firebaseio.com/v0/item/{cid}.json"
            comment = requests.get(comment_url).json()
            text = comment.get('text', '')
        
            first_line = text.split('<p>')[0]
            parts = first_line.split('|')

            if len(parts) >= 3:
                job = {
                    'title': parts[1].strip(),
                    'company': parts[0].strip(),
                    'location': parts[2].strip(),
                    'remote': parts[3].strip() if len(parts) > 3 else '',
                    'date': date,
                    'source': 'hackernews'
                }
            jobs.append(job)
        except:
            continue


    df = pd.DataFrame(jobs)

    return df  

def clean_data(df):
    """
    This function takes a DataFrame from fetch_jobs() and standardizes locations and 
    adds the month and year the job posting is from. It returns a cleaned DataFrame.
    
    :param df: A DataFrame from fetch_jobs()
    """

    df['company'] = df['company'].apply(html.unescape)
    df['title'] = df['title'].apply(html.unescape)
    df['location'] = df['location'].apply(html.unescape)
    
    return df

def save_db(df):
    # Save to the database
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
              conn.execute(text("""
                    INSERT INTO jobs
                    (title, company, location, date, source)
                    VALUES (:title, :company, :location, :date, :source) 
                    ON CONFLICT (title, company, source) DO NOTHING
                """), dict(row))
            except Exception as e:
               print(f"Error: {e}")
        conn.commit()

    # Verify working
    saved = pd.read_sql('SELECT COUNT(*) as total FROM jobs', engine)
    total = saved['total'][0]
    print(f"Total jobs in DB: {total}")

if __name__ == '__main__':
    print('Fetching jobs from Hacker Network...')
    df = fetch_jobs()
    if df.empty:
        print('No jobs fetched. Exiting.')
    else:
        print(f"Found {len(df)} jobs")
        df = clean_data(df)
        save_db(df)
        print('Done!')