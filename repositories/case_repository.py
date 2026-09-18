from typing import Optional, List, Dict, Any
from database.db import get_db
from models.case import Case

class CaseRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, case_id: int) -> Optional[Case]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, u.username as investigator_username
            FROM "Case" c
            LEFT JOIN User u ON c.investigator_id = u.id
            WHERE c.id = ?;
        """, (case_id,))
        row = cursor.fetchone()
        return Case.from_row(row) if row else None

    def list_all(self, status: Optional[str] = None, incident_type: Optional[str] = None) -> List[Case]:
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT c.*, u.username as investigator_username
            FROM "Case" c
            LEFT JOIN User u ON c.investigator_id = u.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND c.status = ?"
            params.append(status)
        if incident_type:
            query += " AND c.incident_type = ?"
            params.append(incident_type)
        query += " ORDER BY c.created_at DESC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Case.from_row(r) for r in rows]

    def create(self, title: str, incident_type: str, description: Optional[str], investigator_id: int) -> Case:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO "Case" (title, incident_type, description, status, investigator_id)
            VALUES (?, ?, ?, 'OPEN', ?);
        """, (title, incident_type, description, investigator_id))
        conn.commit()
        case_id = cursor.lastrowid
        return self.get_by_id(case_id)

    def update(self, case_id: int, title: str, incident_type: str, description: Optional[str]) -> Optional[Case]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE "Case"
            SET title = ?, incident_type = ?, description = ?
            WHERE id = ?;
        """, (title, incident_type, description, case_id))
        conn.commit()
        return self.get_by_id(case_id)

    def close(self, case_id: int) -> Optional[Case]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE "Case"
            SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (case_id,))
        conn.commit()
        return self.get_by_id(case_id)

    def delete(self, case_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "Case" WHERE id = ?;', (case_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_metrics(self) -> Dict[str, int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM "Case";')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM "Case" WHERE status = "OPEN";')
        open_cases = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM "Case" WHERE status = "CLOSED";')
        closed_cases = cursor.fetchone()[0]
        return {
            "total": total,
            "open": open_cases,
            "closed": closed_cases
        }
