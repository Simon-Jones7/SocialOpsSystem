from contextlib import contextmanager
import os
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    with psycopg.connect(DATABASE_URL) as conn:
        yield conn


def ensure_tables():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    draft_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    decision_note TEXT,
                    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decided_by TEXT
                );
                """
            )
        conn.commit()