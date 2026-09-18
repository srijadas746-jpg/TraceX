from typing import Optional, List
from database.db import get_db
from models.custody_record import CustodyRecord

class CustodyRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, record_id: int) -> Optional[CustodyRecord]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cr.*, u.username as actor_username
            FROM CustodyRecord cr
            LEFT JOIN User u ON cr.actor_id = u.id
            WHERE cr.id = ?;
        """, (record_id,))
        row = cursor.fetchone()
        return CustodyRecord.from_row(row) if row else None

    def list_by_evidence(self, evidence_id: int) -> List[CustodyRecord]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cr.*, u.username as actor_username
            FROM CustodyRecord cr
            LEFT JOIN User u ON cr.actor_id = u.id
            WHERE cr.evidence_id = ?
            ORDER BY cr.timestamp ASC, cr.id ASC;
        """, (evidence_id,))
        rows = cursor.fetchall()
        return [CustodyRecord.from_row(r) for r in rows]

    def list_by_case(self, case_id: int) -> List[CustodyRecord]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cr.*, u.username as actor_username
            FROM CustodyRecord cr
            JOIN Evidence e ON cr.evidence_id = e.id
            LEFT JOIN User u ON cr.actor_id = u.id
            WHERE e.case_id = ?
            ORDER BY cr.timestamp ASC, cr.id ASC;
        """, (case_id,))
        rows = cursor.fetchall()
        return [CustodyRecord.from_row(r) for r in rows]

    def create(self, evidence_id: int, action: str, actor_id: int,
               prev_status: Optional[str] = None, new_status: Optional[str] = None,
               remarks: Optional[str] = None) -> CustodyRecord:
        """
        Append-only insert of a custody record. Note: No update or delete methods exist.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO CustodyRecord (evidence_id, action, actor_id, prev_status, new_status, remarks)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (evidence_id, action, actor_id, prev_status, new_status, remarks))
        conn.commit()
        record_id = cursor.lastrowid
        return self.get_by_id(record_id)

    def count_all(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM CustodyRecord;")
        return cursor.fetchone()[0]
