
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(
    host=os.environ["PGHOST"],
    port=os.environ["PGPORT"],
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    connect_timeout=5,
) as conn:

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                current_database(),
                current_user,
                version()
        """)

        database, user, version = cur.fetchone()

        print("Database:", database)
        print("User:", user)
        print("PostgreSQL:", version.split(",")[0])

        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('staging', 'gold')
              AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
        """)

        print("\nAvailable DWH tables:")

        for schema, table in cur.fetchall():
            print(f"  {schema}.{table}")

print("\nDatabase connection test passed!")
