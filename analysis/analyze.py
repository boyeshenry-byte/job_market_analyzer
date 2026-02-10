# import modules
import pandas as pd
from sqlalchemy import create_engine

# get data
engine = create_engine('sqlite:///data/jobs.db')
df = pd.read_sql('SELECT * FROM jobs', engine)

# Find top skills
all_tags = df.tags.dropna().str.split(", ").explode().str.strip().str.lower()
print('Top 15 skills in demand')
print(all_tags.value_counts().head(15))

# Filter for tech/data specific skills
tech_tags = ['python', 'sql', 'javascript', 'react', 'aws', 'docker', 'machine learning',
             'data', 'analytics', 'api', 'cloud', 'devops', 'kubernetes', 'java', 'golang',
             'rust', 'ai', 'nlp', 'tensorflow', 'pytorch']

tech_counts = all_tags[all_tags.isin(tech_tags)].value_counts()
print('\nTechnical Skills in Demand:')
print(tech_counts)

# Check salary data
salary_df = df.dropna(subset=['salary_min'])
print(f'\nJobs with salary data: {len(salary_df)}')
print(f'Salary range: ${salary_df['salary_min'].min():,.0f}) \
      - ${salary_df['salary_max'].max():,.0f}')
print(f'Median min salary: ${salary_df['salary_min'].median():,.0f}')

print('\nTop 5 highest paying roles:')
top = salary_df.nlargest(5, 'salary_min')[['title', 'company', 'salary_min', 'salary_max']]
print(top.to_string(index=False))