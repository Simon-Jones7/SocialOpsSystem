from typing import Optional, Dict

from app.core.db import get_conn


def set_approval(draft_id: str, status: str, note: Optional[str] = None, decided_by: str = "local"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approvals (draft_id, status, decision_note, decided_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (draft_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    decision_note = EXCLUDED.decision_note,
                    decided_by = EXCLUDED.decided_by,
                    decided_at = CURRENT_TIMESTAMP;
                """,
                (draft_id, status, note, decided_by),
            )
        conn.commit()


def get_approval(draft_id: str) -> Optional[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM approvals WHERE draft_id = %s;", (draft_id,))
            row = cur.fetchone()
            return row[0] if row else None


def get_all_approvals() -> Dict[str, str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT draft_id, status FROM approvals;")
            rows = cur.fetchall()
            return {r[0]: r[1] for r in rows}