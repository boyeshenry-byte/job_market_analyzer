CREATE TABLE IF NOT EXISTS jobs (
    title TEXT,
    company TEXT,
    location TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_range TEXT,
    tags TEXT,
    job_type TEXT,
    region TEXT,
    date TEXT,
    url TEXT,
    source TEXT,
    unique(title, company, source)
);