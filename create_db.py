from sqlalchemy import create_engine, text
from config import DB_URL

def make_db():
    """
    Creates a database to store data called from job scrapers.

    : attributes :
    
    title : str
        the name of the position
    company : str
        the company the position is with
    location : str
        the location of the job
    salary_min : int
        the minimum salary for the position
    salary_max : int
        the maximum salary for the position
    salary_range : int
        the salary range for the position (if min and max not used)
    tags : str
        the tags related to the job
    job_type: str
        the type of posititon (full-time, part-time, contract, freelance)
    region : str
        the region of the company
    date : str
        the date the job was listed
    url : str
        the url for the job (if provided)
    source : str
        which job board the job is listed on
    
    """
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        conn.execute(text("""
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
            )
        """))
        conn.commit()

if __name__ == '__main__':
    make_db()
    print("Database created successfully")
