from typing import Optional, List, Dict, Any, Tuple
from database.db import get_db
from models.security_event import SecurityEvent

class EventRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, event_id: int) -> Optional[SecurityEvent]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SecurityEvent WHERE id = ?;", (event_id,))
        row = cursor.fetchone()
        return SecurityEvent.from_row(row) if row else None

    def list_by_case(self, case_id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> List[SecurityEvent]:
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM SecurityEvent WHERE case_id = ? ORDER BY event_timestamp ASC, id ASC"
        params: List[Any] = [case_id]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [SecurityEvent.from_row(r) for r in rows]

    def create(self, case_id: int, event_type: str, event_user: Optional[str],
               source: str, ip_ref: Optional[str], event_timestamp: str,
               raw_line: Optional[str] = None) -> SecurityEvent:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SecurityEvent (case_id, event_type, event_user, source, ip_ref, event_timestamp, raw_line)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (case_id, event_type, event_user, source, ip_ref, event_timestamp, raw_line))
        conn.commit()
        event_id = cursor.lastrowid
        return self.get_by_id(event_id)

    def bulk_insert(self, events: List[Dict[str, Any]]) -> int:
        if not events:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        rows_to_insert = [
            (
                e["case_id"],
                e["event_type"],
                e.get("event_user"),
                e["source"],
                e.get("ip_ref"),
                e["event_timestamp"],
                e.get("raw_line")
            )
            for e in events
        ]
        cursor.executemany("""
            INSERT INTO SecurityEvent (case_id, event_type, event_user, source, ip_ref, event_timestamp, raw_line)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, rows_to_insert)
        conn.commit()
        return cursor.rowcount

    def count_by_case(self, case_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SecurityEvent WHERE case_id = ?;", (case_id,))
        return cursor.fetchone()[0]

    def count_all(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SecurityEvent;")
        return cursor.fetchone()[0]

    def get_event_type_distribution(self, case_id: Optional[int] = None) -> Dict[str, int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if case_id:
            cursor.execute("""
                SELECT event_type, COUNT(*) 
                FROM SecurityEvent 
                WHERE case_id = ? 
                GROUP BY event_type 
                ORDER BY COUNT(*) DESC;
            """, (case_id,))
        else:
            cursor.execute("""
                SELECT event_type, COUNT(*) 
                FROM SecurityEvent 
                GROUP BY event_type 
                ORDER BY COUNT(*) DESC;
            """)
        return {row[0]: row[1] for row in cursor.fetchall()}
