import requests
import pandas as pd
import numpy as np
import time
import html
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from config import DB_URL

def get_scraped_threads():
    """
    This function checks which months we have already scraped so we can ignore them
    """
    engine = create_engine(DB_URL)
    result = pd.read_sql(
        "SELECT DISTINCT date FROM jobs WHERE source = 'hackernews'",
        engine
    )

    return result['date'].tolist()

def get_thread_ids():
    """
    This function fetches HN's who's hiring thread ID's and returns them as a variable to use for scraping.

    : attributes :
    
    thread_ids : str
        the saved url for scraping

    """
    thread_ids = []
    seen = set()
    page = 0
    while True:
        url = f"https://hn.algolia.com/api/v1/search?query=who+is+hiring&tags=ask_hn&hitsPerPage=50&page={page}"
        response = requests.get(url)
        data = response.json()

        if not data['hits']:
            break
    
        for hit in data['hits']:
            if hit['title'].startswith('Ask HN: Who is hiring?'):
                tid = hit['objectID']
                if tid not in seen:
                    seen.add(tid)
                    thread_ids.append(tid)
        
        page += 1
        if page > 5:
            break
    
    return thread_ids

def fetch_jobs(thread_id):
    """
    This function scrapes jobs from Hacker Network's who's hiring job board.

    : params :

    thread_id : str
        the id of the targeted scraping thread

    : attributes : 

    role : str
        the position title
    company : str
        the company posting the position
    location : str
        the location of the position
    salary_range : int
        the pay range associated with the salary
    job_type : str
        the type of job (full time, part time, freelance, contract)
    url : str
        the url associated with the job listing
    """

    url = f"https://hacker-news.firebaseio.com/v0/item/{thread_id}.json"
    time.sleep(0.2)
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

    comment_ids = data.get('kids',[])

    if not comment_ids:
        return pd.DataFrame()

    for cid in comment_ids:
        time.sleep(0.1)
        try:
            comment_url = f"https://hacker-news.firebaseio.com/v0/item/{cid}.json"
            comment = requests.get(comment_url).json()
            text = comment.get('text', '')
        
            first_line = text.split('<p>')[0]
            parts = first_line.split('|')

            if len(parts) >= 3:
                company = parts[0].strip()

                title = ''
                location = ''
                salary_range = ''
                job_type = ''
                url = ''


                for part in parts[1:]:
                    p = part.strip()
                    pl = p.lower()

                    # extract websites
                    if 'href' in pl or 'http' in pl:
                        url = pl
                        continue

                    # check if looks like a location
                    if any(word in pl for word in ['remote', 'onsite', 'hybrid', 'nyc',
                                                   'sf', 'san francisco', 'new york', 'london',
                                                   'us only', 'eu only', 'worldwide', 'sd', 'san diego',
                                                   'berlin']):
                        location = pl
                    elif '$' in p or 'k+' in pl:
                        if '$' in p:
                            salary_range = p
                        else:
                            salary_range = pl
                    elif any(word in pl for word in ['full-time', 'full time', 'part time',
                                                    'part-time', 'freelance', 'contract']):
                        job_type = pl
                    elif not title:
                        title = p
                    else:
                        location = p
                job = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary_range': salary_range,
                    'job_type': job_type,
                    'date': date,
                    'url': url,
                    'source': 'hackernews'
                    }

                jobs.append(job)
        except:
            continue


    df = pd.DataFrame(jobs)

    return df  

def clean_data(df):
    """
    This function takes a DataFrame from fetch_jobs(), removes html tags. It returns a cleaned DataFrame.
    
    :param df: A DataFrame from fetch_jobs()
    """

     # Remove HTML tags
    df['company'] = df['company'].apply(lambda x: re.sub('<[^<]+?>', '', x))
    df['title'] = df['title'].apply(lambda x: re.sub('<[^<]+?>', '', x))
    df['location'] = df['location'].apply(lambda x: re.sub('<[^<]+?>', '', x))
        
    # Unescape HTML entities
    df['company'] = df['company'].apply(html.unescape)
    df['title'] = df['title'].apply(html.unescape)
    df['location'] = df['location'].apply(html.unescape)

    df['salary_range'] = df['salary_range'].apply(lambda x: re.sub('<[^<]+?>', '', x) if x else x)
    df['salary_range'] = df['salary_range'].apply(lambda x: html.unescape(x) if x else x)
    
    return df

def save_db(df):
    # Save to the database
    engine = create_engine(DB_URL, pool_size=1, max_overflow=0)
    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
              conn.execute(text("""
                    INSERT INTO jobs
                    (title, company, location, salary_range, job_type, date, url, source)
                    VALUES (:title, :company, :location, :salary_range, :job_type, :date, :url, :source) 
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
    thread_ids = get_thread_ids()
    scraped_dates = get_scraped_threads()
    print(f"Found {len(thread_ids)} threads. Already used {len(scraped_dates)} months")

    for tid in thread_ids:
        # Check title
        url = f"https://hacker-news.firebaseio.com/v0/item/{tid}.json"
        data = requests.get(url).json()
        title = data.get('title', '')
        date = title.split('(')[-1].replace(')', '').strip()

        current_month = datetime.now().strftime("%B %Y")

        if date in scraped_dates and date != current_month:
            print(f"Skipping {date} - already scraped")
            continue
        
        print(f"Scraping {date}...")
        df = fetch_jobs(tid)
        if df.empty:
            continue
        print(f"Found {len(df)} jobs")
        df = clean_data(df)
        save_db(df)

    print('Done!')