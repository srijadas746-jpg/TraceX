import json
from typing import Optional, List, Dict, Any
from database.db import get_db
from models.finding import Finding

class FindingRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, finding_id: int) -> Optional[Finding]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Finding WHERE id = ?;", (finding_id,))
        row = cursor.fetchone()
        return Finding.from_row(row) if row else None

    def list_by_case(self, case_id: int, kind: Optional[str] = None) -> List[Finding]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if kind:
            cursor.execute(
                "SELECT * FROM Finding WHERE case_id = ? AND kind = ? ORDER BY id ASC;",
                (case_id, kind)
            )
        else:
            cursor.execute(
                "SELECT * FROM Finding WHERE case_id = ? ORDER BY id ASC;",
                (case_id,)
            )
        rows = cursor.fetchall()
        return [Finding.from_row(r) for r in rows]

    def create(self, case_id: int, kind: str, rule_or_key: str, severity: str,
               related_event_ids: Optional[List[int]],
               related_evidence_ids: Optional[List[int]],
               description: str,
               created_at: Optional[str] = None) -> Finding:
        conn = self._get_connection()
        cursor = conn.cursor()
        event_json = json.dumps(related_event_ids or [])
        evidence_json = json.dumps(related_evidence_ids or [])
        if created_at:
            cursor.execute("""
                INSERT INTO Finding (case_id, kind, rule_or_key, severity, related_event_ids, related_evidence_ids, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (case_id, kind, rule_or_key, severity, event_json, evidence_json, description, created_at))
        else:
            cursor.execute("""
                INSERT INTO Finding (case_id, kind, rule_or_key, severity, related_event_ids, related_evidence_ids, description)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (case_id, kind, rule_or_key, severity, event_json, evidence_json, description))
        conn.commit()
        finding_id = cursor.lastrowid
        return self.get_by_id(finding_id)

    def bulk_insert(self, findings: List[Dict[str, Any]]) -> int:
        if not findings:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        rows = [
            (
                f["case_id"],
                f["kind"],
                f["rule_or_key"],
                f["severity"],
                json.dumps(f.get("related_event_ids", [])),
                json.dumps(f.get("related_evidence_ids", [])),
                f["description"]
            )
            for f in findings
        ]
        cursor.executemany("""
            INSERT INTO Finding (case_id, kind, rule_or_key, severity, related_event_ids, related_evidence_ids, description)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, rows)
        conn.commit()
        return cursor.rowcount

    def clear_by_case_and_kind(self, case_id: int, kind: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Finding WHERE case_id = ? AND kind = ?;", (case_id, kind))
        conn.commit()
        return cursor.rowcount

    def count_by_case(self, case_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Finding WHERE case_id = ?;", (case_id,))
        return cursor.fetchone()[0]

    def count_all(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Finding;")
        return cursor.fetchone()[0]

    def get_severity_distribution(self, case_id: Optional[int] = None) -> Dict[str, int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if case_id:
            cursor.execute("""
                SELECT severity, COUNT(*)
                FROM Finding
                WHERE case_id = ?
                GROUP BY severity;
            """, (case_id,))
        else:
            cursor.execute("""
                SELECT severity, COUNT(*)
                FROM Finding
                GROUP BY severity;
            """)
        severities = {"INFO": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for sev, count in cursor.fetchall():
            if sev in severities:
                severities[sev] = count
        return severities
