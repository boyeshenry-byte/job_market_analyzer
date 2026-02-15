import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

st.write("Checking secrets...")
st.write(list(st.secrets.keys()))

HEADERS = {"User-Agent": "job-market-analyzer"}
REMOTEOKURL = "https://remoteok.com/api"
WWR_URL = "https://weworkremotely.com/remote-jobs"
HN_URL = "https://hacker-news.firebaseio.com/v0/item/42575537.json"

