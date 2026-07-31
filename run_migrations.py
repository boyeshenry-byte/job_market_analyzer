import os
from datetime import datetime
from sqlalchemy import create_engine, text
from config import DB_URL

MIGRATIONS_DIR = "migrations"

def get_applied_migrations(conn):
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
        filename TEXT,
        applied_at TIMESTAMPTZ,
        unique(filename))
        """
    ))
    conn.commit()

    res = conn.execute(text("""
    SELECT filename 
    FROM schema_migrations
    """
    ))

    return {i[0] for i in res}
    

def get_migration_files():
    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])

    return files

def apply_migration(conn, filename):
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    with open(filepath, 'r') as f:
        sql = f.read()

    conn.execute(text(sql))

    conn.execute(text("""
        insert into schema_migrations(filename, applied_at) values (:filename ,NOW())
    """), {'filename': filename})

    conn.commit()
    return

def run_migrations():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        applied = get_applied_migrations(conn)
        for filename in get_migration_files():
            if filename in applied:
                print(f"Skipping {filename} — already applied")
                continue
            print(f"Applying {filename}...")
            apply_migration(conn, filename)
    print("Done.")

if __name__ == "__main__":
    run_migrations()