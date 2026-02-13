import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
HEADERS = {"User-Agent": "job-market-analyzer"}
REMOTEOKURL = "https://remoteok.com/api"
WWR_URL = "https://weworkremotely.com/remote-jobs"


