from typing import Optional, List, Dict, Any
from database.db import get_db
from models.evidence import Evidence

class EvidenceRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Evidence WHERE id = ?;", (evidence_id,))
        row = cursor.fetchone()
        return Evidence.from_row(row) if row else None

    def list_by_case(self, case_id: int) -> List[Evidence]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Evidence WHERE case_id = ? ORDER BY collected_at ASC;", (case_id,))
        rows = cursor.fetchall()
        return [Evidence.from_row(r) for r in rows]

    def list_all(self) -> List[Evidence]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Evidence ORDER BY collected_at DESC;")
        rows = cursor.fetchall()
        return [Evidence.from_row(r) for r in rows]

    def create(self, case_id: int, name: str, type: str, source: str,
               file_path: str, file_size: int, sha256_original: str,
               description: Optional[str] = None) -> Evidence:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Evidence (
                case_id, name, type, source, file_path, file_size,
                sha256_original, sha256_current, integrity_status, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NOT_VERIFIED', ?);
        """, (case_id, name, type, source, file_path, file_size, sha256_original, sha256_original, description))
        conn.commit()
        evidence_id = cursor.lastrowid
        return self.get_by_id(evidence_id)

    def update_hash_and_status(self, evidence_id: int, sha256_current: Optional[str], integrity_status: str) -> Optional[Evidence]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Evidence
            SET sha256_current = ?, integrity_status = ?
            WHERE id = ?;
        """, (sha256_current, integrity_status, evidence_id))
        conn.commit()
        return self.get_by_id(evidence_id)

    def count_all(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Evidence;")
        return cursor.fetchone()[0]

    def count_by_status(self, case_id: Optional[int] = None) -> Dict[str, int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if case_id:
            cursor.execute("""
                SELECT integrity_status, COUNT(*) 
                FROM Evidence 
                WHERE case_id = ? 
                GROUP BY integrity_status;
            """, (case_id,))
        else:
            cursor.execute("""
                SELECT integrity_status, COUNT(*) 
                FROM Evidence 
                GROUP BY integrity_status;
            """)
        results = {"VERIFIED": 0, "MODIFIED": 0, "MISSING": 0, "NOT_VERIFIED": 0}
        for status, count in cursor.fetchall():
            if status in results:
                results[status] = count
        return results
