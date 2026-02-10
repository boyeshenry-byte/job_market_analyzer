import requests
from bs4 import BeautifulSoup

url = 'https://realpython.github.io/fake-jobs/'
response = requests.get(url)
print(response.status_code)

soup = BeautifulSoup(response.text, 'lxml')

job_cards = soup.find_all('div', class_='card-content')
print(len(job_cards))

first_card = job_cards[0]

title = first_card.find('h2', class_='title').text.strip()
company = first_card.find('h3', class_='company').text.strip()
location = first_card.find('p', class_='location').text.strip()

print(title)
print(company)
print(location)

jobs = []

for card in job_cards:
    title = card.find('h2', class_='title').text.strip()
    company = card.find('h3', class_='company').text.strip()
    location = card.find('p', class_='location').text.strip()

    job = {
        'title': title,
        'company': company,
        'location': location,
    }
    jobs.append(job)

print(len(jobs))
print(jobs[0])
print(jobs[1])

import pandas as pd

df = pd.DataFrame(jobs)
print(df.head(10))