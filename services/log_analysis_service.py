import csv
import json
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dateutil import parser as date_parser

from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository
from models.security_event import SecurityEvent

VALID_EVENT_TYPES = {
    "LOGIN_SUCCESS",
    "LOGIN_FAILED",
    "MULTIPLE_LOGIN_FAILURES",
    "FILE_CREATED",
    "FILE_MODIFIED",
    "FILE_DELETED",
    "ACCOUNT_LOCKED",
    "UNUSUAL_ACCESS",
    "PERMISSION_CHANGED"
}

class LogAnalysisService:
    """
    Deterministic, explainable log analysis and rule engine.
    Parses synthetic logs and evaluates rules R1-R3.
    """
    def __init__(self,
                 event_repo: Optional[EventRepository] = None,
                 finding_repo: Optional[FindingRepository] = None):
        self.event_repo = event_repo or EventRepository()
        self.finding_repo = finding_repo or FindingRepository()

    def parse_timestamp(self, ts_str: str) -> Optional[str]:
        if not ts_str:
            return None
        try:
            dt = date_parser.parse(str(ts_str))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    def import_logs_from_stream(self, case_id: int, stream: io.StringIO, file_format: str = "csv") -> Dict[str, Any]:
        """
        Parses CSV or JSONL logs safely, skipping malformed rows while processing valid rows.
        """
        valid_events = []
        errors = []
        line_num = 0

        if file_format.lower() == "csv":
            reader = csv.DictReader(stream)
            for row in reader:
                line_num += 1
                try:
                    ts_raw = row.get("timestamp") or row.get("event_timestamp") or row.get("time")
                    event_type = (row.get("event_type") or "").strip().upper()
                    source = (row.get("source") or "synthetic-log").strip()
                    user = (row.get("user") or row.get("event_user") or "").strip() or None
                    ip_ref = (row.get("ip_ref") or row.get("ip") or "").strip() or None

                    if not ts_raw or not event_type:
                        errors.append({"line": line_num, "reason": "Missing timestamp or event_type"})
                        continue

                    normalized_ts = self.parse_timestamp(ts_raw)
                    if not normalized_ts:
                        errors.append({"line": line_num, "reason": f"Invalid timestamp format: '{ts_raw}'"})
                        continue

                    if event_type not in VALID_EVENT_TYPES:
                        errors.append({"line": line_num, "reason": f"Unknown event_type: '{event_type}'"})
                        continue

                    raw_line = json.dumps(row)
                    valid_events.append({
                        "case_id": case_id,
                        "event_type": event_type,
                        "event_user": user,
                        "source": source,
                        "ip_ref": ip_ref,
                        "event_timestamp": normalized_ts,
                        "raw_line": raw_line
                    })
                except Exception as e:
                    errors.append({"line": line_num, "reason": f"Parsing exception: {str(e)}"})

        elif file_format.lower() in ("jsonl", "json"):
            for line in stream:
                line_num += 1
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    row = json.loads(line_str)
                    ts_raw = row.get("timestamp") or row.get("event_timestamp") or row.get("time")
                    event_type = (row.get("event_type") or "").strip().upper()
                    source = (row.get("source") or "synthetic-log").strip()
                    user = (row.get("user") or row.get("event_user") or "").strip() or None
                    ip_ref = (row.get("ip_ref") or row.get("ip") or "").strip() or None

                    if not ts_raw or not event_type:
                        errors.append({"line": line_num, "reason": "Missing timestamp or event_type"})
                        continue

                    normalized_ts = self.parse_timestamp(ts_raw)
                    if not normalized_ts:
                        errors.append({"line": line_num, "reason": f"Invalid timestamp format: '{ts_raw}'"})
                        continue

                    if event_type not in VALID_EVENT_TYPES:
                        errors.append({"line": line_num, "reason": f"Unknown event_type: '{event_type}'"})
                        continue

                    valid_events.append({
                        "case_id": case_id,
                        "event_type": event_type,
                        "event_user": user,
                        "source": source,
                        "ip_ref": ip_ref,
                        "event_timestamp": normalized_ts,
                        "raw_line": line_str
                    })
                except Exception as e:
                    errors.append({"line": line_num, "reason": f"JSON decode error: {str(e)}"})

        inserted_count = self.event_repo.bulk_insert(valid_events)
        return {
            "total_rows_read": line_num,
            "imported_events": inserted_count,
            "error_count": len(errors),
            "errors": errors
        }

    def _to_dt(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            return ts
        return datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")

    def run_rules(self, case_id: int) -> List[Dict[str, Any]]:
        """
        Executes deterministic rules over all security events for the specified case.
        Clears previous INDICATOR findings to ensure idempotency.
        """
        events = self.event_repo.list_by_case(case_id)
        if not events:
            return []

        self.finding_repo.clear_by_case_and_kind(case_id, kind="INDICATOR")

        findings_to_insert = []

        # Group events by user
        user_events: Dict[str, List[SecurityEvent]] = {}
        for ev in events:
            user_key = ev.event_user or "ANONYMOUS"
            if user_key not in user_events:
                user_events[user_key] = []
            user_events[user_key].append(ev)

        # Rule evaluation per user
        for user, u_events in user_events.items():
            if user == "ANONYMOUS":
                continue

            # R1: >= 5 LOGIN_FAILED within 10 min (600s)
            failed_logins = [e for e in u_events if e.event_type == "LOGIN_FAILED"]
            
            i = 0
            while i < len(failed_logins):
                window_start = self._to_dt(failed_logins[i].event_timestamp)
                window_events = [failed_logins[i]]
                j = i + 1
                while j < len(failed_logins):
                    dt_j = self._to_dt(failed_logins[j].event_timestamp)
                    if (dt_j - window_start).total_seconds() <= 600:
                        window_events.append(failed_logins[j])
                        j += 1
                    else:
                        break

                if len(window_events) >= 5:
                    ev_ids = [e.id for e in window_events]
                    findings_to_insert.append({
                        "case_id": case_id,
                        "kind": "INDICATOR",
                        "rule_or_key": "R1",
                        "severity": "MEDIUM",
                        "related_event_ids": ev_ids,
                        "related_evidence_ids": [],
                        "description": (f"Potentially suspicious authentication activity: {len(window_events)} "
                                        f"consecutive failed logins detected for user '{user}' within 10 minutes.")
                    })
                    i = j
                else:
                    i += 1

            # R2: ACCOUNT_LOCKED following repeated failures / R1 within 15 min (900s)
            lock_events = [e for e in u_events if e.event_type == "ACCOUNT_LOCKED"]
            for lock in lock_events:
                lock_dt = self._to_dt(lock.event_timestamp)
                preceding_failures = [
                    e for e in failed_logins
                    if 0 <= (lock_dt - self._to_dt(e.event_timestamp)).total_seconds() <= 900
                ]
                if preceding_failures:
                    rel_ids = [e.id for e in preceding_failures] + [lock.id]
                    findings_to_insert.append({
                        "case_id": case_id,
                        "kind": "INDICATOR",
                        "rule_or_key": "R2",
                        "severity": "HIGH",
                        "related_event_ids": rel_ids,
                        "related_evidence_ids": [],
                        "description": (f"Security indicator: account lock after repeated failures for user '{user}'. "
                                        f"{len(preceding_failures)} failed attempts preceded lockout.")
                    })

            # R3: UNUSUAL_ACCESS then PERMISSION_CHANGED for same user within 15 min (900s)
            access_events = [e for e in u_events if e.event_type == "UNUSUAL_ACCESS"]
            perm_events = [e for e in u_events if e.event_type == "PERMISSION_CHANGED"]

            for acc in access_events:
                acc_dt = self._to_dt(acc.event_timestamp)
                for perm in perm_events:
                    perm_dt = self._to_dt(perm.event_timestamp)
                    delta_sec = (perm_dt - acc_dt).total_seconds()
                    if 0 <= delta_sec <= 900:
                        findings_to_insert.append({
                            "case_id": case_id,
                            "kind": "INDICATOR",
                            "rule_or_key": "R3",
                            "severity": "HIGH",
                            "related_event_ids": [acc.id, perm.id],
                            "related_evidence_ids": [],
                            "description": (f"Rule matched: suspicious access-then-privilege-change sequence "
                                            f"for user '{user}' within {int(delta_sec)} seconds.")
                        })

        if findings_to_insert:
            self.finding_repo.bulk_insert(findings_to_insert)

        return findings_to_insert
