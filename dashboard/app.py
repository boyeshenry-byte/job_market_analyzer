import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# create dashboard
engine = create_engine('sqlite:///data/jobs.db')
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