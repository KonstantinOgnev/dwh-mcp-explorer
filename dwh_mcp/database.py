
import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """Create a read-only PostgreSQL connection."""
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=5,
        options="-c default_transaction_read_only=on"
    )


def list_schemas() -> dict[str, list[str]]:
    """List available DWH schemas as structured JSON."""

    query = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name IN ('staging', 'gold')
        ORDER BY schema_name
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            schemas = [row[0] for row in cur.fetchall()]

    return {"schemas": schemas}

def list_tables(schema: str) -> dict:
    """List DWH tables in structured JSON format."""

    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_schema IN ('staging', 'gold')
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema,))
            tables = [row[0] for row in cur.fetchall()]

    return {
        "schema": schema,
        "tables": tables,
        "table_count": len(tables)
    }



def describe_table(
    schema: str,
    table: str
) -> list[dict]:
    """Retrieve column metadata from PostgreSQL."""

    query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND table_schema IN ('staging', 'gold')
        ORDER BY ordinal_position
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            return [
                {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "position": row[3]
                }
                for row in cur.fetchall()
            ]


def get_primary_keys(schema: str, table: str) -> list[dict]:
    """Return primary key columns for a DWH table."""

    query = """
        SELECT
            con.conname AS constraint_name,
            att.attname AS column_name,
            k.position AS key_position
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class cls
            ON cls.oid = con.conrelid
        JOIN pg_catalog.pg_namespace ns
            ON ns.oid = cls.relnamespace
        CROSS JOIN LATERAL unnest(con.conkey)
            WITH ORDINALITY AS k(attnum, position)
        JOIN pg_catalog.pg_attribute att
            ON att.attrelid = cls.oid
           AND att.attnum = k.attnum
        WHERE con.contype = 'p'
          AND ns.nspname = %s
          AND cls.relname = %s
          AND ns.nspname IN ('staging', 'gold')
        ORDER BY k.position
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            return [
                {
                    "constraint_name": row[0],
                    "column_name": row[1],
                    "position": row[2]
                }
                for row in cur.fetchall()
            ]

def get_foreign_keys(schema: str, table: str) -> list[dict]:
    """Return foreign key relationships for a DWH table."""

    query = """
        SELECT
            con.conname AS constraint_name,
            source_att.attname AS source_column,
            target_ns.nspname AS target_schema,
            target_cls.relname AS target_table,
            target_att.attname AS target_column
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class source_cls
            ON source_cls.oid = con.conrelid
        JOIN pg_catalog.pg_namespace source_ns
            ON source_ns.oid = source_cls.relnamespace
        JOIN pg_catalog.pg_class target_cls
            ON target_cls.oid = con.confrelid
        JOIN pg_catalog.pg_namespace target_ns
            ON target_ns.oid = target_cls.relnamespace
        CROSS JOIN LATERAL generate_subscripts(
            con.conkey, 1
        ) AS k(position)
        JOIN pg_catalog.pg_attribute source_att
            ON source_att.attrelid = source_cls.oid
           AND source_att.attnum = con.conkey[k.position]
        JOIN pg_catalog.pg_attribute target_att
            ON target_att.attrelid = target_cls.oid
           AND target_att.attnum = con.confkey[k.position]
        WHERE con.contype = 'f'
          AND source_ns.nspname = %s
          AND source_cls.relname = %s
          AND source_ns.nspname IN ('staging', 'gold')
        ORDER BY con.conname, k.position
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            return [
                {
                    "constraint_name": row[0],
                    "source_column": row[1],
                    "target_schema": row[2],
                    "target_table": row[3],
                    "target_column": row[4]
                }
                for row in cur.fetchall()
            ]