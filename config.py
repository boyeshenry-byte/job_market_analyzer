import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if DB_URL is None:
    try:
        import streamlit as st
        DB_URL = st.secrects["DATABASE_URL"]
    except:
        pass

HEADERS = {"User-Agent": "job-market-analyzer"}
REMOTEOKURL = "https://remoteok.com/api"
WWR_URL = "https://weworkremotely.com/remote-jobs"
HN_URL = "https://hacker-news.firebaseio.com/v0/item/42575537.json"

