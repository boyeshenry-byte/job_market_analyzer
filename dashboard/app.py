import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

import sys
import os
try:
    DB_URL = st.secrets["DATABASE_URL"]
except:
    from config import DB_URL


def create_dashboard():
    """
    This function creates a dashboard for the analysis of scraped job board data.

    : attributes :

    Jobs by Source : bar_chart
        returns a bar chart comparing the sources of job postings
    Top Technical Skills (RemoteOK) : bar_chart
        returns a bar chart of what skills are in most demand according to listings on RemoteOK
    Salary Ranges : df
        returns a DataFrame of positions, companies, salary ranges, and their source
    Job Types (WeWorkRemote) : bar_chart
        returns a bar chart comparing the types of jobs listed on We Work Remote
    Data and Analytics Roles : df
        returns a DataFrame of jobs, companies, and locations from all sources filtered for Data Science and Data Analytics roles

    """
    # create dashboard
    engine = create_engine(DB_URL)
    df = pd.read_sql("select * from jobs", engine)

    st.title('Job Market Analyzer')
    st.metric('Total Jobs Scraped', len(df))

    # split by sources
    st.header('Jobs by Source')
    source_counts = df.source.value_counts()
    st.bar_chart(source_counts)

    # top skills from remoteok
    st.header('Top Technical Skills (RemoteOK)')
    remoteok = df[df['source']=='remoteok']
    all_tags = remoteok.tags.dropna().str.split(', ').explode().str.strip().str.lower()

    tech_tags = ['python', 'sql', 'javascript', 'react', 'aws', 'docker', 'machine learning',
                'data', 'analytics', 'api', 'cloud', 'devops', 'kubernetes', 'java', 'golang',
                'rust', 'ai', 'nlp', 'tensorflow', 'pytorch']

    tech_counts = all_tags[all_tags.isin(tech_tags)].value_counts()
    st.bar_chart(tech_counts)

    # salary distribution
    st.header('Salary Ranges')
    salary_df = df.dropna(subset=['salary_min'])
    if not salary_df.empty:
        st.dataframe(salary_df
                    [['title', 'company', 'salary_min', 'salary_max', 'source']]\
                        .sort_values('salary_min', ascending=False))


    # job breakdown WWR
    st.header('Job Types (We Work Remotely)')
    wwr = df[df['source'] == 'weworkremotely']
    job_types = wwr['job_type'].value_counts()
    st.bar_chart(job_types)

    # Hacker News Jobs
    st.header("Top Companies (Hacker News)")
    hn = df[df['source'] == "hackernews"]
    company_counts = hn['company'].value_counts().head(15)
    st.bar_chart(company_counts)

    st.header('Data & Analytics Roles')
    data_keywords = ['data analyst', 'data science', 'data engineer', 
                     'analytics', 'machine learning', 'business intelligence',
                     'data scientist', 'bi analyst', 'ml engineer']

    data_jobs = df[df['title'].str.lower().str.contains('|'.join(data_keywords), na=False)]
    st.metric('Data/Analytics Roles', len(data_jobs))

    if not data_jobs.empty:
        st.dataframe(data_jobs[['title', 'company', 'location', 'source']].reset_index(drop=True))

if __name__ == '__main__':
    create_dashboard()